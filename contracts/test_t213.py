"""F2-T1.3 (SPEC-2-001) — rotina operacional de carga mensal, CA-2-02.

Provas (banco local, DSN por env PANUTRIR_DSN; fixture sintética da T2.1c):
  GREEN  o fluxo operacional carrega o mês com registro completo em
         carga_registro (arquivo, hash, contagens, totais, rejeições) — sem SQL
         do operador, com confirmação por ENTER (injetada no teste);
  REGRESSÃO recarregar o MESMO mês não duplica nem altera os outros (o mês é
         apagado e reinsere; os demais ficam intactos);
  IDEMPOTÊNCIA rodar duas vezes termina no mesmo estado (mesmas linhas, mesmos
         totais);
  CANCELAMENTO o operador pode cancelar no passo de confirmação — nada é gravado;
  SIMULAÇÃO --simular mostra o resumo e não grava nada.
"""
import os
import psycopg
import pytest
from pathlib import Path

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "t21c" / "vendas_valido_troca_em_linha_separada.csv"
MES_FIXTURE = "2026-07"


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(DSN, autocommit=True)
    yield c
    # limpeza: remover o mês da fixture (se gravado) e o registro da carga de teste
    with c.cursor() as cur:
        cur.execute("delete from venda_mensal where mes = date '2026-07-01'")
        cur.execute("delete from carga_registro where arquivo_nome = %s", (FIXTURE.name,))
    c.close()


def _contagem(cur, mes="2026-07"):
    cur.execute("select count(*), coalesce(sum(vlritens),0) from venda_mensal where mes = %s::date", (f"{mes}-01",))
    return cur.fetchone()


def test_green_carga_operacional_com_registro_completo(conn):
    from carga_operacional import executar
    cur = conn.cursor()
    antes = _contagem(cur)
    r = executar(FIXTURE, "Ângelo (teste automático)", DSN, confirmar=True,
                 entrada=lambda prompt: "")   # ENTER = confirma
    assert r["status"] == "concluida"
    assert r["conferencia"] and all(c["ok"] for c in r["conferencia"])
    # registro completo
    cur.execute("""select arquivo_nome, arquivo_hash, linhas_lidas, linhas_agregadas,
                          linhas_rejeitadas, totais_por_mes, executado_por, status
                     from carga_registro where carga_id=%s""", (r["carga_id"],))
    nome, hash_, lidas, agreg, rej, totais, operador, status = cur.fetchone()
    assert nome == FIXTURE.name and hash_ and lidas > 0 and agreg > 0
    assert operador.startswith("Ângelo") and status == "concluida"
    assert totais.get(MES_FIXTURE) is not None
    # o mês da fixture está gravado
    depois = _contagem(cur)
    assert depois[0] > antes[0]


def test_regressao_recarregar_nao_duplica_nem_altera_outros(conn):
    from carga_operacional import executar
    from carga_vendas import agregar
    cur = conn.cursor()
    # um mês "outro" (2026-12, não presente na fixture) gravado diretamente
    # para provar que a recarga não o toca
    cur.execute("""insert into venda_mensal (mes, cod_cliente, cod_sku, vlritens, vlrdesc, vlrtroca, qtdade)
                   values (date '2026-12-01', '999', '1', 500, 0, 0, 5)""")
    n_antes_outro = _contagem(cur, "2026-12")
    # recarregar o MESMO mês da fixture
    dados = agregar(FIXTURE)
    r1 = carregar_direto(FIXTURE, dados)
    r2 = carregar_direto(FIXTURE, dados)
    assert r1["inseridas"] == r2["inseridas"]
    # o mês da fixture tem a mesma contagem nas duas cargas
    n_fixture = _contagem(cur, MES_FIXTURE)
    from decimal import Decimal
    assert n_fixture == (dados["totais_por_mes"][MES_FIXTURE]["linhas"],
                         Decimal(str(dados["totais_por_mes"][MES_FIXTURE]["vlritens"])))
    # o mês outro está INTACTO
    assert _contagem(cur, "2026-12") == n_antes_outro
    cur.execute("delete from venda_mensal where mes = date '2026-12-01'")


def carregar_direto(caminho, dados):
    from carga_vendas import carregar
    return carregar(caminho, dados, "teste-t213", DSN)


def test_idempotencia_rodar_duas_vezes_termina_igual(conn):
    from carga_vendas import agregar, carregar
    cur = conn.cursor()
    dados = agregar(FIXTURE)
    carregar(FIXTURE, dados, "teste-t213", DSN)
    n1, t1 = _contagem(cur, MES_FIXTURE)
    carregar(FIXTURE, dados, "teste-t213", DSN)
    n2, t2 = _contagem(cur, MES_FIXTURE)
    assert (n1, t1) == (n2, t2)


def test_cancelamento_pelo_operador_nada_gravado(conn):
    from carga_operacional import executar
    cur = conn.cursor()
    cur.execute("delete from venda_mensal where mes = date '2026-07-01'")
    antes = _contagem(cur)
    r = executar(FIXTURE, "Ângelo (teste automático)", DSN, confirmar=True,
                 entrada=lambda prompt: "n")   # qualquer coisa ≠ ENTER cancela
    assert r["status"] == "cancelado"
    assert _contagem(cur) == antes


def test_simulacao_nada_gravado(conn):
    from carga_operacional import executar
    cur = conn.cursor()
    cur.execute("delete from venda_mensal where mes = date '2026-07-01'")
    antes = _contagem(cur)
    r = executar(FIXTURE, "Ângelo (teste automático)", DSN, simular=True)
    assert r["status"] == "simulado"
    assert _contagem(cur) == antes


def test_arquivo_inexistente_mensagem_clara(conn):
    from carga_operacional import executar
    with pytest.raises(FileNotFoundError):
        executar(Path("/tmp/nao-existe-xyz.csv"), "x", DSN)
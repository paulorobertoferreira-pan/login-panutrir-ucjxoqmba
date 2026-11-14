"""F2-T1.2 (SPEC-2-001) — herança de parâmetros com requer_confirmação, CA-2-05.

Provas (banco local, DSN por env PANUTRIR_DSN):
  · criar_ciclo_com_herdanca('2026-11') cria o ciclo com versão herdada do
    ciclo anterior, e P-02 (Meta Diretoria), P-05 (IS), P-06 (dias úteis) e
    P-07 (G) nascem com pendente_de = 'REQUER_CONFIRMACAO';
  · os valores herdados são os da versão oficial anterior (hipótese, não decisão);
  · pendencias_confirmacao(execucao) lista os 4 parâmetros requeridos não
    confirmados usados pela execução — a lista que força NAO_RECONCILIADA;
  · confirmar um parâmetro (limpar pendente_de) o tira da lista.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
CICLO = "2026-11"
CODIGO = "HERDADA-2026-11"


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    # limpar resíduos de execução anterior do mesmo teste
    cur.execute("delete from execucao_calculo where ciclo_id in (select ciclo_id from ciclo_meta where mes_referencia=%s)", (CICLO,))
    cur.execute("delete from ciclo_meta where mes_referencia=%s", (CICLO,))
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id in (select versao_id from parametros_versao where versao_codigo=%s)", (CODIGO,))
    cur.execute("delete from parametros_versao where versao_codigo=%s", (CODIGO,))
    cur.execute("select id from auth.users where email='paulo.ferreira@panutrir.com.br'")
    u = cur.fetchone()
    autor = str(u[0]) if u else str(__import__("uuid").uuid4())
    cur.execute("select set_config('request.jwt.claim.sub', %s, false)", (autor,))
    cur.execute("select criar_ciclo_com_herdanca(%s, %s, %s)",
                (CICLO, "paulo.ferreira@panutrir.com.br", "Prova CA-2-05: herança de parâmetros"))
    ciclo = cur.fetchone()[0]
    cur.execute("select parametros_versao_id from ciclo_meta where ciclo_id=%s", (ciclo,))
    versao = cur.fetchone()[0]
    cur.execute("""insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, autor, status, finalizado_em, hash_resultado)
                   values (%s, %s, 'teste-t212', 'teste@panutrir.com.br', 'concluida', now(), 'hash')
                   returning execucao_id""", (ciclo, versao))
    execucao = cur.fetchone()[0]
    yield conn, ciclo, versao, execucao
    # limpeza
    cur.execute("delete from execucao_calculo where execucao_id=%s", (execucao,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id=%s", (versao,))
    cur.execute("delete from parametros_versao where versao_id=%s", (versao,))
    conn.close()


def test_ciclo_nasce_com_versao_herdada(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("select versao_codigo, mes_referencia, status from parametros_versao where versao_id=%s", (versao,))
    codigo, mes, status = cur.fetchone()
    assert codigo == CODIGO
    assert mes == CICLO
    assert status == "rascunho"


def test_os_4_campos_de_negocio_nascem_requerendo_confirmacao(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("""select parametro_codigo, pendente_de from parametros_valor
                    where versao_id=%s and parametro_codigo in ('P-02','P-05','P-06','P-07')
                    order by parametro_codigo""", (versao,))
    d = dict(cur.fetchall())
    assert d == {"P-02": "REQUER_CONFIRMACAO", "P-05": "REQUER_CONFIRMACAO",
                 "P-06": "REQUER_CONFIRMACAO", "P-07": "REQUER_CONFIRMACAO"}


def test_valores_herdados_sao_os_do_ciclo_anterior(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("select versao_anterior from parametros_versao where versao_id=%s", (versao,))
    origem = cur.fetchone()[0]
    cur.execute("""select a.parametro_codigo, a.valor_numero = b.valor_numero
                     from parametros_valor a join parametros_valor b using (parametro_codigo)
                    where a.versao_id=%s and b.versao_id=%s
                      and a.parametro_codigo in ('P-02','P-05','P-06','P-07')""", (versao, origem))
    iguais = cur.fetchall()
    assert len(iguais) == 4 and all(i[1] for i in iguais)


def test_pendencias_confirmacao_lista_os_4(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("select parametro_codigo from pendencias_confirmacao(%s) order by parametro_codigo", (execucao,))
    assert [r[0] for r in cur.fetchall()] == ["P-02", "P-05", "P-06", "P-07"]


def test_confirmar_parametro_tira_da_lista(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    # a operação confirma o P-06 (dias úteis) no ciclo novo
    cur.execute("update parametros_valor set pendente_de=null where versao_id=%s and parametro_codigo='P-06'", (versao,))
    cur.execute("select parametro_codigo from pendencias_confirmacao(%s) order by parametro_codigo", (execucao,))
    assert [r[0] for r in cur.fetchall()] == ["P-02", "P-05", "P-07"]
    cur.execute("update parametros_valor set pendente_de='REQUER_CONFIRMACAO' where versao_id=%s and parametro_codigo='P-06'", (versao,))


def test_execucao_sem_pendencia_quando_todos_confirmados(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("update parametros_valor set pendente_de=null where versao_id=%s and parametro_codigo in ('P-02','P-05','P-06','P-07')", (versao,))
    cur.execute("select count(*) from pendencias_confirmacao(%s)", (execucao,))
    assert cur.fetchone()[0] == 0
    # restaurar o estado requerido
    cur.execute("update parametros_valor set pendente_de='REQUER_CONFIRMACAO' where versao_id=%s and parametro_codigo in ('P-02','P-05','P-06','P-07')", (versao,))
    cur.execute("select count(*) from pendencias_confirmacao(%s)", (execucao,))
    assert cur.fetchone()[0] == 4


def test_ciclo_repetido_recusado(ctx):
    conn, ciclo, versao, execucao = ctx
    cur = conn.cursor()
    cur.execute("select id from auth.users where email='paulo.ferreira@panutrir.com.br'")
    u = cur.fetchone()
    autor = str(u[0]) if u else str(__import__("uuid").uuid4())
    cur.execute("select set_config('request.jwt.claim.sub', %s, false)", (autor,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        cur.execute("select criar_ciclo_com_herdanca(%s, %s, %s)",
                    (CICLO, "paulo.ferreira@panutrir.com.br", "prova de ciclo repetido"))
    conn.rollback()
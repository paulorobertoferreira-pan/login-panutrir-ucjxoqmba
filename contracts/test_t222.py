"""F2-T2.2 (SPEC-2-002) — diff campo a campo entre versões, CA-2-09.

Provas (banco local; fixture sintética):
  GREEN  diff campo a campo entre duas versões lista só os parâmetros alterados
         (código, valor anterior, valor novo);
  GREEN  os iguais ficam fora do diff;
  REGRESSÃO a execução aponta a versão que a gerou (parametros_versao_id) e a
         versão carrega autor e motivo.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    vid = cur.fetchone()[0]
    codigos = [f'TESTE-T222-{os.getpid()}-a', f'TESTE-T222-{os.getpid()}-b']
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (vid, codigos[0], 'teste-t222@panutrir.com.br', 'CA-2-09: v1 com alterações',
                 '{"P-02": 13500000, "P-05": 1.05}'))
    v1 = cur.fetchone()[0]
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (v1, codigos[1], 'teste-t222@panutrir.com.br', 'CA-2-09: v2 muda P-02 e P-06',
                 '{"P-02": 14000000, "P-06": 21}'))
    v2 = cur.fetchone()[0]
    yield conn, v1, v2, codigos
    cur.execute("delete from execucao_calculo where parametros_versao_id in (%s,%s) and not exists (select 1 from ciclo_evento ev where ev.execucao_id = execucao_calculo.execucao_id)", (v1, v2))
    cur.execute("delete from ciclo_meta where parametros_versao_id in (%s,%s) and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = ciclo_meta.ciclo_id)", (v1, v2))
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id in (%s,%s)", (v1, v2))
    cur.execute("delete from parametros_versao where versao_id in (%s,%s)", (v2, v1))
    conn.close()


def test_diff_lista_so_os_alterados(ctx):
    conn, v1, v2, codigos = ctx
    cur = conn.cursor()
    cur.execute("""select a.parametro_codigo, b.valor_numero as anterior, a.valor_numero as novo
                     from parametros_valor a
                     join parametros_valor b using (parametro_codigo)
                    where a.versao_id=%s and b.versao_id=%s
                      and coalesce(a.valor_numero::text, a.valor_texto, '')
                   <> coalesce(b.valor_numero::text, b.valor_texto, '')
                    order by a.parametro_codigo""", (v2, v1))
    difs = cur.fetchall()
    assert difs == [('P-02', 13500000, 14000000), ('P-06', 22, 21)]


def test_diff_nao_mostra_iguais(ctx):
    conn, v1, v2, codigos = ctx
    cur = conn.cursor()
    cur.execute("""select count(*) from parametros_valor a join parametros_valor b using (parametro_codigo)
                    where a.versao_id=%s and b.versao_id=%s
                      and coalesce(a.valor_numero::text, a.valor_texto, '')
                  = coalesce(b.valor_numero::text, b.valor_texto, '')""", (v2, v1))
    iguais = cur.fetchone()[0]
    assert iguais > 10   # P-01..P-16 clonados: a maioria não muda


def test_execucao_aponta_a_versao_que_a_gerou(ctx):
    conn, v1, v2, codigos = ctx
    cur = conn.cursor()
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
    mes_teste = None
    for a in (2094, 2093, 2092, 2091, 2090, 2089, 2088):
        for m in range(1, 13):
            cand = f"{a}-{m:02d}"
            cur.execute("select 1 from ciclo_meta where mes_referencia=%s", (cand,))
            if cur.fetchone() is None:
                mes_teste = cand
                break
        if mes_teste:
            break
    assert mes_teste, "sem mês sintético livre"
    cur.execute("""insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)
                   values (%s, 'rascunho', 13000000, %s, gen_random_uuid())
                   returning ciclo_id""", (mes_teste, v2))
    ciclo = cur.fetchone()[0]
    cur.execute("""insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, autor, status, finalizado_em, hash_resultado)
                   values (%s, %s, 'teste-t222', 't@t', 'concluida', now(), 'h') returning execucao_id""", (ciclo, v2))
    execucao = cur.fetchone()[0]
    cur.execute("select parametros_versao_id from execucao_calculo where execucao_id=%s", (execucao,))
    assert cur.fetchone()[0] == v2
    # e a versão aponta o autor/motivo
    cur.execute("select autor, motivo from parametros_versao where versao_id=%s", (v2,))
    autor, motivo = cur.fetchone()
    assert 't222' in autor and 'CA-2-09' in motivo
    cur.execute("delete from execucao_calculo where execucao_id=%s", (execucao,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
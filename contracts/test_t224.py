"""F2-T2.4 (SPEC-2-002) — bloqueios auditados, CA-2-08 e CA-2-10.

Provas (banco local; fixture sintética):
  CA-2-08  criar versão de parâmetros em ciclo APROVADO ou PUBLICADO é recusado
           e a recusa fica auditada (authorization_audit_log, transação autônoma);
  CA-2-10  oficializar versão com parâmetro PENDENTE é recusado e auditado, e a
           versão oficial anterior segue vigente;
  GREEN    oficializar versão SEM pendência funciona (a anterior vira substituída
           e segue consultável).
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")


def _mes_livre(cur):
    for a in (2094, 2093, 2092, 2091, 2090, 2089, 2088, 2087, 2086, 2085,
              2084, 2083, 2082, 2081, 2080):
        for m in range(1, 13):
            cand = f"{a}-{m:02d}"
            cur.execute("select 1 from ciclo_meta where mes_referencia=%s", (cand,))
            if cur.fetchone() is None:
                return cand
    raise RuntimeError("sem mês livre")


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    versao_oficial = cur.fetchone()[0]
    mes = _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id", (mes, versao_oficial))
    ciclo = cur.fetchone()[0]
    yield conn, ciclo, versao_oficial, mes
    # limpeza (mês sintético sem evento: despublicar e apagar)
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    # versões de teste (rascunho pode ser apagado; substituída não — deixar)
    # apagar versões de teste SEM filhos (a FK versao_anterior impede apagar
    # uma versão que outra referencia); repetir até não sobrar nenhuma
    for _ in range(5):
        cur.execute("delete from parametros_valor where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-T224-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from sortimento_restrito where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-T224-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from substituicao where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-T224-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from parametros_versao where versao_codigo like 'TESTE-T224-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id)")
        cur.execute("select count(*) from parametros_versao where versao_codigo like 'TESTE-T224-%' and status='rascunho'")
        if cur.fetchone()[0] == 0:
            break
    conn.close()


def test_ca208_ciclo_aprovado_recusa_versao_nova_e_audita(ctx):
    conn, ciclo, versao_oficial, mes = ctx
    cur = conn.cursor()
    cur.execute("update ciclo_meta set status='aprovado' where ciclo_id=%s", (ciclo,))
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_versao_parametros_ciclo(%s, %s, %s, %s, %s, %s)",
                    (ciclo, versao_oficial, f'TESTE-T224-{os.getpid()}-a', 't@t', 'prova', '{}'))
    conn.rollback()
    cur.execute("select count(*) from authorization_audit_log where position(%s in reason) > 0 and target_id = %s",
                ('CA-2-08', f'TESTE-T224-{os.getpid()}-a'))
    assert cur.fetchone()[0] >= 1, "a recusa fica auditada"
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))


def test_ca208_ciclo_publicado_recusa_versao_nova_e_audita(ctx):
    conn, ciclo, versao_oficial, mes = ctx
    cur = conn.cursor()
    cur.execute("update ciclo_meta set status='publicado' where ciclo_id=%s", (ciclo,))
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_versao_parametros_ciclo(%s, %s, %s, %s, %s, %s)",
                    (ciclo, versao_oficial, f'TESTE-T224-{os.getpid()}-b', 't@t', 'prova', '{}'))
    conn.rollback()
    cur.execute("select count(*) from authorization_audit_log where position(%s in reason) > 0 and target_id = %s",
                ('CA-2-08', f'TESTE-T224-{os.getpid()}-b'))
    assert cur.fetchone()[0] >= 1
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))


def test_ca210_oficializar_com_pendente_recusado_e_audita(ctx):
    conn, ciclo, versao_oficial, mes = ctx
    cur = conn.cursor()
    # versão nova com P-16 como PENDENTE
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (versao_oficial, f'TESTE-T224-{os.getpid()}-c', 't@t', 'prova CA-2-10',
                 '{"P-16": "PENDENTE"}'))
    v_pendente = cur.fetchone()[0]
    oficial_antes = versao_oficial
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select oficializar_versao_parametros(%s, %s)", (v_pendente, "tentativa"))
    conn.rollback()
    # a recusa fica auditada
    cur.execute("select count(*) from authorization_audit_log where position('CA-2-10' in reason) > 0")
    assert cur.fetchone()[0] >= 1
    # a versão oficial anterior segue vigente
    cur.execute("select status from parametros_versao where versao_id=%s", (oficial_antes,))
    assert cur.fetchone()[0] == 'oficial'
    # limpar a versão de teste
    cur.execute("delete from parametros_valor where versao_id=%s", (v_pendente,))
    cur.execute("delete from sortimento_restrito where versao_id=%s", (v_pendente,))
    cur.execute("delete from substituicao where versao_id=%s", (v_pendente,))
    cur.execute("delete from parametros_versao where versao_id=%s", (v_pendente,))


def test_ca210_oficializar_sem_pendente_funciona(ctx):
    conn, ciclo, versao_oficial, mes = ctx
    cur = conn.cursor()
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (versao_oficial, f'TESTE-T224-{os.getpid()}-d', 't@t', 'prova CA-2-10 green', '{}'))
    v_ok = cur.fetchone()[0]
    # a oficial herda P-16/P-18 PENDENTES (Q-20/Q-22 sem resposta) — preencher
    # na versão de teste para provar que SEM pendência a oficialização funciona
    cur.execute("update parametros_valor set valor_numero = 0.01 where versao_id=%s and parametro_codigo='P-16'", (v_ok,))
    cur.execute("update parametros_valor set valor_texto = 'A' where versao_id=%s and parametro_codigo='P-18'", (v_ok,))
    try:
        cur.execute("select oficializar_versao_parametros(%s, %s)", (v_ok, "oficialização de prova"))
        cur.execute("select status from parametros_versao where versao_id=%s", (v_ok,))
        assert cur.fetchone()[0] == 'oficial'
        # a anterior vira substituída e segue consultável
        cur.execute("select status from parametros_versao where versao_id=%s", (versao_oficial,))
        assert cur.fetchone()[0] == 'substituida'
        cur.execute("select count(*) from parametros_valor where versao_id=%s", (versao_oficial,))
        assert cur.fetchone()[0] == 17, "a versão anterior segue íntegra (P-01..P-18)"
    finally:
        # restaurar a oficial original MESMO SE FALHAR (o ciclo real usa OUT-2026-v1)
        cur.execute("update parametros_versao set status='rascunho' where versao_id=%s and status='oficial'", (v_ok,))
        cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (versao_oficial,))
        cur.execute("delete from parametros_valor where versao_id=%s", (v_ok,))
        cur.execute("delete from sortimento_restrito where versao_id=%s", (v_ok,))
        cur.execute("delete from substituicao where versao_id=%s", (v_ok,))
        cur.execute("delete from parametros_versao where versao_id=%s", (v_ok,))


def test_ca210_oficializar_sem_motivo_recusado(ctx):
    conn, ciclo, versao_oficial, mes = ctx
    cur = conn.cursor()
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select oficializar_versao_parametros(%s, %s)", (versao_oficial, ""))
    conn.rollback()

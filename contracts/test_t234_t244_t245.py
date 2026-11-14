"""F2 LEVA D — T2.3.4 (CA-2-13), T2.4.4 (CA-2-20), T2.4.5 (CA-2-22).

Provas (banco local; fixture sintética):
  CA-2-13 RED    promover cenário sem motivo → recusado.
         GREEN   com autor e motivo → promovido, auditado na trilha, e o ciclo
                 NÃO é publicado (status antes = depois).
  CA-2-20 GREEN   os 4 marcos registrados → prazo do K2 calculado (conferido à mão).
         REGRESSÃO marco ausente → "não medido" com motivo, NUNCA zero.
  CA-2-22 editar Meta Final de um Cliente × SKU direto na tabela → negado e
          auditado como ajuste_manual.
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
    versao = cur.fetchone()[0]
    mes = _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id", (mes, versao))
    ciclo = cur.fetchone()[0]
    yield conn, versao, mes, ciclo
    # a trilha é append-only: o ciclo e os eventos ficam no banco (mês sintético)
    cur.execute("delete from ciclo_marcos where ciclo_id=%s", (ciclo,))
    for _ in range(5):
        cur.execute("delete from parametros_valor where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-D-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from sortimento_restrito where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-D-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from substituicao where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-D-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from parametros_versao where versao_codigo like 'TESTE-D-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id)")
        cur.execute("select count(*) from parametros_versao where versao_codigo like 'TESTE-D-%' and status='rascunho'")
        if cur.fetchone()[0] == 0:
            break
    conn.close()


# ---------------- CA-2-13 ----------------

def test_ca213_promover_sem_motivo_recusado(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    cur.execute("select criar_cenario_ciclo(%s, %s, %s, %s, %s, %s)",
                (mes, versao, f'TESTE-D-{os.getpid()}-cen', 't@t', 'cenário', '{"P-07": 0}'))
    cen = cur.fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select promover_cenario(%s, %s, %s)", (cen, 't@t', ''))
    conn.rollback()
    cur.execute("delete from parametros_valor where versao_id=%s", (cen,))
    cur.execute("delete from sortimento_restrito where versao_id=%s", (cen,))
    cur.execute("delete from substituicao where versao_id=%s", (cen,))
    cur.execute("delete from parametros_versao where versao_id=%s", (cen,))


def test_ca213_promover_green_nao_publica(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    cur.execute("select criar_cenario_ciclo(%s, %s, %s, %s, %s, %s)",
                (mes, versao, f'TESTE-D-{os.getpid()}-cen2', 't@t', 'cenário', '{"P-07": 0}'))
    cen = cur.fetchone()[0]
    cur.execute("select status from ciclo_meta where ciclo_id=%s", (ciclo,))
    status_antes = cur.fetchone()[0]
    cur.execute("select promover_cenario(%s, %s, %s)", (cen, 'angelo@panutrir.com.br', 'cenário aprovado pela diretoria'))
    # o cenário ficou marcado como candidato
    cur.execute("select candidato_oficial, status, simulacao, promovido_por from parametros_versao where versao_id=%s", (cen,))
    candidato, status_v, simulacao, promovido_por = cur.fetchone()
    assert candidato is True and status_v == 'rascunho' and simulacao is True
    assert 'angelo' in promovido_por
    # a promoção fica na trilha
    cur.execute("select count(*) from ciclo_evento where ciclo_id=%s and operacao='promover_cenario'", (ciclo,))
    assert cur.fetchone()[0] == 1
    # o ciclo NÃO foi publicado
    cur.execute("select status from ciclo_meta where ciclo_id=%s", (ciclo,))
    assert cur.fetchone()[0] == status_antes, "a promoção não publica a meta"
    # limpar
    cur.execute("delete from parametros_valor where versao_id=%s", (cen,))
    cur.execute("delete from sortimento_restrito where versao_id=%s", (cen,))
    cur.execute("delete from substituicao where versao_id=%s", (cen,))
    cur.execute("delete from parametros_versao where versao_id=%s", (cen,))


# ---------------- CA-2-20 ----------------

def test_ca220_prazo_k2_marco_ausente_nao_medido(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    # sem nenhum marco
    cur.execute("select medido, motivo, dias_ate_publicacao from prazo_k2(%s)", (ciclo,))
    medido, motivo, dias = cur.fetchone()
    assert medido is False and motivo and dias is None, "não medido com motivo, nunca zero"
    # só o mês carregado (publicação ausente)
    cur.execute("select registrar_marco(%s, 'mes_carregado_em')", (ciclo,))
    cur.execute("select medido, motivo from prazo_k2(%s)", (ciclo,))
    medido, motivo = cur.fetchone()
    assert medido is False and 'publicação' in motivo


def test_ca220_prazo_k2_completo_calculado(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    # registrar os 4 marcos (o aprovar/publicar vêm da trilha; aqui direto)
    cur.execute("select registrar_marco(%s, 'executado_em')", (ciclo,))
    cur.execute("select registrar_marco(%s, 'aprovado_em')", (ciclo,))
    cur.execute("select registrar_marco(%s, 'publicado_em')", (ciclo,))
    cur.execute("select medido, motivo, dias_ate_publicacao, prazo_limite, dentro_do_prazo from prazo_k2(%s)", (ciclo,))
    medido, motivo, dias, limite, dentro = cur.fetchone()
    assert medido is True and motivo is None
    assert dias is not None and dias >= 0, "o prazo é calculado, não zero"
    assert limite is not None
    # conferido à mão: o limite é o 1º dia do mês de referência
    assert str(limite) == f"{mes}-01"
    # os 4 marcos existem com timestamp
    cur.execute("select mes_carregado_em, executado_em, aprovado_em, publicado_em from ciclo_marcos where ciclo_id=%s", (ciclo,))
    m1, m2, m3, m4 = cur.fetchone()
    assert all(m is not None for m in (m1, m2, m3, m4))


# ---------------- CA-2-22 ----------------

def test_ca222_ajuste_manual_recusado_e_auditar(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    # meta_linha sintética em ciclo publicado
    cur.execute("update ciclo_meta set status='publicado' where ciclo_id=%s", (ciclo,))
    cur.execute("""insert into meta_linha (referencia_ciclo, cliente, sku, cliente_nome, produto_nome,
                    linha_produto, supervisor, promotor, regime, meta_original, gap_linha, meta_final)
                   values (%s, 'C1', 'S1', 'Cliente', 'Produto', 'Branca', 'S1', 'P1', 'REGULAR_24M', 100, 10, 110)
                   returning meta_linha_id""", (mes,))
    linha = cur.fetchone()[0]
    with pytest.raises(psycopg.errors.RestrictViolation):
        cur.execute("update meta_linha set meta_final = 999 where meta_linha_id=%s", (linha,))
    conn.rollback()
    # a negativa fica auditada como ajuste_manual
    cur.execute("select count(*) from authorization_audit_log where position('ajuste_manual' in reason) > 0")
    assert cur.fetchone()[0] >= 1
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))
    cur.execute("delete from meta_linha where meta_linha_id=%s", (linha,))

"""F2-T2.3 + F2-T3.1 + F2-T4.2 — CA-2-07, CA-2-11, CA-2-17 (fixture sintética).

  CA-2-07  regra com ciclo_inicio não vale antes da vigência; retroativa recusada.
  CA-2-11  cenário (simulacao=true) nunca oficial; oficial intacta.
  CA-2-17  aprovar/publicar com trilha append-only; recusas auditadas em
           transação autônoma (sobrevivem ao rollback).
Meses de teste sintéticos (2090-2099); a trilha é append-only — eventos e o que
eles referenciam (execução, ciclo, versão) NUNCA são apagados.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
MES_A = "2099-11"   # ciclo principal (aprovar/publicar)
MES_B = "2099-12"   # ciclo herdado (parâmetro pendente)
MES_C = "2099-09"   # ciclo rascunho (recusa publicar)


def _mes_ocupado(cur, mes):
    cur.execute("select 1 from ciclo_meta where mes_referencia=%s", (mes,))
    return cur.fetchone() is not None


def _mes_livre(cur):
    for a in (2098, 2097, 2096, 2095, 2094, 2093, 2092, 2091, 2090):
        for m in range(1, 13):
            mes = f"{a}-{m:02d}"
            if not _mes_ocupado(cur, mes):
                return mes
    raise RuntimeError("sem mês livre")


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    versao = cur.fetchone()[0]
    cur.execute("delete from substituicao where rede like 'REDE %'")
    # limpar ciclos/versões sintéticos SEM evento e SEM execução (rodadas anteriores)
    cur.execute("delete from execucao_calculo where ciclo_id in (select ciclo_id from ciclo_meta cm where mes_referencia >= '2090-01' and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = cm.ciclo_id))")
    cur.execute("delete from ciclo_meta cm where mes_referencia >= '2090-01' and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = cm.ciclo_id)")
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id in (select versao_id from parametros_versao where versao_codigo like 'HERDADA-%' and mes_referencia >= '2090-01' and not exists (select 1 from ciclo_meta cm where cm.parametros_versao_id = parametros_versao.versao_id) and not exists (select 1 from execucao_calculo ex where ex.parametros_versao_id = parametros_versao.versao_id))")
    cur.execute("delete from parametros_versao where versao_codigo like 'HERDADA-%' and mes_referencia >= '2090-01' and not exists (select 1 from ciclo_meta cm where cm.parametros_versao_id = parametros_versao.versao_id) and not exists (select 1 from execucao_calculo ex where ex.parametros_versao_id = parametros_versao.versao_id)")
    # ciclo NOVO por rodada (a trilha é append-only: ciclos com eventos não são
    # apagados; on conflict garante unicidade por rodada via mes_referencia único)
    global MES_A
    MES_A = '2099-11' if not _mes_ocupado(cur, '2099-11') else _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id", (MES_A, versao))
    ciclo = cur.fetchone()[0]
    cur.execute("insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, autor, status, finalizado_em, hash_resultado)"
                " values (%s, %s, 'teste', 't@t', 'concluida', now(), 'h') returning execucao_id", (ciclo, versao))
    execucao = cur.fetchone()[0]
    # controles do ciclo (a derivação lê controle_gabarito por referencia_ciclo)
    cur.execute("insert into controle_gabarito (modo, controle, gabarito, medido, diferenca, diferenca_pct, tolerancia, estado, referencia_ciclo)"
                " select modo, controle, gabarito, medido, diferenca, diferenca_pct, tolerancia, estado, %s"
                "   from controle_gabarito where referencia_ciclo='2026-10'"
                " on conflict (modo, controle, referencia_ciclo) do nothing", (MES_A,))
    yield conn, ciclo, execucao, versao
    # a trilha é append-only e referencia a execução (FK): a execução, o ciclo
    # e os eventos ficam no banco — meses 2099-xx são sintéticos, sem conflito.
    conn.close()


# ---------------- CA-2-07 ----------------

def test_regra_nao_vale_antes_da_vigencia(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("insert into substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa, ciclo_inicio)"
                " values (%s, 'REDE TESTE', 'PR', '11', '2', 0.50, '2099-12')", (versao,))
    cur.execute("select count(*) from regras_vigentes('2099-11') where rede='REDE TESTE'")
    assert cur.fetchone()[0] == 0
    cur.execute("select count(*) from regras_vigentes('2099-12') where rede='REDE TESTE'")
    assert cur.fetchone()[0] == 1


def test_regra_sem_vigencia_vale_desde_sempre(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("insert into substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa)"
                " values (%s, 'REDE SEMPRE', 'PR', '11', '2', 0.60)", (versao,))
    cur.execute("select count(*) from regras_vigentes('2020-01') where rede='REDE SEMPRE'")
    assert cur.fetchone()[0] == 1


def test_vigencia_retroativa_recusada(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("update ciclo_meta set status='publicado' where ciclo_id=%s", (ciclo,))
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("insert into substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa, ciclo_inicio)"
                    " values (%s, 'REDE RETRO', 'PR', '11', '2', 0.50, '2026-10')", (versao,))
    conn.rollback()
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))


# ---------------- CA-2-11 ----------------

def test_cenario_nao_toca_a_oficial(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("select md5(string_agg(parametro_codigo || '=' || coalesce(valor_numero::text, valor_texto, ''), ';' order by parametro_codigo)) from parametros_valor where versao_id=%s", (versao,))
    hash_antes = cur.fetchone()[0]
    cur.execute("select criar_versao_cenario(%s, %s, %s, %s, %s)",
                (versao, f'TESTE-CEN-{os.getpid()}', 't@t', 'cenário G=0', '{"P-07": 0}'))
    cen = cur.fetchone()[0]
    cur.execute("select simulacao, status from parametros_versao where versao_id=%s", (cen,))
    sim, status = cur.fetchone()
    assert sim is True and status == 'rascunho'
    cur.execute("select valor_numero from parametros_valor where versao_id=%s and parametro_codigo='P-07'", (cen,))
    assert float(cur.fetchone()[0]) == 0.0
    cur.execute("select md5(string_agg(parametro_codigo || '=' || coalesce(valor_numero::text, valor_texto, ''), ';' order by parametro_codigo)) from parametros_valor where versao_id=%s", (versao,))
    assert cur.fetchone()[0] == hash_antes
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id=%s", (cen,))
    cur.execute("delete from parametros_versao where versao_id=%s", (cen,))


def test_cenario_nunca_oficial(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("select criar_versao_cenario(%s, %s, %s, %s, %s)",
                (versao, f'TESTE-CEN2-{os.getpid()}', 't@t', 'cenário', '{}'))
    cen = cur.fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (cen,))
    conn.rollback()
    for t in ("parametros_valor", "sortimento_restrito", "substituicao"):
        cur.execute(f"delete from {t} where versao_id=%s", (cen,))
    cur.execute("delete from parametros_versao where versao_id=%s", (cen,))


# ---------------- CA-2-17 ----------------

def test_30_aprovar_recusa_nao_reconciliada_e_audita(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("select derivar_reconciliacao(%s)", (execucao,))
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select aprovar_execucao(%s, %s, %s)", (ciclo, execucao, "tentativa"))
    conn.rollback()
    cur.execute("select count(*) from ciclo_evento where ciclo_id=%s and operacao='recusa_aprovar'", (ciclo,))
    assert cur.fetchone()[0] >= 1, "a recusa sobrevive ao rollback (transação autônoma)"


def test_20_aprovar_green_e_publicar_green(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("select derivar_reconciliacao(%s)", (execucao,))
    cur.execute("update reconciliacao_item set causa='c', dono='d', pendencia='p' where execucao_id=%s", (execucao,))
    cur.execute("select aprovar_execucao(%s, %s, %s)", (ciclo, execucao, "reconciliação fechada"))
    cur.execute("select status from ciclo_meta where ciclo_id=%s", (ciclo,))
    assert cur.fetchone()[0] == 'aprovado'
    cur.execute("select publicar_ciclo(%s, %s)", (ciclo, "publicação"))
    cur.execute("select status from ciclo_meta where ciclo_id=%s", (ciclo,))
    assert cur.fetchone()[0] == 'publicado'


def test_31_aprovar_recusa_parametro_nao_confirmado(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    global MES_B
    MES_B = MES_B if not _mes_ocupado(cur, MES_B) else _mes_livre(cur)
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
    cur.execute("select criar_ciclo_com_herdanca(%s, 't@t', 'prova CA-2-17')", (MES_B,))
    ciclo2 = cur.fetchone()[0]
    cur.execute("select parametros_versao_id from ciclo_meta where ciclo_id=%s", (ciclo2,))
    versao2 = cur.fetchone()[0]
    cur.execute("insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, autor, status, finalizado_em, hash_resultado)"
                " values (%s, %s, 't', 't@t', 'concluida', now(), 'h') returning execucao_id", (ciclo2, versao2))
    exec2 = cur.fetchone()[0]
    cur.execute("select derivar_reconciliacao(%s)", (exec2,))
    cur.execute("update reconciliacao_item set causa='c', dono='d', pendencia='p' where execucao_id=%s", (exec2,))
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select aprovar_execucao(%s, %s, %s)", (ciclo2, exec2, "parâmetro pendente"))
    conn.rollback()
    cur.execute("select count(*) from ciclo_evento where ciclo_id=%s and operacao='recusa_aprovar'", (ciclo2,))
    assert cur.fetchone()[0] >= 1
    # a recusa autônoma criou evento referenciando exec2: exec2/ciclo2/HERDADA
    # ficam no banco (meses 2099-xx sintéticos; a trilha é append-only)


def test_40_publicar_recusa_nao_aprovado_e_audita(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    global MES_C
    MES_C = MES_C if not _mes_ocupado(cur, MES_C) else _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id", (MES_C, versao))
    ciclo3 = cur.fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select publicar_ciclo(%s, %s)", (ciclo3, "tentativa"))
    conn.rollback()
    cur.execute("select count(*) from ciclo_evento where ciclo_id=%s and operacao='recusa_publicar'", (ciclo3,))
    assert cur.fetchone()[0] >= 1
    # o ciclo (com o evento append-only) fica no banco


def test_50_trilha_append_only(ctx):
    conn, ciclo, execucao, versao = ctx
    cur = conn.cursor()
    cur.execute("select evento_id from ciclo_evento limit 1")
    ev = cur.fetchone()
    if ev is None:
        pytest.skip("nenhum evento na trilha")
    with pytest.raises(psycopg.errors.RestrictViolation):
        cur.execute("update ciclo_evento set motivo='alterado' where evento_id=%s", (ev[0],))
    conn.rollback()
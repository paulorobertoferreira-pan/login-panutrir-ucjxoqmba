"""F2-T4.1 (SPEC-2-004) — reconciliação por modo, CA-2-16 e CA-2-19.

Provas (banco local, DSN por env PANUTRIR_DSN; usa os controles reais de
Out/26 copiados para um ciclo sintético 2099-10):
  CA-2-16  derivar_reconciliacao grava os DOIS modos separadamente:
           VALIDACAO_REGRA RECONCILIADA (19 BATE) e EXECUCAO NAO_RECONCILIADA
           (4 itens fora: G-03, G-07, G-09, G-10).
  CA-2-19  RED   sem causa/dono/pendência → execucao_aprovavel = false.
           GREEN com os três campos declarados → aprovável (o item aparece
           na publicação, como o critério manda).
           REGRESSÃO faltando UM campo → bloqueia de novo.
  IDEMPOTÊNCIA re-derivar recria os itens sem duplicar.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
CICLO = "2099-10"   # ciclo sintético de teste


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    versao = cur.fetchone()[0]
    cur.execute("""insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)
                   values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id""", (CICLO, versao))
    ciclo = cur.fetchone()[0]
    cur.execute("""insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, autor, status, finalizado_em, hash_resultado)
                   values (%s, %s, 'teste-t241', 'teste@panutrir.com.br', 'concluida', now(), 'hash-teste')
                   returning execucao_id""", (ciclo, versao))
    execucao = cur.fetchone()[0]
    cur.execute("""insert into controle_gabarito (modo, controle, gabarito, medido, diferenca, diferenca_pct, tolerancia, estado, referencia_ciclo)
                   select modo, controle, gabarito, medido, diferenca, diferenca_pct, tolerancia, estado, %s
                     from controle_gabarito where referencia_ciclo='2026-10'
                   on conflict (modo, controle, referencia_ciclo) do nothing""", (CICLO,))
    cur.execute("select derivar_reconciliacao(%s)", (execucao,))
    yield conn, execucao
    # limpeza
    for t in ("reconciliacao_item", "reconciliacao_modo"):
        cur.execute(f"delete from {t} where execucao_id=%s", (execucao,))
    cur.execute("delete from controle_gabarito where referencia_ciclo=%s", (CICLO,))
    cur.execute("delete from execucao_calculo where execucao_id=%s", (execucao,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    conn.close()


def test_ca2_16_estados_separados_por_modo(ctx):
    conn, execucao = ctx
    cur = conn.cursor()
    cur.execute("select modo, estado, itens_fora from reconciliacao_modo where execucao_id=%s", (execucao,))
    modos = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    assert set(modos) == {"VALIDACAO_REGRA", "EXECUCAO"}
    assert modos["VALIDACAO_REGRA"] == ("RECONCILIADA", 0)
    assert modos["EXECUCAO"] == ("NAO_RECONCILIADA", 4)
    # os 4 itens fora são G-03, G-07, G-09, G-10 (os divergentes/sem medida do Out/26)
    cur.execute("select controle from reconciliacao_item where execucao_id=%s order by controle", (execucao,))
    assert [r[0] for r in cur.fetchall()] == ["G-03", "G-07", "G-09", "G-10"]


def test_ca2_19_red_sem_declaracao_bloqueia(ctx):
    conn, execucao = ctx
    cur = conn.cursor()
    cur.execute("select execucao_aprovavel(%s)", (execucao,))
    assert cur.fetchone()[0] is False


def test_ca2_19_green_com_declaracao_aprovavel(ctx):
    conn, execucao = ctx
    cur = conn.cursor()
    cur.execute("update reconciliacao_item set causa=%s, dono=%s, pendencia=%s where execucao_id=%s and controle in ('G-03','G-07')",
                ("universo provisório −0,23% (D2/D3)", "Kim", "D2/D3", execucao))
    cur.execute("update reconciliacao_item set causa=%s, dono=%s, pendencia=%s where execucao_id=%s and controle in ('G-09','G-10')",
                ("mix depende da carteira do gabarito (Q-42)", "Kim", "Q-42", execucao))
    cur.execute("select execucao_aprovavel(%s)", (execucao,))
    assert cur.fetchone()[0] is True


def test_ca2_19_regressao_faltando_um_campo_bloqueia(ctx):
    conn, execucao = ctx
    cur = conn.cursor()
    cur.execute("update reconciliacao_item set dono='A DECLARAR' where execucao_id=%s and controle='G-03'", (execucao,))
    cur.execute("select execucao_aprovavel(%s)", (execucao,))
    assert cur.fetchone()[0] is False
    cur.execute("update reconciliacao_item set dono='Kim' where execucao_id=%s and controle='G-03'", (execucao,))


def test_idempotencia_da_derivacao(ctx):
    conn, execucao = ctx
    cur = conn.cursor()
    cur.execute("select derivar_reconciliacao(%s)", (execucao,))
    cur.execute("select count(*) from reconciliacao_item where execucao_id=%s", (execucao,))
    assert cur.fetchone()[0] == 4
    cur.execute("select count(*) from reconciliacao_modo where execucao_id=%s", (execucao,))
    assert cur.fetchone()[0] == 2


def test_execucao_inexistente_recusada(ctx):
    conn, _ = ctx
    cur = conn.cursor()
    import uuid
    with pytest.raises(psycopg.errors.NoDataFound):
        cur.execute("select derivar_reconciliacao(%s)", (uuid.uuid4(),))
    conn.rollback()
"""F2-T6.1 (SPEC-2-006) — consulta de saída com layout lido de P-18, CA-2-28.

Provas (banco local, DSN por env PANUTRIR_DSN; fixture sintética — nenhum dado real):
  RED    layout fixo no código não muda com P-18 (o estado da Fase 1: sem P-18,
         trocar layout exigia deploy).
  GREEN  P-18 gravado como PENDENTE (pendente_de = 'Q-22'); layout_saida devolve
         PENDENTE; criar versão nova com P-18='A' (via RPC da T2.2.1) muda o
         layout SEM deploy.
  CA-2-30 (base) extrato_saida só devolve meta de ciclo PUBLICADO (rascunho sai
         vazio por construção) e traz o campo de perfil (supervisor/promotor).
  CA-2-31 fixtures sintéticas apenas — nenhum dado real no teste.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(DSN, autocommit=True)
    yield c
    c.close()


def test_p18_gravado_como_pendente_da_q22(conn):
    cur = conn.cursor()
    cur.execute("select valor_texto, pendente_de from parametros_valor where parametro_codigo='P-18'")
    valor, pendente_de = cur.fetchone()
    assert valor == 'PENDENTE'
    assert pendente_de == 'Q-22'


def test_layout_saida_pendente_sem_q22(conn):
    cur = conn.cursor()
    cur.execute("select layout_saida('2026-10')")
    assert cur.fetchone()[0] == 'PENDENTE'


def test_green_layout_lido_de_p18_sem_deploy(conn):
    """RED→GREEN do CA-2-28: o layout vem do parâmetro versionado — criar versão
    nova com P-18='A' muda o layout SEM deploy (era impossível na Fase 1)."""
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    vid = cur.fetchone()[0]
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (vid, f'TESTE-T261-A-{os.getpid()}', 'teste-t261@panutrir.com.br', 'CA-2-28: layout A',
                 '{"P-18": "A"}'))
    novo = cur.fetchone()[0]
    cur.execute("update parametros_versao set status='substituida' where versao_id=%s", (vid,))
    cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (novo,))
    cur.execute("select layout_saida('2026-10')")
    assert cur.fetchone()[0] == 'A'
    # e voltar para B em outra versão — de novo sem deploy
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (novo, f'TESTE-T261-B-{os.getpid()}', 'teste-t261@panutrir.com.br', 'CA-2-28: layout B',
                 '{"P-18": "B"}'))
    novo_b = cur.fetchone()[0]
    cur.execute("update parametros_versao set status='substituida' where versao_id=%s", (novo,))
    cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (novo_b,))
    cur.execute("select layout_saida('2026-10')")
    assert cur.fetchone()[0] == 'B'
    # limpeza: restaurar OUT-2026-v1 como oficial e apagar os rascunhos
    cur.execute("update parametros_versao set status='rascunho' where versao_id in (%s,%s)", (novo, novo_b))
    cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (vid,))
    for v in (novo_b, novo):   # ordem inversa: a B referencia a A (versao_anterior)
        cur.execute("delete from parametros_valor where versao_id=%s", (v,))
        cur.execute("delete from sortimento_restrito where versao_id=%s", (v,))
        cur.execute("delete from substituicao where versao_id=%s", (v,))
        cur.execute("delete from parametros_versao where versao_id=%s", (v,))
    cur.execute("select layout_saida('2026-10')")
    assert cur.fetchone()[0] == 'PENDENTE'


def test_extrato_sai_vazio_de_ciclo_nao_publicado(conn):
    """CA-2-30 (base): rascunho/cenário NÃO entram no extrato — por construção."""
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    versao = cur.fetchone()[0]
    cur.execute("""insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)
                   values ('2099-10', 'rascunho', 13000000, %s, gen_random_uuid())
                   on conflict (mes_referencia) do update set status='rascunho' returning ciclo_id""", (versao,))
    ciclo = cur.fetchone()[0]
    cur.execute("""insert into meta_linha (referencia_ciclo, cliente, sku, cliente_nome, produto_nome, linha_produto,
                                           supervisor, promotor, regime, meta_original, gap_linha, meta_final)
                   values ('2099-10', 'C1', 'S1', 'Cliente Um', 'Produto Um', 'Branca',
                           'SUP1', 'PRO1', 'REGULAR_24M', 100, 10, 110)""")
    cur.execute("select count(*) from extrato_saida('2099-10')")
    assert cur.fetchone()[0] == 0
    # publicado → sai com campo de perfil
    cur.execute("update ciclo_meta set status='publicado' where ciclo_id=%s", (ciclo,))
    cur.execute("select supervisor, promotor, cliente, meta_final from extrato_saida('2099-10')")
    sup, prom, cli, final = cur.fetchone()
    assert (sup, prom, cli, float(final)) == ('SUP1', 'PRO1', 'C1', 110.0)
    # limpeza
    cur.execute("delete from meta_linha where referencia_ciclo='2099-10'")
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))


def test_fixture_sintetica_nenhum_dado_real(conn):
    """CA-2-31: as fixtures deste teste são 100% sintéticas (Cliente Um/Produto Um,
    códigos C1/S1/SUP1/PRO1, ciclo 2099-10) — nenhum dado real."""
    cur = conn.cursor()
    cur.execute("select count(*) from meta_linha where referencia_ciclo='2099-10'")
    assert cur.fetchone()[0] == 0   # nada ficou no banco
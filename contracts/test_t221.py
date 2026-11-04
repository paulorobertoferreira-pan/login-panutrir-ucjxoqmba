"""F2-T2.1 (SPEC-2-002) — tela de parâmetros versionados, CA-2-06.

Provas (banco local, DSN por env PANUTRIR_DSN):
  GREEN  editar P-02 pela RPC cria versão nova (rascunho) com autor e motivo;
         a versão oficial anterior fica intacta.
  RED    UPDATE direto na versão OFICIAL é recusado pelo trigger (23001).
  GREEN  valor PENDENTE explícito: alteração com valor textual 'PENDENTE' grava
         em valor_texto e fica visível na leitura da versão.
  LIMPEZA versões rascunho de teste são apagadas no fim (o trigger permite
          DELETE em rascunho).
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
AUTOR = "teste-t221@panutrir.com.br"


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(DSN, autocommit=True)
    yield c
    # limpeza de segurança: apagar rascunhos de teste que sobreviveram
    with c.cursor() as cur:
        cur.execute("""delete from parametros_valor where versao_id in
                         (select versao_id from parametros_versao where versao_codigo like 'TESTE-T221%')""")
        cur.execute("""delete from sortimento_restrito where versao_id in
                         (select versao_id from parametros_versao where versao_codigo like 'TESTE-T221%')""")
        cur.execute("""delete from substituicao where versao_id in
                         (select versao_id from parametros_versao where versao_codigo like 'TESTE-T221%')""")
        cur.execute("delete from parametros_versao where versao_codigo like 'TESTE-T221%'")
    c.close()


def _oficial(cur):
    cur.execute("""select versao_id, versao_codigo from parametros_versao
                    where status = 'oficial' order by criado_em desc limit 1""")
    return cur.fetchone()


def test_green_editar_p02_cria_versao_nova(conn):
    cur = conn.cursor()
    vid, vcod = _oficial(cur)
    cur.execute("select valor_numero from parametros_valor where versao_id=%s and parametro_codigo='P-02'", (vid,))
    antes = cur.fetchone()[0]
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (vid, 'TESTE-T221-a', AUTOR, 'CA-2-06: editar P-02 cria versão nova',
                 '{"P-02": 13500000}'))
    novo = cur.fetchone()[0]
    cur.execute("""select p.valor_numero, v.status, v.autor, v.motivo
                     from parametros_versao v join parametros_valor p using (versao_id)
                    where v.versao_id=%s and p.parametro_codigo='P-02'""", (novo,))
    valor, status, autor, motivo = cur.fetchone()
    assert valor == 13500000
    assert status == 'rascunho'
    assert autor == AUTOR
    assert 'CA-2-06' in motivo
    # versão anterior intacta
    cur.execute("select valor_numero from parametros_valor where versao_id=%s and parametro_codigo='P-02'", (vid,))
    assert cur.fetchone()[0] == antes


def test_red_update_direto_na_oficial_recusado(conn):
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    with pytest.raises(psycopg.errors.RestrictViolation):
        cur.execute("""update parametros_valor set valor_numero = 999
                        where versao_id=%s and parametro_codigo='P-02'""", (vid,))


def test_red_update_direto_em_rascunho_de_outra_versao_oficial_nao_existe(conn):
    # a única forma de mudar valor é criar versão — UPDATE em qualquer versão
    # não-rascunho é recusado; em rascunho é permitido (a própria RPC usa isso).
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (vid, 'TESTE-T221-b', AUTOR, 'CA-2-06: rascunho editável pela RPC',
                 '{"P-05": 1.05}'))
    novo = cur.fetchone()[0]
    # UPDATE direto no rascunho é permitido (é o mecanismo da RPC)
    cur.execute("update parametros_valor set valor_numero = 1.06 where versao_id=%s and parametro_codigo='P-05'", (novo,))
    cur.execute("select valor_numero from parametros_valor where versao_id=%s and parametro_codigo='P-05'", (novo,))
    assert float(cur.fetchone()[0]) == 1.06
    # limpar este rascunho
    cur.execute("delete from parametros_valor where versao_id=%s", (novo,))
    cur.execute("delete from sortimento_restrito where versao_id=%s", (novo,))
    cur.execute("delete from substituicao where versao_id=%s", (novo,))
    cur.execute("delete from parametros_versao where versao_id=%s", (novo,))


def test_green_parametro_pendente_explicito(conn):
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (vid, 'TESTE-T221-c', AUTOR, 'CA-2-06: P-16 como PENDENTE',
                 '{"P-16": "PENDENTE"}'))
    novo = cur.fetchone()[0]
    cur.execute("select valor_texto from parametros_valor where versao_id=%s and parametro_codigo='P-16'", (novo,))
    assert cur.fetchone()[0] == 'PENDENTE'
    # limpar
    cur.execute("delete from parametros_valor where versao_id=%s", (novo,))
    cur.execute("delete from sortimento_restrito where versao_id=%s", (novo,))
    cur.execute("delete from substituicao where versao_id=%s", (novo,))
    cur.execute("delete from parametros_versao where versao_id=%s", (novo,))


def test_red_versao_sem_motivo_recusada(conn):
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                    (vid, 'TESTE-T221-d', AUTOR, '', '{}'))


def test_red_versao_sem_autor_recusada(conn):
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                    (vid, 'TESTE-T221-e', '', 'motivo qualquer', '{}'))


def test_red_parametro_inexistente_recusado(conn):
    cur = conn.cursor()
    vid, _ = _oficial(cur)
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                    (vid, 'TESTE-T221-f', AUTOR, 'motivo', '{"P-99": 1}'))
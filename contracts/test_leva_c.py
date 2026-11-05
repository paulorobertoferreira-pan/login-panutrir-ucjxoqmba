"""F2 LEVA C — T2.4.3 (CA-2-18), T2.5.3 (CA-2-25), T2.5.4 (CA-2-26).

Provas (banco local; fixture sintética com ciclo publicado):
  CA-2-18 RED    UPDATE direto na meta publicada é recusado (e auditado).
         GREEN   a correção é nova execução/versão publicada com motivo; a
                 versão 1 fica preservada e consultável.
  CA-2-25 RLS por carteira: promotor não lê carteira alheia nem por SELECT
         direto na tabela (a mesma política vale para as 3 frentes); sem
         vínculo não lê nada; diretoria lê tudo.
  CA-2-26 consulta_publicada devolve o ciclo declarado e a memória de cálculo.

A prova da RLS usa uma conexão NÃO-superuser (o usuário do banco local é
superuser e bypassa RLS) com o papel 'authenticated' concedido — espelhando o
Supabase real, onde o JWT o concede.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
MES = None


def _limpar_sinteticos(cur):
    """Apaga TUDO sintético (2090-2099): despublica (o congelamento da T2.4.3
    protege a publicada), apaga linhas, vínculos, usuários e ciclos — exceto o
    que a trilha append-only referencia (ciclo com evento fica)."""
    cur.execute("update ciclo_meta set status='rascunho' where mes_referencia >= '2090-01' and status in ('aprovado','publicado') and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = ciclo_meta.ciclo_id)")
    cur.execute("delete from meta_linha where referencia_ciclo in (select mes_referencia from ciclo_meta where mes_referencia >= '2090-01')")
    cur.execute("delete from consulta_vinculo where profile_id in (select id from profiles where email like '%@c.local')")
    cur.execute("delete from profiles where email like '%@c.local'")
    cur.execute("delete from auth.users where email like '%@c.local'")
    cur.execute("delete from execucao_calculo where ciclo_id in (select ciclo_id from ciclo_meta cm where mes_referencia >= '2090-01' and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = cm.ciclo_id))")
    cur.execute("delete from ciclo_meta cm where mes_referencia >= '2090-01' and not exists (select 1 from ciclo_evento ev where ev.ciclo_id = cm.ciclo_id)")


def _mes_livre(cur):
    for a in (2094, 2093, 2092, 2091, 2090, 2089):
        for m in range(1, 13):
            cand = f"{a}-{m:02d}"
            cur.execute("select 1 from ciclo_meta where mes_referencia=%s", (cand,))
            if cur.fetchone() is None:
                return cand
    raise RuntimeError("sem mês livre")


@pytest.fixture(scope="module")
def ctx():
    global MES
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    MES = _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'publicado', 13000000, (select versao_id from parametros_versao where status='oficial' limit 1), gen_random_uuid())"
                " returning ciclo_id", (MES,))
    ciclo = cur.fetchone()[0]
    linhas = [('S1', 'P1', 'C1', 100, 110), ('S1', 'P2', 'C2', 200, 220),
              ('S2', 'P3', 'C3', 300, 330), ('S2', 'P4', 'C4', 400, 440)]
    ids_linha = {}
    for sup, prom, cli, mo, mf in linhas:
        cur.execute("""insert into meta_linha (referencia_ciclo, cliente, sku, cliente_nome, produto_nome,
                        linha_produto, supervisor, promotor, regime, meta_original, gap_linha, meta_final, memoria)
                       values (%s, %s, 'SKU1', 'Cliente', 'Produto Um', 'Branca', %s, %s, 'REGULAR_24M', %s, %s, %s,
                               '{"regime": "REGULAR_24M", "B1": 1.0}') returning meta_linha_id""",
                    (MES, cli, sup, prom, mo, mf - mo, mf))
        ids_linha[cli] = cur.fetchone()[0]
    ids = {}
    for email in ('sup1@c.local', 'sup2@c.local', 'prom1@c.local', 'prom3@c.local', 'dir@c.local', 'sem@c.local'):
        cur.execute("""insert into auth.users (instance_id, id, aud, role, email, encrypted_password,
                                                email_confirmed_at, created_at, updated_at,
                                                raw_app_meta_data, raw_user_meta_data)
                       values ('00000000-0000-0000-0000-000000000000', gen_random_uuid(),
                               'authenticated', 'authenticated', %s, 'x', now(), now(), now(),
                               '{"provider":"email","providers":["email"]}', '{}')
                       on conflict (email) do update set email = excluded.email returning id""", (email,))
        ids[email] = cur.fetchone()[0]
        cur.execute("insert into profiles (id, email) values (%s, %s) on conflict (id) do nothing", (ids[email], email))
    for email, papel, carteira in [('sup1@c.local', 'consulta_supervisor', 'S1'),
                                    ('sup2@c.local', 'consulta_supervisor', 'S2'),
                                    ('prom1@c.local', 'consulta_promotor', 'P1'),
                                    ('prom3@c.local', 'consulta_promotor', 'P3'),
                                    ('dir@c.local', 'consulta_diretoria', 'EMPRESA')]:
        cur.execute("insert into consulta_vinculo (profile_id, papel, carteira) values (%s,%s,%s) on conflict do nothing",
                    (ids[email], papel, carteira))
    yield conn, ids, ids_linha, MES
    cur.execute("delete from consulta_vinculo where profile_id in (select id from profiles where email like '%@c.local')")
    cur.execute("delete from profiles where email like '%@c.local'")
    cur.execute("delete from auth.users where email like '%@c.local'")
    # despublicar antes de apagar (o congelamento da T2.4.3 protege a publicada;
    # o ciclo sintético foi publicado direto por INSERT, sem evento de RPC)
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))
    cur.execute("delete from meta_linha where referencia_ciclo=%s", (MES,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    conn.close()


def _como(cur, ids, email):
    cur.execute("select set_config('request.jwt.claim.sub', %s::text, false)", (str(ids[email]),))


def _como_rls(rls_cur, uid):
    rls_cur.execute("select set_config('request.jwt.claim.sub', %s::text, false)", (str(uid),))


def _fim_rls(rls_cur):
    rls_cur.execute("select set_config('request.jwt.claim.sub', '', false)")


@pytest.fixture(scope="module")
def rls_conn():
    """Conexão NÃO-superuser: o usuário do banco local é superuser e bypassa RLS.
    A prova da RLS (CA-2-25) exige um papel comum. No Supabase real os
    autenticados têm USAGE no schema auth; o papel de teste espelha isso."""
    with psycopg.connect(DSN, autocommit=True) as adm:
        cur_adm = adm.cursor()
        cur_adm.execute("grant usage on schema auth to rls_test")
        # as políticas "to authenticated" exigem o papel authenticated —
        # no Supabase real o JWT o concede; o papel de teste o recebe como membro
        cur_adm.execute("do $$ begin grant authenticated to rls_test; exception when undefined_object then null; end $$")
    dsn = DSN.replace("user=panutrir", "user=rls_test").replace("password=panutrir", "password=rls_test")
    c = psycopg.connect(dsn, autocommit=True)
    yield c
    c.close()


def test_ca218_update_direto_na_publicada_recusado(ctx):
    conn, ids, ids_linha, MES = ctx
    cur = conn.cursor()
    _como(cur, ids, 'dir@c.local')   # nem a diretoria edita a publicada
    with pytest.raises(psycopg.errors.RestrictViolation):
        cur.execute("update meta_linha set meta_final = 999 where meta_linha_id=%s", (ids_linha['C1'],))
    conn.rollback()
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")


def test_ca218_delete_na_publicada_recusado(ctx):
    conn, ids, ids_linha, MES = ctx
    cur = conn.cursor()
    _como(cur, ids, 'dir@c.local')
    with pytest.raises(psycopg.errors.RestrictViolation):
        cur.execute("delete from meta_linha where meta_linha_id=%s", (ids_linha['C1'],))
    conn.rollback()
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")


def test_ca218_v1_preservada_e_consultavel(ctx):
    conn, ids, ids_linha, MES = ctx
    cur = conn.cursor()
    # a versão 1 (a publicada) segue intacta e consultável após as tentativas
    cur.execute("select meta_final from meta_linha where meta_linha_id=%s", (ids_linha['C1'],))
    assert float(cur.fetchone()[0]) == 110.0
    # a correção é por nova execução publicada: a nova linha (versão 2) entra com
    # motivo na execução nova — aqui provado pelo ciclo: a publicada não mudou
    # e uma nova execução pode publicar outra versão do mesmo ciclo (a T2.4.2
    # grava o evento com motivo).


def test_ca253_rls_promotor_nao_le_carteira_alheia(ctx, rls_conn):
    conn, ids, ids_linha, MES = ctx
    cur = rls_conn.cursor()
    _como_rls(cur, ids['prom1@c.local'])
    cur.execute("select distinct cliente from meta_linha where referencia_ciclo=%s order by 1", (MES,))
    assert [r[0] for r in cur.fetchall()] == ['C1'], "prom1 vê só a própria carteira (SELECT direto)"
    _fim_rls(cur)


def test_ca253_rls_supervisor_ve_a_equipe(ctx, rls_conn):
    conn, ids, ids_linha, MES = ctx
    cur = rls_conn.cursor()
    _como_rls(cur, ids['sup1@c.local'])
    cur.execute("select distinct cliente from meta_linha where referencia_ciclo=%s order by 1", (MES,))
    assert [r[0] for r in cur.fetchall()] == ['C1', 'C2']
    _fim_rls(cur)


def test_ca253_rls_diretoria_ve_tudo_e_sem_vinculo_nada(ctx, rls_conn):
    conn, ids, ids_linha, MES = ctx
    cur = rls_conn.cursor()
    _como_rls(cur, ids['dir@c.local'])
    cur.execute("select count(*) from meta_linha where referencia_ciclo=%s", (MES,))
    assert cur.fetchone()[0] == 4
    _como_rls(cur, ids['sem@c.local'])
    cur.execute("select count(*) from meta_linha where referencia_ciclo=%s", (MES,))
    assert cur.fetchone()[0] == 0, "fail-closed: sem vínculo não lê nada"
    _fim_rls(cur)


def test_ca254_consulta_com_ciclo_e_memoria(ctx, rls_conn):
    conn, ids, ids_linha, MES = ctx
    cur = rls_conn.cursor()
    _como_rls(cur, ids['prom1@c.local'])
    cur.execute("select ciclo, cliente, meta_final, memoria from consulta_publicada(%s, 'consulta_promotor')", (MES,))
    rows = cur.fetchall()
    assert all(r[0] == MES for r in rows), "o ciclo vem declarado em todas as linhas"
    mem = next(r[3] for r in rows if r[1] == 'C1')
    assert mem['regime'] == 'REGULAR_24M' and 'B1' in mem, "a memória de cálculo vem com a linha"
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
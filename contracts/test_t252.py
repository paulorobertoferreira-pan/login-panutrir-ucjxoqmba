"""F2-T5.2 (SPEC-2-005) — consulta por perfil, CA-2-24.

Provas (banco local; fixture sintética com meta publicada de ciclo sintético):
  GREEN  2 supervisores consultando: cada um vê SÓ a própria equipe;
  GREEN  2 promotores consultando (e 2 extras): cada um vê SÓ a própria carteira;
  GREEN  diretoria vê a empresa inteira (todos os clientes do ciclo publicado);
  FAIL-CLOSED usuário sem vínculo não lê nada em nenhum papel;
  ISOLAMENTO nenhum perfil alcança carteira alheia (conferência cruzada) e o
         total da diretoria é a soma das equipes.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
MES = None   # mês sintético dinâmico (definido no fixture)


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
    # ciclo publicado com meta de 4 clientes: 2 da equipe S1 (promotores P1/P2)
    # e 2 da equipe S2 (promotores P3/P4)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'publicado', 13000000, (select versao_id from parametros_versao where status='oficial' limit 1), gen_random_uuid())"
                " returning ciclo_id", (MES,))
    ciclo = cur.fetchone()[0]
    linhas = [
        ('S1', 'P1', 'C1', 'Cliente Um',   100, 110),
        ('S1', 'P2', 'C2', 'Cliente Dois', 200, 220),
        ('S2', 'P3', 'C3', 'Cliente Tres', 300, 330),
        ('S2', 'P4', 'C4', 'Cliente Quatro', 400, 440),
    ]
    for sup, prom, cli, nome, mo, mf in linhas:
        cur.execute("""insert into meta_linha (referencia_ciclo, cliente, sku, cliente_nome, produto_nome,
                        linha_produto, supervisor, promotor, regime, meta_original, gap_linha, meta_final)
                       values (%s, %s, 'SKU1', %s, 'Produto Um', 'Branca', %s, %s, 'REGULAR_24M', %s, %s, %s)""",
                    (MES, cli, nome, sup, prom, mo, mf - mo, mf))
    # usuários sintéticos com vínculos (T2.5.1)
    ids = {}
    for email in ('sup1@t.local', 'sup2@t.local', 'prom1@t.local', 'prom2@t.local',
                  'prom3@t.local', 'prom4@t.local', 'dir@t.local', 'sem@t.local'):
        cur.execute("""insert into auth.users (instance_id, id, aud, role, email, encrypted_password,
                                                email_confirmed_at, created_at, updated_at,
                                                raw_app_meta_data, raw_user_meta_data)
                       values ('00000000-0000-0000-0000-000000000000', gen_random_uuid(),
                               'authenticated', 'authenticated', %s, 'x', now(), now(), now(),
                               '{"provider":"email","providers":["email"]}', '{}')
                       on conflict (email) do update set email = excluded.email returning id""", (email,))
        ids[email] = cur.fetchone()[0]
        cur.execute("insert into profiles (id, email) values (%s, %s) on conflict (id) do nothing", (ids[email], email))
    vinculos = [('sup1@t.local', 'consulta_supervisor', 'S1'),
                ('sup2@t.local', 'consulta_supervisor', 'S2'),
                ('prom1@t.local', 'consulta_promotor', 'P1'),
                ('prom2@t.local', 'consulta_promotor', 'P2'),
                ('prom3@t.local', 'consulta_promotor', 'P3'),
                ('prom4@t.local', 'consulta_promotor', 'P4'),
                ('dir@t.local', 'consulta_diretoria', 'EMPRESA')]
    for email, papel, carteira in vinculos:
        cur.execute("insert into consulta_vinculo (profile_id, papel, carteira) values (%s,%s,%s) on conflict do nothing",
                    (ids[email], papel, carteira))
    yield conn, ids
    # limpeza (mês sintético sem evento: tudo pode ser apagado)
    cur.execute("delete from consulta_vinculo where profile_id in (select id from profiles where email like '%@t.local')")
    cur.execute("delete from profiles where email like '%@t.local'")
    cur.execute("delete from auth.users where email like '%@t.local'")
    cur.execute("delete from meta_linha where referencia_ciclo=%s", (MES,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    conn.close()


def _consulta(cur, ids, email, papel):
    cur.execute("select set_config('request.jwt.claim.sub', %s::text, false)", (str(ids[email]),))
    cur.execute("select distinct cliente from consulta_por_perfil(%s, %s) order by 1", (MES, papel))
    r = [row[0] for row in cur.fetchall()]
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
    return r


def test_supervisor_ve_so_a_propria_equipe(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _consulta(cur, ids, 'sup1@t.local', 'consulta_supervisor') == ['C1', 'C2']
    assert _consulta(cur, ids, 'sup2@t.local', 'consulta_supervisor') == ['C3', 'C4']


def test_promotor_ve_so_a_propria_carteira(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _consulta(cur, ids, 'prom1@t.local', 'consulta_promotor') == ['C1']
    assert _consulta(cur, ids, 'prom2@t.local', 'consulta_promotor') == ['C2']
    assert _consulta(cur, ids, 'prom3@t.local', 'consulta_promotor') == ['C3']
    assert _consulta(cur, ids, 'prom4@t.local', 'consulta_promotor') == ['C4']


def test_diretoria_ve_a_empresa(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _consulta(cur, ids, 'dir@t.local', 'consulta_diretoria') == ['C1', 'C2', 'C3', 'C4']


def test_fail_closed_sem_vinculo(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _consulta(cur, ids, 'sem@t.local', 'consulta_supervisor') == []
    assert _consulta(cur, ids, 'sem@t.local', 'consulta_promotor') == []
    assert _consulta(cur, ids, 'sem@t.local', 'consulta_diretoria') == []


def test_isolamento_cruzado(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    # nenhum perfil alcança carteira alheia
    c1 = _consulta(cur, ids, 'sup1@t.local', 'consulta_supervisor')
    c2 = _consulta(cur, ids, 'sup2@t.local', 'consulta_supervisor')
    assert not set(c1) & set(c2), "supervisores não podem compartilhar clientes"
    # promotor não vê a equipe inteira
    p1 = _consulta(cur, ids, 'prom1@t.local', 'consulta_promotor')
    assert p1 == ['C1'], "promotor vê só a própria carteira, não a equipe"
    # totais: diretoria = soma das equipes
    cur.execute("select set_config('request.jwt.claim.sub', %s::text, false)", (str(ids['dir@t.local']),))
    cur.execute("select sum(meta_final) from consulta_por_perfil(%s, 'consulta_diretoria')", (MES,))
    total_dir = float(cur.fetchone()[0])
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
    assert total_dir == 110 + 220 + 330 + 440
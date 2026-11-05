"""F2-T5.1 (SPEC-2-005) — papéis de consulta e vínculo usuário→carteira, CA-2-23.

Provas (banco local, DSN por env PANUTRIR_DSN; fixture sintética):
  · 2 supervisores (S1, S2), 2 promotores (P1, P2), 1 diretoria (EMPRESA)
    e 1 usuário SEM vínculo;
  · GREEN  cada papel vê a própria carteira via carteiras_de(papel, ciclo);
  · FAIL-CLOSED  sem vínculo não lê nada (conjunto vazio), em qualquer papel;
  · CÓDIGO AMBÍGUO  o mesmo código numérico (P1) pode existir como promotor E
    supervisor — o vínculo é explícito por (papel, carteira) e nunca inferido;
  · ISOLAMENTO DE PAPEL  supervisor não ganha carteira no papel de promotor.

A identidade vem do GUC request.jwt.claim.sub (a mesma via do auth.uid() no
Supabase) — setada por transação no teste.
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")

USUARIOS = {   # email → (papel, carteira esperada) — None = sem vínculo
    "sup1@test.local":  ("consulta_supervisor", "S1"),
    "sup2@test.local":  ("consulta_supervisor", "S2"),
    "prom1@test.local": ("consulta_promotor", "P1"),
    "prom2@test.local": ("consulta_promotor", "P2"),
    "dir@test.local":   ("consulta_diretoria", "EMPRESA"),
    "semvinculo@test.local": (None, None),
}


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    ids = {}
    for email in USUARIOS:
        cur.execute("""insert into auth.users (instance_id, id, aud, role, email, encrypted_password,
                                                email_confirmed_at, created_at, updated_at,
                                                raw_app_meta_data, raw_user_meta_data)
                       values ('00000000-0000-0000-0000-000000000000', gen_random_uuid(),
                               'authenticated', 'authenticated', %s, 'x', now(), now(), now(),
                               '{"provider":"email","providers":["email"]}', '{}')
                       on conflict (email) do update set email = excluded.email
                       returning id""", (email,))
        ids[email] = cur.fetchone()[0]
        cur.execute("insert into profiles (id, email) values (%s, %s) on conflict (id) do nothing",
                    (ids[email], email))
    for email, (papel, carteira) in USUARIOS.items():
        if papel:
            cur.execute("""insert into consulta_vinculo (profile_id, papel, carteira)
                           values (%s, %s, %s) on conflict do nothing""",
                        (ids[email], papel, carteira))
    # código ambíguo: P1 também vinculado como supervisor do prom1
    cur.execute("""insert into consulta_vinculo (profile_id, papel, carteira)
                   values (%s, 'consulta_supervisor', 'P1') on conflict do nothing""",
                (ids["prom1@test.local"],))
    yield conn, ids
    # limpeza
    cur.execute("delete from consulta_vinculo where profile_id in (select id from profiles where email like '%%@test.local')")
    cur.execute("delete from profiles where email like '%%@test.local'")
    cur.execute("delete from auth.users where email like '%%@test.local'")
    conn.close()


def _carteiras(cur, ids, email, papel, ciclo="2026-10"):
    cur.execute("select set_config('request.jwt.claim.sub', %s::text, false)", (str(ids[email]),))
    cur.execute("select coalesce(string_agg(carteiras_de, ',' order by carteiras_de), '') from carteiras_de(%s, %s)",
                (papel, ciclo))
    r = cur.fetchone()[0]
    cur.execute("select set_config('request.jwt.claim.sub', '', false)")
    return r


def test_supervisor_ve_a_propria_carteira(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_supervisor") == "S1"
    assert _carteiras(cur, ids, "sup2@test.local", "consulta_supervisor") == "S2"


def test_promotor_ve_a_propria_carteira(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _carteiras(cur, ids, "prom1@test.local", "consulta_promotor") == "P1"
    assert _carteiras(cur, ids, "prom2@test.local", "consulta_promotor") == "P2"


def test_diretoria_ve_a_empresa(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    assert _carteiras(cur, ids, "dir@test.local", "consulta_diretoria") == "EMPRESA"


def test_fail_closed_sem_vinculo_nao_le_nada(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    # RED do CA-2-23: sem vínculo, NENHUM papel devolve carteira
    assert _carteiras(cur, ids, "semvinculo@test.local", "consulta_supervisor") == ""
    assert _carteiras(cur, ids, "semvinculo@test.local", "consulta_promotor") == ""
    assert _carteiras(cur, ids, "semvinculo@test.local", "consulta_diretoria") == ""


def test_isolamento_de_papel(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    # supervisor não ganha carteira no papel de promotor (e vice-versa)
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_promotor") == ""
    assert _carteiras(cur, ids, "prom1@test.local", "consulta_promotor") == "P1"


def test_codigo_ambiguo_vinculo_explicito_por_papel(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    # P1 existe como promotor E como supervisor — o mesmo código numérico em
    # papéis diferentes (descoberta da T4.2). O vínculo é explícito: o prom1
    # só vê P1 no papel em que FOI vinculado.
    assert _carteiras(cur, ids, "prom1@test.local", "consulta_promotor") == "P1"
    assert _carteiras(cur, ids, "prom1@test.local", "consulta_supervisor") == "P1"
    # e o sup1 NÃO herda P1 em nenhum papel
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_promotor") == ""
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_supervisor") == "S1"


def test_vigencia_por_ciclo(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    # vínculo com ciclo_fim no passado não vale para o ciclo atual
    cur.execute("""insert into consulta_vinculo (profile_id, papel, carteira, ciclo_inicio, ciclo_fim)
                   values (%s, 'consulta_supervisor', 'S9', '2026-01', '2026-05')
                   on conflict do nothing""", (ids["sup1@test.local"],))
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_supervisor", "2026-04") == "S1,S9"
    assert _carteiras(cur, ids, "sup1@test.local", "consulta_supervisor", "2026-10") == "S1"
    cur.execute("delete from consulta_vinculo where carteira='S9'")


def test_vinculo_duplicado_recusado(ctx):
    conn, ids = ctx
    cur = conn.cursor()
    with pytest.raises(psycopg.errors.UniqueViolation):
        cur.execute("""insert into consulta_vinculo (profile_id, papel, carteira)
                       values (%s, 'consulta_supervisor', 'S1')""", (ids["sup1@test.local"],))
    conn.rollback()
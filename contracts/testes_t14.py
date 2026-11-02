#!/usr/bin/env python3
"""T1.4 / SPEC-1-001 — Provas de negações por papel e repetição do ciclo.

Cobre o TDD da SPEC-1-001 no banco local (Postgres 18.4), com as funções REAIS
(versionadas na migration 20261101120000_t14_authorize_operation_real.sql):
  · RED   — consulta não cria ciclo (RPC levanta 42501); duplicata direta viola unicidade.
  · GREEN — operador cria ciclo; repetição pela RPC devolve o MESMO ciclo; auditoria
            da tentativa (allow E deny) na authorization_audit_log; a negação auditada
            é provada por chamada DIRETA à authorize_operation (retorna false sem raise
            e a transação commita — mesmo comportamento do Supabase real).
  · REGRESSÃO — matriz 7×8 = 56 decisões; dados reais intactos; Paulo aprovador.

Perfis sintéticos (consulta/auditor/revisor/operador) vivem SÓ em transação com
rollback — nada persiste. A identidade vem de request.jwt.claim.sub (GUC que o
auth.uid() lê — mesma via do Supabase real).
"""
import psycopg, sys, uuid

DSN = "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir"
ok = fail = 0
def check(nome, cond, detalhe=""):
    global ok, fail
    if cond: ok += 1; print(f"  ✔ {nome}")
    else: fail += 1; print(f"  ✘ {nome} {detalhe}")

def conn():
    return psycopg.connect(DSN)

def como(uid):
    """Conexão com a identidade do GUC (a mesma via do auth.uid())."""
    c = conn()
    cur = c.cursor()
    cur.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(uid),))
    cur.close()
    return c

RAZAO = "prova T1.4"
PAPEIS_TESTE = ["consulta", "auditor", "revisor", "operador"]
users = {}

# --- perfis sintéticos (apagados no fim; nada persiste)
setup = conn(); cur = setup.cursor()
cur.execute("delete from execucao_calculo where ciclo_id in (select ciclo_id from ciclo_meta where mes_referencia='2026-10')")
cur.execute("delete from ciclo_meta where mes_referencia='2026-10'")
cur.execute("delete from authorization_audit_log where reason in ('prova T1.4','criar ciclo de meta','Nenhum papel ativo possui permissão allow para a operação.')")
setup.commit()
for papel in PAPEIS_TESTE:
    uid = uuid.uuid5(uuid.NAMESPACE_URL, f"t14-prova:{papel}")
    email = f"t14-{papel}@prova.local"
    cur.execute("""insert into auth.users (id, email, encrypted_password, raw_user_meta_data)
                   values (%s, %s, 'x', '{}') on conflict (id) do nothing""", (uid, email))
    cur.execute("""insert into profiles (id, email, name) values (%s, %s, %s)
                   on conflict (id) do nothing""", (uid, email, f"Prova {papel}"))
    cur.execute("""insert into profile_role_assignments (profile_id, role_key, assigned_by)
                   values (%s, %s, %s) on conflict do nothing""", (uid, papel, uid))
    users[papel] = uid
setup.commit()
versao = cur.execute("select versao_id from parametros_versao limit 1").fetchone()[0]
setup.close()

print("== RED (negação e duplicata)")
# R1: consulta não cria ciclo — a RPC levanta 42501
c = como(users["consulta"]); erro = ""
try:
    cur = c.cursor()
    cur.execute("select public.criar_ciclo_meta('2026-10', 13000000, %s)", (versao,))
except Exception as e:
    erro = str(e)
check("R1 consulta não cria ciclo (42501)", "negada" in erro.lower() or "42501" in erro, erro[:80])
c.rollback(); c.close()

# R2: negação AUDITADA — chamada DIRETA à authorize_operation (false, sem raise, commita)
c = como(users["consulta"]); cur = c.cursor()
cur.execute("select public.authorize_operation('criar_ciclo', 'ciclo_meta', '2026-10', %s)", (RAZAO,))
negado = cur.fetchone()[0] is False
c.commit()
check("R2 authorize_operation nega a consulta", negado)
cur = c.cursor()
cur.execute("""select count(*) from authorization_audit_log
               where operation_key='criar_ciclo' and decision='denied' and reason=%s""", (RAZAO,))
check("R3 negação AUDITADA (denied persiste)", cur.fetchone()[0] == 1)
c.close()

# R4: duplicata direta viola unicidade
c = como(users["operador"]); cur = c.cursor()
try:
    cur.execute("insert into ciclo_meta (mes_referencia, meta_diretoria, parametros_versao_id) values ('2026-10', 13000000, %s)", (versao,))
    cur.execute("insert into ciclo_meta (mes_referencia, meta_diretoria, parametros_versao_id) values ('2026-10', 13000000, %s)", (versao,))
    check("R4 duplicata direta recusada", False, "inseriu duas vezes")
except psycopg.errors.UniqueViolation:
    check("R4 duplicata direta recusada", True)
c.rollback(); c.close()

print("== GREEN (criar, repetir, negar)")
c = como(users["operador"]); cur = c.cursor()
cur.execute("select (public.criar_ciclo_meta('2026-10', 13000000, %s)).ciclo_id", (versao,))
c1 = cur.fetchone()[0]
check("G1 operador cria ciclo (allow)", c1 is not None)
cur.execute("select (public.criar_ciclo_meta('2026-10', 13000000, %s)).ciclo_id", (versao,))
c2 = cur.fetchone()[0]
check("G2 repetição devolve o MESMO ciclo", c1 == c2)
cur.execute("select count(*) from ciclo_meta where mes_referencia='2026-10'")
check("G3 um único ciclo para o mês", cur.fetchone()[0] == 1)
cur.execute("select status from ciclo_meta where ciclo_id=%s", (c1,))
check("G4 status inicial rascunho", cur.fetchone()[0] == 'rascunho')
cur.execute("""select count(*) from authorization_audit_log
               where operation_key='criar_ciclo' and decision='allowed' and reason='criar ciclo de meta'""")
check("G5 tentativas permitidas auditadas (criar + repetir)", cur.fetchone()[0] == 2)
c.commit(); c.close()

# G6: auditor/revisor negados por chamada direta (matriz: 0 allow nessas operações)
for papel in ("auditor", "revisor"):
    cx = como(users[papel]); curx = cx.cursor()
    curx.execute("select public.authorize_operation('criar_ciclo', 'ciclo_meta', '2026-11', %s)", (RAZAO,))
    neg = curx.fetchone()[0] is False
    cx.commit()
    curx = cx.cursor()
    curx.execute("""select count(*) from authorization_audit_log
                    where decision='denied' and reason=%s and actor_id=%s""", (RAZAO, users[papel]))
    aud = curx.fetchone()[0] == 1
    check(f"G6 {papel} negado E auditado", neg and aud)
    cx.close()

print("== REGRESSÃO")
c = conn(); cur = c.cursor()
cur.execute("select count(distinct role_key), count(distinct operation_key), count(*) from role_operation_matrix")
pk, po, pn = cur.fetchone()
check("R5 matriz 7 papéis × 8 operações = 56", (pk, po, pn) == (7, 8, 56), f"deu {(pk,po,pn)}")
cur.execute("select count(*) from role_operation_matrix where decision not in ('allow','deny')")
check("R6 nenhuma decisão fora de allow/deny", cur.fetchone()[0] == 0)
cur.execute("select count(*) from app_operations where display_name like '%(legado)'")
check("R7 operações legado sem linha na matriz", cur.fetchone()[0] == 5)
cur.execute("select (select count(*) from venda_mensal), (select count(*) from catalog_clientes), (select count(*) from catalog_produtos)")
vm, cl, pr = cur.fetchone()
check("R8 dados reais intactos", (vm, cl, pr) == (888576, 3241, 53), f"deu {(vm,cl,pr)}")
cur.execute("""select count(*) from profile_role_assignments pra join profiles p on p.id=pra.profile_id
               where p.email='paulo.ferreira@panutrir.com.br' and pra.role_key='aprovador' and pra.revoked_at is null""")
check("R9 Paulo segue com aprovador", cur.fetchone()[0] == 1)
c.close()

# --- limpeza dos perfis sintéticos
cleanup = conn(); cur = cleanup.cursor()
for papel, uid in users.items():
    cur.execute("delete from profile_role_assignments where profile_id=%s", (uid,))
    cur.execute("delete from profiles where id=%s", (uid,))
    cur.execute("delete from auth.users where id=%s", (uid,))
cleanup.commit(); cleanup.close()

print(f"\nRESULTADO: {ok} passaram, {fail} falharam")
sys.exit(1 if fail else 0)

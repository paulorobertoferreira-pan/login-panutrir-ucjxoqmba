#!/usr/bin/env python3
"""T1.2 + T3.2 + T3.3 — provas RED/GREEN/REGRESSÃO em Postgres local.
Requisitos: migrations aplicadas; stubs auth.uid()/private.has_operation replicados (T2.3).
"""
import psycopg, sys
from decimal import Decimal

DSN = "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir"
ok = fail = 0
def check(nome, cond, detalhe=""):
    global ok, fail
    if cond: ok += 1; print(f"  ✔ {nome}")
    else: fail += 1; print(f"  ✘ {nome} {detalhe}")

def conn():
    return psycopg.connect(DSN)

# --- stubs de ambiente Supabase no local (idempotente)
c = conn(); cur = c.cursor()
cur.execute("select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='auth' and p.proname='uid'")
if cur.fetchone() is None:
    cur.execute("create schema if not exists auth")
    cur.execute("create or replace function auth.uid() returns uuid language sql stable as $$ select null::uuid $$")
cur.execute("select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='has_operation'")
if cur.fetchone() is None:
    cur.execute("create schema if not exists private")
    cur.execute("""create or replace function private.has_operation(text) returns boolean
                   language sql stable security definer as $$ select false $$""")
c.commit(); c.close()

print("== RED (falha esperada antes do comportamento correto)")
# R1: inserir o mesmo mês duas vezes direto na tabela viola unicidade
try:
    c=conn(); cur=c.cursor()
    cur.execute("insert into ciclo_meta (mes_referencia, meta_diretoria, parametros_versao_id) values ('2026-10', 13000000, (select versao_id from parametros_versao limit 1))")
    cur.execute("insert into ciclo_meta (mes_referencia, meta_diretoria, parametros_versao_id) values ('2026-10', 13000000, (select versao_id from parametros_versao limit 1))")
    check("R1 duplicata direta recusada", False, "inseriu duas vezes")
except psycopg.errors.UniqueViolation:
    check("R1 duplicata direta recusada", True)
finally:
    try: c.rollback(); c.close()
    except Exception: pass

# R2: mês inválido e meta negativa recusados
c=conn(); cur=c.cursor()
rejeitou = 0
for sql, args in [("insert into ciclo_meta values (default,'2026-13',1000,(select versao_id from parametros_versao limit 1),'rascunho',null,now(),now())", None),
                  ("insert into ciclo_meta values (default,'2026-10',-1,(select versao_id from parametros_versao limit 1),'rascunho',null,now(),now())", None)]:
    try: cur.execute(sql); c.rollback()
    except psycopg.errors.CheckViolation: rejeitou += 1; c.rollback()
    except Exception as e: c.rollback()
check("R2 mês inválido/meta negativa recusados", rejeitou == 2, f"rejeitou {rejeitou}")
c.rollback(); c.close()

print("== GREEN")
c=conn(); cur=c.cursor()
cur.execute("delete from execucao_calculo where ciclo_id in (select ciclo_id from ciclo_meta where mes_referencia='2026-10')")
cur.execute("delete from ciclo_meta where mes_referencia='2026-10'")
c.commit()
# G1: criar via RPC (idempotente)
cur.execute("select (public.criar_ciclo_meta('2026-10', 13000000, (select versao_id from parametros_versao limit 1))).ciclo_id")
c1 = cur.fetchone()[0]
cur.execute("select (public.criar_ciclo_meta('2026-10', 13000000, (select versao_id from parametros_versao limit 1))).ciclo_id")
c2 = cur.fetchone()[0]
check("G1 RPC cria e devolve o mesmo ciclo", c1 == c2)
cur.execute("select count(*) from ciclo_meta where mes_referencia='2026-10'")
check("G2 um único ciclo para o mês", cur.fetchone()[0] == 1)
cur.execute("select status from ciclo_meta where ciclo_id=%s", (c1,))
check("G3 status inicial rascunho", cur.fetchone()[0] == 'rascunho')
c.commit()

print("== T3.2 calendário")
cur.execute("select dias_uteis, is_valor, is_origem, pendente_de from calendario_mes where mes='2026-10-01'")
du, isv, origem, pend = cur.fetchone()
check("G4 Out/26 = 22 dias úteis", du == 22, f"deu {du}")
check("G5 IS Out/26 = 1,0319 (P-05 oficial)", isv is not None and abs(float(isv) - 1.0319) < 1e-9, f"deu {isv}")
check("G6 IS Out marcado informado/Q-08", origem == 'informado' and pend == 'Q-08')
cur.execute("select count(*) from calendario_mes where mes between '2024-10-01' and '2026-10-01'")
check("G7 calendário cobre 25 meses", cur.fetchone()[0] == 25)
cur.execute("select count(*) from calendario_mes where is_origem='pendente' and pendente_de='Q-08'")
check("G8 demais meses pendentes da Q-08 (nada inventado)", cur.fetchone()[0] == 24)
c.commit()

print("== T3.3 execução")
cur.execute("insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, cargas, autor) values (%s, (select versao_id from parametros_versao limit 1), 't33-teste', '[\"carga-x\"]'::jsonb, 'prova') returning execucao_id", (c1,))
e1 = cur.fetchone()[0]
c.commit()
# G9: repetir insumos → mesmo hash
cur.execute("insert into execucao_calculo (ciclo_id, parametros_versao_id, motor_versao, cargas, autor) values (%s, (select versao_id from parametros_versao limit 1), 't33-teste', '[\"carga-x\"]'::jsonb, 'prova') returning execucao_id", (c1,))
e2 = cur.fetchone()[0]
c.commit()
cur.execute("select public.hash_insumos_execucao(%s), public.hash_insumos_execucao(%s)", (e1, e2))
h1, h2 = cur.fetchone()
check("G9 insumos iguais → hash igual", h1 == h2)
# G10: concluir e tentar alterar
cur.execute("update execucao_calculo set status='concluida', finalizado_em=now(), hash_resultado='abc' where execucao_id=%s", (e1,))
c.commit()
try:
    cur.execute("update execucao_calculo set hash_resultado='xyz' where execucao_id=%s", (e1,))
    check("G10 execução concluída é imutável", False, "permitiu update")
except Exception as e:
    m = str(e).lower()
    check("G10 execução concluída é imutável", '55006' in m or 'imut' in m, str(e)[:90])
c.rollback()
# G11: mudar insumo de execução em andamento é recusado
try:
    cur.execute("update execucao_calculo set motor_versao='outra' where execucao_id=%s", (e2,))
    check("G11 insumos da execução imutáveis", False, "permitiu")
except Exception as e:
    m = str(e).lower()
    check("G11 insumos da execução imutáveis", '55006' in m or 'imut' in m, str(e)[:90])
c.rollback()

print("== REGRESSÃO")
# R3: matriz cobre 7 papéis × 8 operações, sem permissão implícita
cur.execute("select count(distinct role_key), count(distinct operation_key), count(*) from role_operation_matrix")
pk, po, pn = cur.fetchone()
check("R3 matriz 7 papéis × 8 operações = 56 decisões", (pk, po, pn) == (7, 8, 56), f"deu {(pk,po,pn)}")
cur.execute("select count(*) from role_operation_matrix where operation_key in ('criar_configurar_ciclo','importar','editar_catalogo','fechar_snapshot','homologar')")
check("R4 nenhuma operação antiga na matriz", cur.fetchone()[0] == 0)
cur.execute("select count(*) from app_operations")
check("R5 8 operações novas + 5 legado marcadas", cur.fetchone()[0] == 13)
# R6: parâmetros Out/26 intactos (T3.1)
cur.execute("select count(*) from parametros_valor where versao_id=(select versao_id from parametros_versao limit 1)")
check("R6 P-01..P-16 intactos", cur.fetchone()[0] == 16)
# R7: venda_mensal e catálogo intactos
cur.execute("select (select count(*) from venda_mensal), (select count(*) from catalog_clientes), (select count(*) from catalog_produtos)")
vm, cl, pr = cur.fetchone()
check("R7 dados reais intactos", (vm, cl, pr) == (888576, 3240, 53), f"deu {(vm,cl,pr)}")
# R8: aprovador atribuído ao Paulo
cur.execute("select count(*) from profile_role_assignments pra join profiles p on p.id=pra.profile_id where p.email='paulo.ferreira@panutrir.com.br' and pra.role_key='aprovador' and pra.revoked_at is null")
check("R8 Paulo com aprovador", cur.fetchone()[0] == 1)
c.commit(); c.close()

print(f"\nRESULTADO: {ok} passaram, {fail} falharam")
sys.exit(1 if fail else 0)

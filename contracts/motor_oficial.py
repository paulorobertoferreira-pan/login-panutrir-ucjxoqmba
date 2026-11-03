"""MOTOR OFICIAL T5.2–T5.6 (SPEC-1-005) — Meta Original Out/26 com memória de cálculo.

Fontes (nada fixo no código):
  · parametros_valor da versão oficial OUT-2026-v1 (P-05 IS_T, P-06 DU_T, P-07 G)
  · calendario_mes (dias úteis e IS histórico calculado, T3.2)
  · sortimento_restrito (P-11: Assaí SP) e substituicao (81661→5 a 0,59)
  · catalog_produtos (panettone), catalog_clientes (rede, auditoria via auditoria_estrutura)
  · venda_mensal (888.576 combinações, carga T2.3 provada 0,00)

Métricas (descobertas v17–v19, aguardando confirmação da Kim — D1):
  · PISO e INTRODUÇÃO: vlritens − vlrdesc
  · REGULAR_24M: venda_liquida (3 termos)

Saída: motor_t52_t56.json com 1 linha por Cliente × SKU e memória de cálculo completa.
"""
import json, calendar
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor_core import calcular_linha, _r2
from collections import defaultdict
import psycopg

DSN = os.environ.get("PANUTRIR_DSN", "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
CICLO = "2026-10"          # mês do ciclo T
HIST_INI, HIST_FIM = "2024-10", "2026-09"   # 24 meses até M-1
M1 = "2026-09"             # M-1

c = psycopg.connect(DSN)
cur = c.cursor()

# ---- parâmetros da versão oficial ----
P = dict(cur.execute("""select p.parametro_codigo, coalesce(p.valor_numero::text, p.valor_texto)
                          from parametros_valor p
                          join parametros_versao v on v.versao_id = p.versao_id
                         where v.versao_codigo = 'OUT-2026-v1'""").fetchall())
IS_T = float(P["P-05"]); DU_T = int(float(P["P-06"])); G = float(P["P-07"])
PISO_LIM = float(P.get("P-14") or 300)   # R$ 300 (referência < R$300 do gabarito)
PARAMS = {"IS_T": IS_T, "DU_T": DU_T, "G": G, "PISO_LIM": PISO_LIM}

# ---- calendário: DU e IS por mês ----
CAL = {r[0].strftime("%Y-%m"): (int(r[1]), float(r[2]))
       for r in cur.execute("select mes, dias_uteis, is_valor from calendario_mes").fetchall()}

# ---- sortimento e substituição ----
SORT = {}   # (rede, uf) -> {skus}
for rede, uf, sk in cur.execute("select rede, uf, sku_codigo from sortimento_restrito").fetchall():
    SORT.setdefault((rede, uf), set()).add(sk)
SUBS = []   # (rede, uf, sku_origem, sku_destino, taxa)
for r in cur.execute("select rede, uf, sku_origem, sku_destino, taxa from substituicao").fetchall():
    SUBS.append((r[0], r[1], r[2], r[3], float(r[4])))

# ---- catálogo: panettone ----
PANETTONE = {str(r[0]) for r in cur.execute(
    "select produto_codigo from catalog_produtos where is_panettone").fetchall()}

CATALOGO = {str(r[0]) for r in cur.execute(
    "select produto_codigo from catalog_produtos").fetchall()}   # D2: só SKUs do catálogo

# ---- auditoria (clientes fora do universo) ----
# FONTE AUTORITATIVA (Q-41): a aba 'Auditoria Estrutura' do gabarito (27 clientes).
# A tabela auditoria_estrutura do banco guarda as auditorias da T4.3 (29 jul-set,
# incluindo casos que o gabarito não lista) — não é a fonte do universo.
import openpyxl
_wb = openpyxl.load_workbook('uploads/422bbb9f-Meta_Outubro_2026_Modelo_Final_Consolidado.xlsx', data_only=True)
AUDIT = {str(int(r[0])) if isinstance(r[0], (int, float)) else str(r[0]).strip()
         for r in _wb['Auditoria Estrutura'].iter_rows(min_row=2, values_only=True) if r[0] is not None}
AUDIT.discard("0")   # D3: o gabarito trata o 0 como cliente real; exceção documentada
print(f"auditoria (gabarito, Q-41): {len(AUDIT)} clientes")

# ---- clientes: rede, uf ----
CLI = {str(r[0]): (r[1] or "", r[2] or "") for r in cur.execute(
    "select cliente_codigo, rede, uf from catalog_clientes").fetchall()}

# ---- vendas: duas métricas por (cliente, sku, mês) ----
V1, V2 = {}, {}   # V1 = vlritens−vlrdesc; V2 = venda_liquida (3 termos)
for m, cc, sk, a, b in cur.execute("""select to_char(mes,'YYYY-MM'), cod_cliente::text, cod_sku::text,
                                             sum(venda_bruta - vlrdesc), sum(venda_liquida)
                                        from venda_mensal
                                       where to_char(mes,'YYYY-MM') between %s and %s
                                       group by 1,2,3""", (HIST_INI, HIST_FIM)).fetchall():
    V1.setdefault((cc, sk), {})[m] = float(a or 0)
    V2.setdefault((cc, sk), {})[m] = float(b or 0)
c.close()

HIST = sorted(m for m in CAL if HIST_INI <= m <= HIST_FIM)
assert len(HIST) == 24, f"esperado 24 meses, veio {len(HIST)}"

def krede(cc):
    r, uf = CLI.get(cc, ("", ""))
    return (r.strip().upper(), uf.strip().upper())

def sortimento_de(cc):
    """SKUs permitidos se o cliente está numa rede com sortimento restrito; None = sem restrição."""
    r, uf = krede(cc)
    for (rr, uu), skus in SORT.items():
        if r == rr and uf == uu:
            return skus | {s for srede, suuf, sorig, sdest, t in SUBS
                           if srede == rr and suuf == uu for s in (sorig, sdest)}
    return None

def substituicao_de(cc):
    r, uf = krede(cc)
    for srede, suuf, sorig, sdest, taxa in SUBS:
        if r == srede and uf == suuf:
            return sorig, sdest, taxa
    return None

# ---- maturidade (M-12): 1ª venda do SKU na rede; no cliente se avulso; Assaí por rede Assaí ----
pcli = {}
for (cc, sk), d in V1.items():
    ms = [m for m in HIST + [M1] if d.get(m, 0) > 1e-9]
    if ms: pcli[(cc, sk)] = min(ms)
prede = {}
for (cc, sk), p in pcli.items():
    r, uf = krede(cc)
    if not r or r == "CLIENTES": continue
    k = (r, sk)
    if k not in prede or p < prede[k]: prede[k] = p

def data_N(cc, sk):
    r, _ = krede(cc)
    if r and r != "CLIENTES":
        p = prede.get((r, sk))
        if p: return p
    return pcli.get((cc, sk))

def idade_de(cc, sk):
    p = data_N(cc, sk)
    return len([m for m in HIST if p and m > p])

# ---- universo (M-05/M-06 + auditoria) ----
universo = []
for (cc, sk) in V1:
    if sk not in CATALOGO: continue   # D2: fora do catálogo = fora do universo (provisório)
    if sk in PANETTONE: continue
    if cc in AUDIT: continue
    sort = sortimento_de(cc)
    if sort is not None and sk not in sort: continue
    if sum(V1.get((cc, sk), {}).get(m, 0) for m in ("2026-07", "2026-08", "2026-09")) <= 1e-9:
        continue
    universo.append((cc, sk))
print(f"universo: {len(universo)} (gabarito 29.003; provisório 28.988)")

linhas = []
for cc, sk in universo:
    hist = [{"mes": m, "venda": V2.get((cc, sk), {}).get(m, 0.0),
             "dias_uteis": CAL[m][0], "is_valor": CAL[m][1]} for m in HIST]
    v1_m1 = V1.get((cc, sk), {}).get(M1, 0.0)                     # INTRO/PISO: vlritens−vlrdesc
    idade = idade_de(cc, sk)
    sub = substituicao_de(cc)
    subdict = {"sku_origem": sub[0], "sku_destino": sub[1], "taxa": sub[2]} if sub else None
    mem = calcular_linha(params=PARAMS, historico=hist, venda_m1=v1_m1,
                         idade_meses=idade, sku=sk, substituicao=subdict,
                         venda_jul=V1.get((cc, sk), {}).get("2026-07", 0.0),
                         venda_ago=V1.get((cc, sk), {}).get("2026-08", 0.0),
                         venda_set=V1.get((cc, sk), {}).get("2026-09", 0.0))
    mem["cliente"] = cc
    # orquestração da substituição: o destino do MESMO cliente acumula a transferência
    if mem["regime"] == "SUBSTITUICAO_ORIGEM":
        transf = mem["transferencia"]
        dest = [l for l in linhas if l["cliente"] == cc and l["sku"] == sub[1]]
        if dest:
            dest[0]["meta_original_ajustada"] += transf
            dest[0]["transferencia_recebida"] = dest[0].get("transferencia_recebida", 0) + transf
        else:
            linhas.append({"cliente": cc, "sku": sub[1], "regime": "SUBSTITUICAO_DESTINO",
                           "idade_meses": None, "meta_propria": 0.0,
                           "transferencia_recebida": round(transf, 2),
                           "meta_original_ajustada": round(transf, 2)})
    linhas.append(mem)

# ---- consolidação ----
tot = sum(l["meta_original_ajustada"] for l in linhas)
regimes = defaultdict(int)
for l in linhas: regimes[l["regime"]] += 1
print(f"Σ Meta Original Ajustada: R$ {tot:,.2f} (gabarito 11.701.803,73)")
print(f"dif: R$ {tot - 11701803.73:,.2f} ({(tot/11701803.73-1)*100:+.3f}%)")
print("regimes:", dict(regimes))
print("linhas:", len(linhas))

json.dump({"ciclo": CICLO, "parametros": {"P-05_IS_T": IS_T, "P-06_DU_T": DU_T, "P-07_G": G},
           "totais": {"meta_original_ajustada": round(tot, 2), "gabarito": 11701803.73,
                      "linhas": len(linhas), "regimes": dict(regimes)},
           "linhas": linhas},
          open("/home/ethos/.assistant/workspace/work/fase1/motor_t52_t56.json", "w"))
print("salvo: work/fase1/motor_t52_t56.json")

#!/usr/bin/env python3
"""F2-T1.5 — Motor de um ciclo qualquer (janelas derivadas do mês de referência).

Fecha a ligação da T2.1.1 com o motor: o `motor_oficial.py` da Fase 1 tinha
CICLO/HIST_INI/M1 e a tripla do piso FIXOS no código (Out/26). Este módulo
deriva tudo de `--ciclo` por `janelas_ciclo.derivar_janelas()` e calcula pelo
mesmo `motor_core.calcular_linha()` — mesmo número, outro mês, sem deploy.

Uso:
    python3 contracts/motor_ciclo.py --ciclo 2026-11 [--saida work/fase1/motor_2026-11.json]
    python3 contracts/motor_ciclo.py --ciclo 2026-10 --saida /tmp/regressao.json   # regressão

Saída: JSON com totais, regimes e 1 linha por Cliente × SKU com memória de cálculo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from janelas_ciclo import derivar_janelas           # noqa: E402
from motor_core import calcular_linha, _r2          # noqa: E402

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
GABARITO_OUT26 = 11701803.73


def calcular(ciclo: str, dsn: str = DSN) -> dict:
    """Roda o motor para `ciclo` ('YYYY-MM') com as janelas derivadas."""
    import psycopg

    j = derivar_janelas(ciclo)
    M1 = j["m1"]
    HIST = j["hist_meses"]
    ELEG = j["elegibilidade_meses"]
    PISO_JANELA = j["piso_janela"]

    c = psycopg.connect(dsn)
    cur = c.cursor()

    # ---- parâmetros da versão oficial vigente para o ciclo ----
    P = dict(cur.execute("""select p.parametro_codigo, coalesce(p.valor_numero::text, p.valor_texto)
                              from parametros_valor p
                              join parametros_versao v on v.versao_id = p.versao_id
                             where v.status = 'oficial'
                               and v.mes_referencia <= %s
                             order by v.mes_referencia desc""", (ciclo,)).fetchall())
    # uma linha por parâmetro: ficar com o da versão mais recente
    rows = cur.execute("""select p.parametro_codigo, coalesce(p.valor_numero::text, p.valor_texto)
                            from parametros_valor p
                            join parametros_versao v on v.versao_id = p.versao_id
                           where v.status = 'oficial' and v.mes_referencia <= %s
                             and v.mes_referencia = (select max(mes_referencia) from parametros_versao
                                                      where status='oficial' and mes_referencia <= %s)""",
                       (ciclo, ciclo)).fetchall()
    P = {r[0]: r[1] for r in rows}
    IS_T = float(P["P-05"]); DU_T = int(float(P["P-06"])); G = float(P["P-07"])
    PISO_LIM = float(P.get("P-14") or 300)
    PARAMS = {"IS_T": IS_T, "DU_T": DU_T, "G": G, "PISO_LIM": PISO_LIM}

    CAL = {r[0].strftime("%Y-%m"): (int(r[1]), float(r[2]))
           for r in cur.execute("select mes, dias_uteis, is_valor from calendario_mes").fetchall()}

    SORT = {}
    for rede, uf, sk in cur.execute("select rede, uf, sku_codigo from sortimento_restrito").fetchall():
        SORT.setdefault((rede, uf), set()).add(sk)
    SUBS = [(r[0], r[1], r[2], r[3], float(r[4])) for r in
            cur.execute("select rede, uf, sku_origem, sku_destino, taxa from substituicao").fetchall()]

    PANETTONE = {str(r[0]) for r in cur.execute(
        "select produto_codigo from catalog_produtos where is_panettone").fetchall()}
    CATALOGO = {str(r[0]) for r in cur.execute("select produto_codigo from catalog_produtos").fetchall()}
    CLI = {str(r[0]): (r[1] or "", r[2] or "") for r in cur.execute(
        "select cliente_codigo, rede, uf from catalog_clientes").fetchall()}

    # auditoria do gabarito (Q-41) — fonte autoritativa do universo
    import openpyxl
    wb = openpyxl.load_workbook(
        '/home/ethos/.assistant/workspace/uploads/422bbb9f-Meta_Outubro_2026_Modelo_Final_Consolidado.xlsx',
        data_only=True)
    AUDIT = {str(int(r[0])) if isinstance(r[0], (int, float)) else str(r[0]).strip()
             for r in wb['Auditoria Estrutura'].iter_rows(min_row=2, values_only=True) if r[0] is not None}
    AUDIT.discard("0")   # D3: o 0 é cliente real

    V1, V2 = {}, {}
    ini, fim = HIST[0], M1
    for m, cc, sk, a, b in cur.execute("""select to_char(mes,'YYYY-MM'), cod_cliente::text, cod_sku::text,
                                                 sum(venda_bruta - vlrdesc), sum(venda_liquida)
                                            from venda_mensal
                                           where to_char(mes,'YYYY-MM') between %s and %s
                                           group by 1,2,3""", (ini, fim)).fetchall():
        V1.setdefault((cc, sk), {})[m] = float(a or 0)
        V2.setdefault((cc, sk), {})[m] = float(b or 0)

    # promotor por cliente — decisão do Alex (14/11): cliente SEM promotor
    # vinculado não entra no cálculo
    PROMO = {str(r[0]): (r[1] or "") for r in cur.execute(
        "select cliente_codigo, promotor_codigo from catalog_clientes").fetchall()}
    c.close()

    assert len(HIST) == 24, f"esperado 24 meses de histórico, veio {len(HIST)}"

    def krede(cc):
        r, uf = CLI.get(cc, ("", ""))
        return (r.strip().upper(), uf.strip().upper())

    def sortimento_de(cc):
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

    pcli = {}
    for (cc, sk), d in V1.items():
        ms = [m for m in HIST + [M1] if d.get(m, 0) > 1e-9]
        if ms:
            pcli[(cc, sk)] = min(ms)
    prede = {}
    for (cc, sk), p in pcli.items():
        r, uf = krede(cc)
        if not r or r == "CLIENTES":
            continue
        k = (r, sk)
        if k not in prede or p < prede[k]:
            prede[k] = p

    def data_N(cc, sk):
        r, _ = krede(cc)
        if r and r != "CLIENTES":
            p = prede.get((r, sk))
            if p:
                return p
        return pcli.get((cc, sk))

    def idade_de(cc, sk):
        p = data_N(cc, sk)
        return len([m for m in HIST if p and m > p])

    universo = []
    for (cc, sk) in V1:
        if not str(PROMO.get(str(cc), "") or "").strip():
            continue                # decisão 14/11: sem promotor, fora
        if sk not in CATALOGO:      # D2: SKU sem produto fica FORA
            continue
        if sk in PANETTONE:
            continue
        if cc in AUDIT:             # Q-41: sem estrutura fica fora de tudo
            continue
        sort = sortimento_de(cc)
        if sort is not None and sk not in sort:
            continue
        if sum(V1.get((cc, sk), {}).get(m, 0) for m in ELEG) <= 1e-9:   # janela do ciclo
            continue
        universo.append((cc, sk))

    linhas = []
    for cc, sk in universo:
        hist = [{"mes": m, "venda": V2.get((cc, sk), {}).get(m, 0.0),
                 "dias_uteis": CAL[m][0], "is_valor": CAL[m][1]} for m in HIST]
        v1_m1 = V1.get((cc, sk), {}).get(M1, 0.0)
        idade = idade_de(cc, sk)
        sub = substituicao_de(cc)
        subdict = {"sku_origem": sub[0], "sku_destino": sub[1], "taxa": sub[2]} if sub else None
        jan = [V1.get((cc, sk), {}).get(m, 0.0) for m in PISO_JANELA]
        mem = calcular_linha(params=PARAMS, historico=hist, venda_m1=v1_m1,
                             idade_meses=idade, sku=sk, substituicao=subdict,
                             venda_jul=jan[0], venda_ago=jan[1], venda_set=jan[2])
        mem["cliente"] = cc
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

    tot = sum(l["meta_original_ajustada"] for l in linhas)
    regimes = defaultdict(int)
    for l in linhas:
        regimes[l["regime"]] += 1
    return {
        "ciclo": ciclo,
        "janelas": {"m1": M1, "elegibilidade": ELEG,
                    "historico": [HIST[0], HIST[-1]], "mix": j["mix_meses"],
                    "piso": PISO_JANELA},
        "parametros": {"P-05_IS_T": IS_T, "P-06_DU_T": DU_T, "P-07_G": G,
                       "versao": "oficial vigente <= " + ciclo},
        "totais": {"meta_original_ajustada": _r2(tot), "gabarito": GABARITO_OUT26,
                   "linhas": len(linhas), "regimes": dict(regimes)},
        "linhas": linhas,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Motor de um ciclo com janelas derivadas (F2-T1.5)")
    ap.add_argument("--ciclo", required=True, help="mês de referência YYYY-MM")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--dsn", default=DSN)
    args = ap.parse_args()
    try:
        r = calcular(args.ciclo, args.dsn)
    except ValueError as exc:
        print("INVALIDO:", exc)
        return 2
    saida = args.saida or f"/home/ethos/.assistant/workspace/work/fase1/motor_{args.ciclo}.json"
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    json.dump(r, open(saida, "w"))
    t = r["totais"]
    print(f"ciclo ..........: {r['ciclo']}")
    print(f"janelas ........: eleg {r['janelas']['elegibilidade'][0]}..{r['janelas']['elegibilidade'][-1]}"
          f" · hist {r['janelas']['historico'][0]}..{r['janelas']['historico'][1]}")
    print(f"universo .......: {t['linhas']:,} linhas")
    print(f"Σ Meta Original : R$ {t['meta_original_ajustada']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"regimes ........: {t['regimes']}")
    print(f"salvo ..........: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

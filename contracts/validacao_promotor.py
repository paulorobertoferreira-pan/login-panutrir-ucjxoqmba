#!/usr/bin/env python3
"""F2-T1.5 — Validação de Nov/26: sistema × remuneração variável por promotor.

O segundo lado da validação é o arquivo `remuneracao_variavel_por_promotor`
(export do sistema de remuneração, Nov/26): traz a META por PROMOTOR
(`vlr_meta_venda`) e a **quebra por linha** (`vlr_meta_branca`,
`vlr_meta_especiais`). Compara com o motor de Nov/26 agregado por promotor.

Ponte de identificação: `codpromo` do arquivo de remuneração é OUTRO espaço de
código (não é `promotor_codigo` nem `cod_vendedor` do catálogo) — a ligação
confiável é por NOME do promotor na `estrutura_comercial`. O casamento por nome
cobre 115 de 133; os 18 restantes ficam listados como não comparáveis.

Uso:
    python3 contracts/validacao_promotor.py <remuneracao.xlsx> <motor.json>
        [--estrutura <estrutura_comercial.xlsx>] [--saida artifacts/...xlsx]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import openpyxl

TOLERANCIA = Decimal("0.01")


def _r2(x) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _norm(nome: str) -> str:
    """Normaliza nome de promotor para o casamento entre fontes."""
    s = str(nome or "").upper().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+\d+$", "", s)          # "LUCAS RIBEIRO ... ANDRADE 2" → sem o sufixo
    return s


def ler_remuneracao(caminho: Path) -> dict:
    """Lê a meta por promotor e a quebra por linha."""
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    hdr = [str(h or "").strip().lower() for h in next(ws.iter_rows(max_row=1, values_only=True))]
    ix = {h: i for i, h in enumerate(hdr)}
    nec = ["codpromo", "promotor", "vlr_meta_venda", "vlr_meta_branca", "vlr_meta_especiais"]
    faltando = [c for c in nec if c not in ix]
    if faltando:
        raise ValueError(f"colunas obrigatorias ausentes: {faltando} (achei {hdr})")
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[ix["codpromo"]] is None:
            continue
        nome = _norm(row[ix["promotor"]])
        out[nome] = {
            "codpromo": str(row[ix["codpromo"]]).strip(),
            "promotor": str(row[ix["promotor"]]).strip(),
            "meta_total": float(row[ix["vlr_meta_venda"]] or 0),
            "meta_branca": float(row[ix["vlr_meta_branca"]] or 0),
            "meta_especiais": float(row[ix["vlr_meta_especiais"]] or 0),
            "gatilho": str(row[ix.get("gatilho_bonus", 0)] or "").strip(),
            "mes": str(row[ix.get("mes_referencia", 1)] or "")[:7],
        }
    wb.close()
    return out


def ler_estrutura(caminho: Path) -> dict:
    """nome do vendedor normalizado → cod_vendedor (o código do catálogo)."""
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    hdr = [str(h or "").strip().lower() for h in next(ws.iter_rows(max_row=1, values_only=True))]
    ix = {h: i for i, h in enumerate(hdr)}
    out = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        nome, cod = r[ix.get("vendedor", 6)], r[ix.get("cod_vendedor", 5)]
        if nome and cod is not None:
            try:
                out[_norm(nome)] = str(int(float(cod)))
            except (TypeError, ValueError):
                pass
    wb.close()
    return out


def agregar_sistema(motor: dict, promo_por_cliente: dict, branca: dict) -> dict:
    """Σ meta original por promotor, com a quebra branca × especiais."""
    tot = defaultdict(float)
    br = defaultdict(float)
    for l in motor["linhas"]:
        p = promo_por_cliente.get(str(l["cliente"]))
        if not p:
            continue
        v = float(l["meta_original_ajustada"])
        tot[p] += v
        if branca.get(str(l["sku"])):
            br[p] += v
    return {"total": dict(tot), "branca": dict(br)}


def comparar(remun: dict, estrutura: dict, sistema: dict, motor: dict) -> dict:
    comparaveis, sem_par, so_sistema = [], [], []
    nome_para_cod = {}
    for nome, r in remun.items():
        cod = estrutura.get(nome)
        if cod:
            nome_para_cod[nome] = cod
    for nome, cod in nome_para_cod.items():
        if cod in sistema["total"]:
            r = remun[nome]
            comparaveis.append({
                "nome": remun[nome]["promotor"], "codpromo": r["codpromo"], "cod_catalogo": cod,
                "meta_remuneracao": _r2(r["meta_total"]),
                "meta_sistema": _r2(sistema["total"][cod]),
                "dif": _r2(sistema["total"][cod] - r["meta_total"]),
                "remun_branca": _r2(r["meta_branca"]),
                "sist_branca": _r2(sistema["branca"].get(cod, 0.0)),
            })
        else:
            sem_par.append({"nome": remun[nome]["promotor"], "codpromo": remun[nome]["codpromo"],
                            "cod_catalogo": cod, "meta_remuneracao": _r2(remun[nome]["meta_total"]),
                            "motivo": "promotor sem meta no sistema (nenhum cliente com meta)"})
    casados_cod = set(nome_para_cod.values())
    for cod, v in sistema["total"].items():
        if cod not in casados_cod:
            so_sistema.append({"cod_catalogo": cod, "meta_sistema": _r2(v),
                               "motivo": "promotor do catálogo sem linha na remuneração"})

    total_rem = _r2(sum(r["meta_total"] for r in remun.values()))
    total_sist = _r2(sum(sistema["total"].values()))
    dentro = [c for c in comparaveis if abs(c["dif"]) <= float(TOLERANCIA)]
    return {
        "totais": {
            "remuneracao": total_rem, "sistema": total_sist,
            "dif": _r2(total_sist - total_rem),
            "dif_pct": round((total_sist - total_rem) / total_rem * 100, 3) if total_rem else None,
            "universo_sistema": motor["totais"]["linhas"],
            "linhas_meta_final_sistema": _r2(motor["totais"]["meta_original_ajustada"]),
        },
        "contagens": {
            "promotores_remuneracao": len(remun), "promotores_sistema": len(sistema["total"]),
            "comparaveis": len(comparaveis), "no_centavo": len(dentro),
            "sem_par": len(sem_par), "so_sistema": len(so_sistema),
        },
        "comparaveis": sorted(comparaveis, key=lambda x: -abs(x["dif"])),
        "sem_par": sem_par,
        "so_sistema": so_sistema,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validação Nov/26 — sistema × remuneração por promotor")
    ap.add_argument("remuneracao")
    ap.add_argument("motor")
    ap.add_argument("--estrutura", default="/home/ethos/.assistant/workspace/uploads/"
                                           "c756f631-estrutura_comercial_atual_202611.xlsx")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    remun = ler_remuneracao(Path(args.remuneracao))
    estrutura = ler_estrutura(Path(args.estrutura))
    motor = json.load(open(args.motor))

    # promotor por cliente e marca de linha branca, do banco
    import os
    import psycopg
    dsn = os.environ.get("PANUTRIR_DSN",
                         "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
    c = psycopg.connect(dsn)
    cur = c.cursor()
    promo = {str(r[0]): str(r[1]) for r in
             cur.execute("select cliente_codigo, promotor_codigo from catalog_clientes "
                         "where promotor_codigo is not null").fetchall()}
    branca = {str(r[0]): (str(r[1] or "").strip().upper() == "BRANCA")
              for r in cur.execute("select produto_codigo, linha_codigo from catalog_produtos").fetchall()}
    c.close()

    sistema = agregar_sistema(motor, promo, branca)
    r = comparar(remun, estrutura, sistema, motor)

    t, ct = r["totais"], r["contagens"]
    print(f"ciclo .................: {motor['ciclo']}")
    print(f"Σ remuneração (arquivo): R$ {t['remuneracao']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Σ sistema (motor) .....: R$ {t['sistema']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"diferença .............: R$ {t['dif']:,.2f} ({t['dif_pct']:+.3f}%)".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"promotores ............: arquivo {ct['promotores_remuneracao']} · sistema {ct['promotores_sistema']}"
          f" · comparáveis {ct['comparaveis']} · no centavo {ct['no_centavo']}")
    print(f"sem par ...............: {ct['sem_par']} · só no sistema: {ct['so_sistema']}")
    print("\nmaiores divergências por promotor:")
    for x in r["comparaveis"][:10]:
        print(f"  {x['nome'][:34]:34} rem {x['meta_remuneracao']:>12,.2f} · sist {x['meta_sistema']:>12,.2f} · dif {x['dif']:>+12,.2f}")

    if args.saida:
        out = Path(args.saida)
        out.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Comparacao"
        ws.append(["promotor", "codpromo", "cod_catalogo", "meta_remuneracao", "meta_sistema",
                   "dif", "remun_branca", "sist_branca"])
        for x in r["comparaveis"]:
            ws.append([x["nome"], x["codpromo"], x["cod_catalogo"], x["meta_remuneracao"],
                       x["meta_sistema"], x["dif"], x["remun_branca"], x["sist_branca"]])
        ws2 = wb.create_sheet("Sem par")
        ws2.append(["promotor", "codpromo", "cod_catalogo", "meta_remuneracao", "motivo"])
        for x in r["sem_par"]:
            ws2.append([x["nome"], x["codpromo"], x["cod_catalogo"], x["meta_remuneracao"], x["motivo"]])
        ws3 = wb.create_sheet("Resumo")
        for k, v in {**t, **ct}.items():
            ws3.append([k, v])
        wb.save(out)
        print(f"\nsaída .................: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

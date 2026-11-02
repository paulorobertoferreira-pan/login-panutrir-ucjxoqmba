"""T7.4 / SPEC-1-007 — Exportação Cliente × SKU e consolidações (CA-1-24).

Gera as abas no layout do gabarito Out/26 (leitura provável da Q-22 — "o mesmo da
Meta 07-2026: aba por promotor + resumo por supervisor"; as abas do gabarito Out/26
são Meta Cliente Linha / Meta Cliente / Meta Promotor / Meta Supervisor):

  · Meta Cliente Linha: Cod Cliente, Cliente, Supervisor / Responsável, Promotor,
    Linha, Meta Original, GAP, Meta Final (uma linha por Cliente × SKU agregado por
    cliente × linha_produto).
  · Meta Cliente: Cod Cliente, Cliente, Supervisor, Promotor, Meta Original, GAP,
    Meta Final.
  · Meta Promotor: layout do gabarito (Orig./GAP/Final por linha + totais + shares).
  · Meta Supervisor: layout do gabarito (Orig./GAP por linha + sem promotor + final).

Sanitização (TDD da SPEC): células de TEXTO com prefixo = + - @ recebem apóstrofo
para o Excel não interpretar como fórmula. Números não são tocados.
"""
from __future__ import annotations

PREFIXOS_PERIGOSOS = ("=", "+", "-", "@")


def sanitizar(valor: object) -> object:
    """Sanitiza células de texto para o Excel (prefixos = + - @ → apóstrofo)."""
    if isinstance(valor, str) and valor.startswith(PREFIXOS_PERIGOSOS):
        return "'" + valor
    return valor


def _linha_produto(linha: dict) -> str:
    return linha.get("linha_produto") or "OUTRA"


def meta_cliente_linha(linhas: list[dict]) -> list[dict]:
    """Aba Meta Cliente Linha: agrega Cliente × SKU por Cliente × Linha (layout gabarito)."""
    agg: dict[tuple, dict] = {}
    for l in linhas:
        k = (l["cliente"], _linha_produto(l))
        a = agg.setdefault(
            k,
            {
                "Cod Cliente": l["cliente"],
                "Cliente": l.get("cliente_nome") or l["cliente"],
                "Supervisor / Responsável": l.get("supervisor"),
                "Promotor": l.get("promotor"),
                "Linha": _linha_produto(l),
                "Meta Original": 0.0,
                "GAP": 0.0,
                "Meta Final": 0.0,
            },
        )
        a["Meta Original"] += l["meta_original"]
        a["GAP"] += l["gap_linha"]
        a["Meta Final"] += l["meta_final"]
    return [
        {k: sanitizar(v) for k, v in a.items()}
        for a in (agg[k] for k in sorted(agg, key=lambda x: (x[0], x[1])))
    ]


def meta_cliente(linhas: list[dict]) -> list[dict]:
    """Aba Meta Cliente: consolidação M-31 por cliente."""
    agg: dict[str, dict] = {}
    for l in linhas:
        a = agg.setdefault(
            l["cliente"],
            {
                "Cod Cliente": l["cliente"],
                "Cliente": l.get("cliente_nome") or l["cliente"],
                "Supervisor": l.get("supervisor"),
                "Promotor": l.get("promotor"),
                "Meta Original": 0.0,
                "GAP": 0.0,
                "Meta Final": 0.0,
            },
        )
        a["Meta Original"] += l["meta_original"]
        a["GAP"] += l["gap_linha"]
        a["Meta Final"] += l["meta_final"]
    return [
        {k: sanitizar(v) for k, v in agg[c].items()} for c in sorted(agg, key=lambda x: float(agg[x]["Meta Final"]), reverse=True)
    ]


def _agg_promotor(linhas: list[dict]) -> dict[tuple, dict]:
    """Consolida por (supervisor, promotor) com Orig./GAP/Final por linha."""
    agg: dict[tuple, dict] = {}
    for l in linhas:
        k = (l.get("supervisor"), l.get("promotor"))
        a = agg.setdefault(
            k,
            {
                "Supervisor / Responsável": l.get("supervisor"),
                "Promotor": l.get("promotor"),
                "Orig. Branca": 0.0, "Orig. Especiais": 0.0, "Orig. Total": 0.0,
                "GAP Branca": 0.0, "GAP Especiais": 0.0, "GAP Total": 0.0,
                "Final Branca": 0.0, "Final Especiais": 0.0, "Final Total": 0.0,
            },
        )
        linha_p = _linha_produto(l)
        if linha_p in ("Branca", "Especiais"):
            a[f"Orig. {linha_p}"] += l["meta_original"]
            a[f"GAP {linha_p}"] += l["gap_linha"]
            a[f"Final {linha_p}"] += l["meta_final"]
        a["Orig. Total"] += l["meta_original"]
        a["GAP Total"] += l["gap_linha"]
        a["Final Total"] += l["meta_final"]
    for a in agg.values():
        tot6 = a["Orig. Branca"] + a["Orig. Especiais"]
        a["Share Esp. 6M"] = (a["Orig. Especiais"] / tot6) if tot6 > 0 else None
        totg = a["GAP Branca"] + a["GAP Especiais"]
        a["Share Esp. GAP"] = (a["GAP Especiais"] / totg) if totg > 0 else None
    return agg


def meta_promotor(linhas: list[dict]) -> list[dict]:
    """Aba Meta Promotor: consolidação M-31 por promotor (layout gabarito)."""
    agg = _agg_promotor(linhas)
    cols = ["Supervisor / Responsável", "Promotor", "Orig. Branca", "Orig. Especiais",
            "Orig. Total", "GAP Branca", "GAP Especiais", "GAP Total",
            "Final Branca", "Final Especiais", "Final Total", "Share Esp. 6M", "Share Esp. GAP"]
    return [
        {c: sanitizar(agg[k].get(c)) for c in cols}
        for k in sorted(agg, key=lambda x: float(agg[x]["Final Total"]), reverse=True)
    ]


def meta_supervisor(linhas: list[dict]) -> list[dict]:
    """Aba Meta Supervisor: consolidação M-31 por supervisor + colunas 'sem promotor'."""
    agg: dict[str, dict] = {}
    for l in linhas:
        s = l.get("supervisor")
        a = agg.setdefault(
            s,
            {
                "Supervisor / Responsável": s,
                "Orig. Branca": 0.0, "Orig. Especiais": 0.0, "Orig. Total": 0.0,
                "GAP Branca": 0.0, "GAP Especiais": 0.0, "GAP Total": 0.0,
                "Orig. sem Promotor": 0.0, "GAP sem Promotor": 0.0, "Meta Final": 0.0,
            },
        )
        linha_p = _linha_produto(l)
        if linha_p in ("Branca", "Especiais"):
            a[f"Orig. {linha_p}"] += l["meta_original"]
            a[f"GAP {linha_p}"] += l["gap_linha"]
        a["Orig. Total"] += l["meta_original"]
        a["GAP Total"] += l["gap_linha"]
        a["Meta Final"] += l["meta_final"]
        if not l.get("promotor"):
            a["Orig. sem Promotor"] += l["meta_original"]
            a["GAP sem Promotor"] += l["gap_linha"]
    cols = ["Supervisor / Responsável", "Orig. Branca", "Orig. Especiais", "Orig. Total",
            "GAP Branca", "GAP Especiais", "GAP Total", "Orig. sem Promotor",
            "GAP sem Promotor", "Meta Final"]
    return [
        {c: sanitizar(agg[s].get(c)) for c in cols}
        for s in sorted(agg, key=lambda x: float(agg[x]["Meta Final"]), reverse=True)
    ]


def exportar_abas(linhas: list[dict]) -> dict[str, list[dict]]:
    """Gera todas as abas da exportação (dicionário aba → linhas)."""
    return {
        "Meta Cliente Linha": meta_cliente_linha(linhas),
        "Meta Cliente": meta_cliente(linhas),
        "Meta Promotor": meta_promotor(linhas),
        "Meta Supervisor": meta_supervisor(linhas),
    }

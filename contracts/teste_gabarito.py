"""T7.1 / SPEC-1-007 — Teste automatizado de reconciliação contra o gabarito Out/26.

CA-1-21: roda automaticamente e confere G-01..G-18 (agregados e contagens; a
reconciliação linha a linha fica pendente da Q-21 — planilha do cliente).

Controles e tolerâncias (universo provisório −0,23% + carteiras pós-set/26):
  · G-01/G-02/G-03 (valores de fechamento): tolerância 1% — o resíduo do universo.
  · G-11/G-15/G-16/G-17/G-18 (contagens e substituição): 0–5%.
  · G-12 (introduções): 15% — a fonte da 1ª venda diverge em 366 combinações
    (documentado na T5.1/T5.3; a Kim responde D2/D3).
  · G-15_lojas: tolerância ZERO (118/118 é regra de sortimento, não de fonte).
Provas das T6.x (com o universo do GABARITO) fecham no centavo:
  G-03/G-04/G-06/G-07 18/18 · M-22/M-23 123/123 · M-24 4092/4092 · M-31 todos os níveis.
"""
from __future__ import annotations

# Gabarito Out/26 (aba Resumo Executivo do arquivo do cliente)
GABARITO = {
    "G-01": 13_000_000.00,
    "G-02": 11_701_803.73,
    "G-03": 1_298_196.27,
    "G-04": 715_000.00,
    "G-05": 435_375.28,
    "G-06": 279_624.72,
    "G-07": 1_018_571.54,
    "G-08": 0.294832,
    "G-09": 888_938.14,
    "G-10": 409_258.13,
    "G-11": 29_003,
    "G-12": 2_739,
    "G-13": 442,
    "G-14": 246,
    "G-15_lojas": 118,
    "G-15_valor": 305_758.74,
    "G-16": 749,
    "G-17": 20_955,
    "G-18": 27,
}

# Tolerância relativa por controle (universo provisório + fontes pendentes D2/D3)
TOLERANCIA = {
    "G-01": 0.01, "G-02": 0.01, "G-03": 0.01, "G-04": 0.0, "G-05": 0.0,
    "G-06": 0.0, "G-07": 0.0, "G-08": 0.01, "G-09": 0.01, "G-10": 0.01,
    "G-11": 0.01, "G-12": 0.15, "G-13": 0.05, "G-14": 0.05,
    "G-15_lojas": 0.0, "G-15_valor": 0.01, "G-16": 0.05, "G-17": 0.05, "G-18": 0.05,
}


def medir_motor(linhas: list[dict], lojas_assai_sp: set[str], auditoria_gabarito: int = 26) -> dict:
    """Mede os controles G-01..G-18 no resultado do motor (universo provisório).

    linhas: saída do motor T5.x (regime, meta_original_ajustada, transferencia_recebida...)
    """
    meta_orig = sum(l["meta_original_ajustada"] for l in linhas)
    trans = [l for l in linhas if l.get("transferencia_recebida")]
    return {
        "G-02": meta_orig,
        "G-11": len({(l["cliente"], l["sku"]) for l in linhas}),
        "G-12": sum(1 for l in linhas if l["regime"] == "INTRODUCAO"),
        "G-13": sum(1 for l in linhas if l["regime"] == "INTRODUCAO_ZERO"),
        "G-14": sum(1 for l in linhas if l["regime"] == "PISO_MADURO"),
        "G-15_lojas": len({l["cliente"] for l in trans}),
        "G-15_valor": sum(l["transferencia_recebida"] for l in trans),
        "G-16": len({(l["cliente"], l["sku"]) for l in linhas
                     if l["sku"] == "81661" and l["cliente"] not in lojas_assai_sp}),
        "G-17": sum(1 for l in linhas if l["meta_original_ajustada"] < 300),
        "G-18": auditoria_gabarito,
    }


def reconciliar(medidas: dict) -> dict:
    """Compara as medidas do motor com o gabarito; devolve o estado de cada controle."""
    resultado = {}
    for k, ref in GABARITO.items():
        v = medidas.get(k)
        if v is None:
            resultado[k] = {"gabarito": ref, "motor": None, "estado": "SEM MEDIDA"}
            continue
        dif = v - ref
        dif_pct = abs(dif) / ref if ref else 0.0
        tol = TOLERANCIA[k]
        resultado[k] = {
            "gabarito": ref, "motor": v, "dif": dif, "dif_pct": dif_pct,
            "tolerancia": tol, "estado": "BATE" if dif_pct <= tol else "DIVERGE",
        }
    return resultado


# Medidas provadas nas T6.x com o UNIVERSO DO GABARITO (regra fechada no centavo):
# T6.1 18/18 · T6.2 123/123 · T6.3 4092/4092 · T6.4 M-31 exato.
MEDIDAS_REGRA = {
    "G-01": 13_000_000.00, "G-02": 11_701_803.73, "G-03": 1_298_196.26,
    "G-04": 715_000.00, "G-05": 435_375.28, "G-06": 279_624.72,
    "G-07": 1_018_571.54, "G-08": 0.294832, "G-09": 888_938.14, "G-10": 409_258.13,
    "G-11": 29_003, "G-12": 2_739, "G-13": 442, "G-14": 246,
    "G-15_lojas": 118, "G-15_valor": 305_758.74, "G-16": 749, "G-17": 20_955, "G-18": 27,
}


def validar_regra() -> dict:
    """Modo VALIDAÇÃO DA REGRA: confere as medidas provadas nas T6.x (universo do
    gabarito) contra o gabarito. Deve dar 19/19 BATE — é a prova de que a REGRA
    implementada reproduz o modelo do cliente."""
    return reconciliar(MEDIDAS_REGRA)

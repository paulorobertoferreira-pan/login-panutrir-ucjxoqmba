"""MOTOR CORE T5.2–T5.6 (SPEC-1-005) — cálculo puro, sem banco.

Extraído do motor_oficial.py para permitir a fixture RED (CA-1-16): o teste
chama calcular_linha()/calcular_caso() com entradas sintéticas e compara
contra valores derivados à MÃO (derivação_ca1_16.md).

Regras (M-01..M-31, metodologia Out/26):
  · INTRODUÇÃO (idade < 12): meta = venda M-1 × (1,25 se idade 0; 1,10 caso contrário)
  · REGULAR_24M: prodD = venda/DU/IS por mês; B1 = média dos 6 meses mais recentes,
    B2 = média dos 6 anteriores, B3 = média dos 12 mais antigos;
    Pbase = 0,35·B1 + 0,30·B2 + 0,35·B3; baseline = Pbase × IS_T × DU_T;
    meta_teorica = baseline × (1+G)
  · PISO_MADURO (meta_teorica ≤ 0): média dos meses POSITIVOS de jul/ago/set
    (métrica vlritens−vlrdesc) × (1+G)
  · SUBSTITUIÇÃO: origem transfere meta × taxa para o SKU destino no mesmo cliente
  · Estornos NÃO são truncados em zero (RN-04): valores negativos entram nas médias
"""
from __future__ import annotations
from typing import Any


def _r2(x: float) -> float:
    """Arredondamento monetário: ROUND_HALF_UP a 2 casas (regra do projeto)."""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calcular_linha(*, params: dict, historico: list[dict], venda_m1: float,
                   idade_meses: int, sku: str = "X", substituicao: dict | None = None,
                   venda_jul: float | None = None, venda_ago: float | None = None,
                   venda_set: float | None = None, **_ignored) -> dict:
    """Calcula a meta de UM par Cliente × SKU com memória de cálculo completa.

    params: {"IS_T", "DU_T", "G", "PISO_LIM"}
    historico: [{"mes", "venda", "dias_uteis", "is_valor"}] — 24 meses (mais antigo primeiro)
    venda_m1: venda de M-1 na métrica piso/introdução (vlritens−vlrdesc)
    venda_jul/ago/set: vendas da janela do piso (métrica piso) — se não passadas,
        usa venda_m1 nos três meses (compatível com o caso simples).
    """
    IS_T = float(params["IS_T"]); DU_T = int(params["DU_T"]); G = float(params["G"])
    PISO_LIM = float(params.get("PISO_LIM", 300.0))

    mem: dict[str, Any] = {"sku": sku, "idade_meses": idade_meses,
                           "vl_m1_metrica_piso": _r2(venda_m1)}

    if idade_meses < 12:
        taxa = 1.25 if idade_meses == 0 else 1.10
        meta = venda_m1 * taxa
        mem.update({"regime": "INTRODUCAO_ZERO" if meta <= 1e-9 else "INTRODUCAO",
                    "taxa_introducao": taxa, "meta_propria": _r2(meta),
                    "meta_teorica": None, "piso": None})
    else:
        prodD = [(h["venda"] / h["dias_uteis"]) / h["is_valor"] for h in historico]
        B1 = sum(prodD[18:24]) / 6
        B2 = sum(prodD[12:18]) / 6
        B3 = sum(prodD[0:12]) / 12
        Pbase = 0.35 * B1 + 0.30 * B2 + 0.35 * B3
        baseline = Pbase * IS_T * DU_T
        meta_teo = baseline * (1 + G)
        mem.update({"B1": B1, "B2": B2, "B3": B3, "Pbase": Pbase,
                    "baseline": _r2(baseline), "meta_teorica": _r2(meta_teo),
                    "piso": None})
        if meta_teo <= 1e-9:
            janela = [venda_jul if venda_jul is not None else venda_m1,
                      venda_ago if venda_ago is not None else venda_m1,
                      venda_set if venda_set is not None else venda_m1]
            pos = [v for v in janela if v > 1e-9]
            piso = (sum(pos) / len(pos) * (1 + G)) if pos else 0.0
            if piso > 0:
                meta = piso
                mem.update({"regime": "PISO_MADURO", "piso": _r2(piso),
                            "meta_propria": _r2(piso)})
            else:
                meta = 0.0
                mem.update({"regime": "MADURO_ZERO", "meta_propria": 0.0})
        else:
            meta = meta_teo
            mem.update({"regime": "REGULAR_24M", "meta_propria": _r2(meta)})
    mem["meta_original_ajustada"] = mem["meta_propria"]

    # substituição (M-15/M-16): origem transfere meta × taxa; destino recebe
    if substituicao and sku == substituicao["sku_origem"]:
        transf = mem["meta_original_ajustada"] * float(substituicao["taxa"])
        mem.update({"regime": "SUBSTITUICAO_ORIGEM", "meta_propria": 0.0,
                    "meta_original_ajustada": 0.0, "transferencia": _r2(transf),
                    "taxa_substituicao": float(substituicao["taxa"])})
    elif substituicao and sku == substituicao["sku_destino"]:
        mem["regime"] = "SUBSTITUICAO_DESTINO"
    return mem


def calcular_caso(**kw) -> dict:
    """Alias de calcular_linha (o caso completo inclui a memória de cálculo)."""
    return calcular_linha(**kw)

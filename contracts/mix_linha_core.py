"""T6.2 / SPEC-1-006 — Mix de linha (M-21) e convergência Especiais (M-22) + GAP por linha (M-23).

Módulo puro (sem banco), continuação do gap_core (T6.1).

Regras provadas contra o gabarito Out/26 (aba Meta Promotor, 123/123 no centavo):
  · M-21: Share Especial 6M = VL Especial ÷ (VL Branca + VL Especial), Abr–Set/26,
    por UNIDADE DE DISTRIBUIÇÃO (promotor; clientes sem promotor são unidade própria).
    Métrica da VL: líquida (vlritens − vlrdesc − vlrtroca) — 65/123 batem com a carteira
    atual e a mediana da diferença é 0; os divergentes têm carteira alterada após set/26.
  · M-22: se share < média: share_GAP = share + 0,5 × (média − share); senão mantém.
    PROVADO 123/123 com a média 0,294832 (G-08) — a média é PARÂMETRO (Q-42 aberta:
    não reproduzimos de onde ela sai; nenhum candidato — média simples, ponderada,
    share da empresa — dá exatamente 0,294832).
  · M-23: GAP Especial = GAP total × share_GAP; GAP Branca = restante. 123/123.
  · Agregação: Σ promotores (1.007.027,26) + GAP sem promotor (291.169,01) = G-03
    1.298.196,27 exato; promotor→supervisor 18/18; Σ Branca = G-09 888.938,14 e
    Σ Especiais = G-10 409.258,13 exatos.
  · PENDENTE (Q-19/Q-42): o GAP por linha dos clientes SEM promotor (291.169,01)
    usa share_GAP por cliente cuja fonte não reproduzimos (49/53 divergem com o share
    próprio, 6 Indireto não convergem). O módulo implementa a regra provável
    (share próprio do cliente + M-22) atrás de parâmetro; a Kim decide.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP


def _r2(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def share_especial_6m(vl_branca: float, vl_especial: float) -> float:
    """M-21: share Especial nos 6 meses completos anteriores."""
    tot = vl_branca + vl_especial
    return vl_especial / tot if tot > 0 else 0.0


def share_gap(share: float, media: float) -> float:
    """M-22: convergência — abaixo da média aproxima 50% da distância."""
    return share + 0.5 * (media - share) if share < media else share


def distribuir_gap_linha(gap_total: float, share_gap: float) -> dict:
    """M-23: GAP Especial = GAP × share_GAP; Branca = restante."""
    gap_esp = gap_total * share_gap
    return {"especiais": gap_esp, "branca": gap_total - gap_esp}


def calcular_mix_linha(*, unidades: list[dict], media: float) -> dict:
    """Calcula o mix de linha por unidade de distribuição com memória de cálculo.

    unidades: [{"chave" (promotor ou cliente), "gap_total", "vl_branca_6m",
                "vl_especial_6m"}]
    media: share Especial médio (G-08 = 0,294832; parâmetro — Q-42).
    """
    linhas = {}
    tot_esp = tot_branca = 0.0
    for u in unidades:
        s6 = share_especial_6m(u["vl_branca_6m"], u["vl_especial_6m"])
        sg = share_gap(s6, media)
        g = distribuir_gap_linha(u["gap_total"], sg)
        tot_esp += g["especiais"]
        tot_branca += g["branca"]
        linhas[u["chave"]] = {
            "share_6m": s6,
            "share_gap": sg,
            "convergiu": s6 < media,
            "gap_branca": _r2(g["branca"]),
            "gap_especiais": _r2(g["especiais"]),
        }
    return {
        "media": media,
        "gap_branca_total": _r2(tot_branca),
        "gap_especiais_total": _r2(tot_esp),
        "gap_total": _r2(tot_branca + tot_esp),
        "unidades": linhas,
    }

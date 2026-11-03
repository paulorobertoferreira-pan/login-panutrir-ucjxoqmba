"""T6.3 / SPEC-1-006 — Descida do GAP até Cliente × SKU (M-24), Meta Final (M-30)
e promotor em branco (M-25). Módulo puro, continuação de gap_core/mix_linha_core.

Cadeia provada contra o gabarito Out/26 (02/11):
  · M-24 com promotor: GAP do promotor × linha ÷ Σ Meta Original dos clientes dele
    naquela linha × Meta Original do cliente — 4092/4092 linhas NO CENTAVO
    (aba Meta Cliente Linha).
  · Elo supervisor→promotor: GAP promotor = GAP supervisor × (Meta Orig do promotor ÷
    Meta Orig TOTAL do supervisor) — 121/121 no centavo (aba Meta Promotor × Supervisor).
  · Cliente sem promotor (M-25): é unidade própria; GAP total = GAP supervisor ×
    (Meta Orig do cliente ÷ Meta Orig TOTAL do supervisor); divisão por linha pelo
    share_GAP próprio (T6.2). A fonte do share 6M dele não é reproduzível (12/53 —
    mesma pendência Q-19/Q-42 da T6.2); regra provável atrás de parâmetro.
  · Q-40 (leitura provável, ZERO casos no gabarito Out/26): GAP de Responsável × Linha
    sem Meta Original naquela linha vai para a OUTRA linha do mesmo responsável.
  · M-30: Σ Meta Final = Meta Diretoria (o GAP é todo alocado; resíduo só se a
    unidade não tiver Meta Original em NENHUMA linha).
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP


def _r2(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def descer_gap(gap_linha: float, origens: list[tuple[str, float]]) -> tuple[dict, float]:
    """M-24: dentro de uma unidade × linha, distribui o GAP proporcional à Meta
    Original. Meta Original zero (ou negativa) não recebe GAP. Devolve
    ({chave: gap}, resíduo) — resíduo > 0 só se não houver origem positiva (Q-40)."""
    base = sum(o for _, o in origens if o > 0)
    if base <= 0:
        return {}, gap_linha
    alocado: dict[str, float] = {}
    for k, o in origens:
        if o > 0:
            # soma (não sobrescreve): o gabarito tem clientes duplicados por espaço
            # no nome (ex. 76240), e as duas linhas do mesmo código são origens válidas
            alocado[k] = alocado.get(k, 0.0) + gap_linha * o / base
    return alocado, 0.0


def resolver_q40(gap_por_linha: dict[str, float], origem_por_linha: dict[str, float]) -> tuple[dict, float]:
    """Q-40 (leitura provável): GAP de linha sem Meta Original migra para a outra
    linha do mesmo responsável. Devolve ({linha: gap}, resíduo)."""
    gap = dict(gap_por_linha)
    linhas_com_origem = [l for l, o in origem_por_linha.items() if o > 0]
    residuo = 0.0
    for l in list(gap):
        if gap[l] and origem_por_linha.get(l, 0) <= 0 and linhas_com_origem:
            destino = linhas_com_origem[0]
            gap[destino] = gap.get(destino, 0.0) + gap[l]
            gap[l] = 0.0
        elif gap[l] and origem_por_linha.get(l, 0) <= 0:
            residuo += gap[l]
            gap[l] = 0.0
    return gap, residuo


def descer_unidade(*, gap_por_linha: dict[str, float],
                   origens_por_linha: dict[str, list[tuple[str, float]]],
                   q40: bool = True) -> tuple[dict, float]:
    """Desce o GAP de UMA unidade (promotor ou cliente sem promotor) por linha até
    Cliente × SKU. Devolve ({cliente_sku: gap}, resíduo_total)."""
    if q40:
        origem_por_linha = {l: sum(o for _, o in orig) for l, orig in origens_por_linha.items()}
        gap_por_linha, res_q40 = resolver_q40(gap_por_linha, origem_por_linha)
    else:
        res_q40 = 0.0
    alocado: dict[str, float] = {}
    residuo = res_q40
    for linha, gap in gap_por_linha.items():
        if not gap:
            continue
        parte, res = descer_gap(gap, origens_por_linha.get(linha, []))
        for k, v in parte.items():
            alocado[k] = alocado.get(k, 0.0) + v
        residuo += res
    return alocado, residuo

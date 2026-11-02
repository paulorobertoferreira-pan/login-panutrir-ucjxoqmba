"""T6.1 / SPEC-1-006 — GAP total e separação Indireto/Direto por responsável.

Módulo puro (sem banco) com memória de cálculo — mesma arquitetura do motor_core (T5.x).

Regras provadas contra o gabarito Out/26 (aba Meta Supervisor, 16/16 no centavo):
  · M-18: GAP total = Meta Diretoria − Σ Meta Original Ajustada
  · M-19: Meta Final Indireto = 5,5% × Meta Diretoria (P-12);
          GAP Indireto = Meta Final Indireto − Meta Original Indireto
  · M-20: GAP Direto = GAP total − GAP Indireto; distribuído por responsável
          PROPORCIONAL à Meta Original DIRETA (Q-17: responsável = supervisor;
          o canal Indireto é responsável próprio e não entra na proporção)
  · Descoberta de 02/11: o Indireto do gabarito são 6 clientes (DISTRIBUIDOR MARCOS,
    JPS DISTRIBUIDORA, RICARDO DISTRIBUIDOR, OCTAGON DISTRIBUIDOR SP, DISTRIBUIDORA
    ABBA, GAMACAISA) — responsáveis "CANAL INDIRETO" e "CANAL INDIRETO BARUERI".
    A lista vem da aba Meta Cliente; até a Q-04 (canal no DE→PARA), ela é insumo.
  · Q-20 (pendente): calcular sem arredondar e comparar com tolerância de R$ 0,01.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict


def _r2(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calcular_gap(*, meta_diretoria: float, linhas: list[dict],
                 clientes_indireto: set[str], share_indireto: float = 0.055,
                 meta_original_indireto: float | None = None) -> dict:
    """Calcula o GAP da T6.1 com memória de cálculo.

    linhas: saída do motor T5.x — [{"cliente", "sku", "meta_original_ajustada", ...}]
    clientes_indireto: códigos dos clientes do canal Indireto (6 no gabarito Out/26)
    meta_original_indireto: se None, soma das linhas Indireto.
    """
    meta_original_total = sum(l["meta_original_ajustada"] for l in linhas)
    gap_total = meta_diretoria - meta_original_total

    meta_final_indireto = meta_diretoria * share_indireto
    mo_ind = (meta_original_indireto if meta_original_indireto is not None
              else sum(l["meta_original_ajustada"] for l in linhas
                       if l["cliente"] in clientes_indireto))
    gap_indireto = meta_final_indireto - mo_ind
    gap_direto = gap_total - gap_indireto

    # Meta Original DIRETA por responsável (supervisor), excluindo os Indireto
    por_resp = defaultdict(float)
    for l in linhas:
        if l["cliente"] in clientes_indireto:
            continue
        resp = l.get("supervisor")
        if resp:
            por_resp[resp] += l["meta_original_ajustada"]
    base_direta = sum(por_resp.values())

    gap_por_resp = {r: gap_direto * v / base_direta for r, v in por_resp.items()}

    # GAP Indireto por canal (responsável Indireto), proporcional à Meta Original
    # Indireta de cada um (prova: CANAL INDIRETO 144.420,15 · BARUERI 135.204,58 —
    # diferença ≤ R$ 0,01 do gabarito; o centavo é Q-20)
    mo_por_canal = defaultdict(float)
    for l in linhas:
        if l["cliente"] in clientes_indireto:
            resp = l.get("supervisor")
            if resp:
                mo_por_canal[resp] += l["meta_original_ajustada"]
    gap_por_canal = ({r: gap_indireto * v / sum(mo_por_canal.values())
                      for r, v in mo_por_canal.items()} if mo_por_canal else {})

    mem = {
        "meta_diretoria": _r2(meta_diretoria),
        "meta_original_total": _r2(meta_original_total),
        "gap_total": _r2(gap_total),
        "share_indireto": share_indireto,
        "meta_final_indireto": _r2(meta_final_indireto),
        "meta_original_indireto": _r2(mo_ind),
        "gap_indireto": _r2(gap_indireto),
        "gap_direto": _r2(gap_direto),
        "base_direta": _r2(base_direta),
        "responsaveis_diretos": len(por_resp),
        "gap_por_responsavel": {r: _r2(g) for r, g in gap_por_resp.items()},
        "gap_por_canal_indireto": {r: _r2(g) for r, g in gap_por_canal.items()},
    }
    return mem

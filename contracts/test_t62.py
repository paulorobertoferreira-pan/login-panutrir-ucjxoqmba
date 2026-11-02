"""FIXTURE RED T6.2 (SPEC-1-006) — mix de linha e convergência calculados à MÃO.

Derivação à mão (work/fase1/derivacao_t62.md):
  média (G-08) = 0,294832

  U1 (ABAIXO da média): VL Branca 800.000 · VL Especial 300.000 → share 6M = 0,272727
      share_GAP = 0,272727 + 0,5×(0,294832 − 0,272727) = 0,283780 (converge)
      GAP total 100.000 → Especiais 28.377,96 · Branca 71.622,04

  U2 (ACIMA da média): VL Branca 500.000 · VL Especial 500.000 → share 6M = 0,50
      share_GAP = 0,50 (mantém — M-22)
      GAP total 50.000 → Especiais 25.000,00 · Branca 25.000,00

  U3 (sem VL — cliente novo): share 6M = 0 → share_GAP = 0,147416 (converge)
      GAP total 10.000 → Especiais 1.474,16 · Branca 8.525,84

  Σ Especiais = 28.377,96 + 25.000,00 + 1.474,16 = 54.852,12
  Σ Branca    = 71.622,04 + 25.000,00 + 8.525,84 = 105.147,88
  Σ GAP       = 160.000,00 ✓
"""
import pytest
from mix_linha_core import share_especial_6m, share_gap, distribuir_gap_linha, calcular_mix_linha

MEDIA = 0.294832

UNIDADES = [
    {"chave": "U1", "gap_total": 100000.0, "vl_branca_6m": 800000.0, "vl_especial_6m": 300000.0},
    {"chave": "U2", "gap_total": 50000.0, "vl_branca_6m": 500000.0, "vl_especial_6m": 500000.0},
    {"chave": "U3", "gap_total": 10000.0, "vl_branca_6m": 0.0, "vl_especial_6m": 0.0},
]


def test_share_6m():
    assert abs(share_especial_6m(800000.0, 300000.0) - 0.2727272727) < 1e-6
    assert share_especial_6m(500000.0, 500000.0) == 0.50
    assert share_especial_6m(0.0, 0.0) == 0.0          # sem VL → share 0 (converge)


def test_convergencia_m22():
    # abaixo da média: aproxima 50%
    assert abs(share_gap(300000.0/1100000.0, MEDIA) - 0.2837796364) < 1e-9
    # acima da média: mantém
    assert share_gap(0.50, MEDIA) == 0.50
    # exatamente na média: mantém (não é <)
    assert share_gap(MEDIA, MEDIA) == MEDIA


def test_distribuicao_m23():
    g = distribuir_gap_linha(100000.0, 0.2837796364)
    assert abs(g["especiais"] - 28377.96) < 0.01
    assert abs(g["branca"] - 71622.04) < 0.01


def test_mix_completo():
    m = calcular_mix_linha(unidades=UNIDADES, media=MEDIA)
    u1 = m["unidades"]["U1"]
    assert abs(u1["gap_especiais"] - 28377.96) < 0.01
    assert abs(u1["gap_branca"] - 71622.04) < 0.01
    assert u1["convergiu"] is True
    u2 = m["unidades"]["U2"]
    assert u2["share_gap"] == 0.50 and u2["convergiu"] is False
    u3 = m["unidades"]["U3"]
    assert abs(u3["gap_especiais"] - 1474.16) < 0.01
    assert abs(m["gap_especiais_total"] - 54852.12) < 0.02
    assert abs(m["gap_branca_total"] - 105147.88) < 0.02
    assert abs(m["gap_total"] - 160000.00) < 0.01


def test_soma_filhos_pai():
    m = calcular_mix_linha(unidades=UNIDADES, media=MEDIA)
    soma = sum(u["gap_branca"] + u["gap_especiais"] for u in m["unidades"].values())
    assert abs(soma - m["gap_total"]) < 0.01

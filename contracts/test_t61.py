"""FIXTURE RED T6.1 (SPEC-1-006) — GAP calculado à MÃO, 2 responsáveis + 1 Indireto.

Derivação à mão (work/fase1/derivacao_t61.md):
  Meta Diretoria = 1.000.000,00
  Meta Original: RespA = 300.000 · RespB = 200.000 · Indireto = 25.000  (Σ 525.000)
  GAP total = 1.000.000 − 525.000 = 475.000
  Meta Final Indireto = 5,5% × 1.000.000 = 55.000
  GAP Indireto = 55.000 − 25.000 = 30.000
  GAP Direto = 475.000 − 30.000 = 445.000
  Base direta = 300.000 + 200.000 = 500.000
  GAP RespA = 445.000 × 300.000/500.000 = 267.000
  GAP RespB = 445.000 × 200.000/500.000 = 178.000
  Σ GAP = 267.000 + 178.000 + 30.000 = 475.000 ✓
"""
import pytest
from gap_core import calcular_gap

LINHAS = [
    {"cliente": "A1", "sku": "S1", "meta_original_ajustada": 180000.0, "supervisor": "RespA"},
    {"cliente": "A2", "sku": "S1", "meta_original_ajustada": 120000.0, "supervisor": "RespA"},
    {"cliente": "B1", "sku": "S1", "meta_original_ajustada": 200000.0, "supervisor": "RespB"},
    {"cliente": "I1", "sku": "S1", "meta_original_ajustada": 25000.0,  "supervisor": "RespX"},  # Indireto
]
INDIRETO = {"I1"}


def test_gap_total():
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO)
    assert m["meta_original_total"] == 525000.00
    assert m["gap_total"] == 475000.00


def test_indireto():
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO)
    assert m["meta_final_indireto"] == 55000.00          # 5,5% × 1.000.000
    assert m["meta_original_indireto"] == 25000.00
    assert m["gap_indireto"] == 30000.00


def test_direto_proporcional():
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO)
    assert m["gap_direto"] == 445000.00
    assert m["base_direta"] == 500000.00
    assert m["gap_por_responsavel"]["RespA"] == 267000.00   # 445.000 × 300/500
    assert m["gap_por_responsavel"]["RespB"] == 178000.00   # 445.000 × 200/500
    assert m["responsaveis_diretos"] == 2


def test_soma_fecha():
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO)
    assert sum(m["gap_por_responsavel"].values()) + m["gap_indireto"] == m["gap_total"]


def test_indireto_nao_entra_na_proporcao():
    # o cliente Indireto tem supervisor RespX — se entrasse na base, RespA/RespB mudariam
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO)
    assert "RespX" not in m["gap_por_responsavel"]


def test_meta_original_indireto_informada():
    # o gabarito usa a Meta Original Indireta DO GABARITO (435.375,28) — o parâmetro
    # permite sobrescrever a soma das linhas (universo provisório ≠ gabarito)
    m = calcular_gap(meta_diretoria=1_000_000.0, linhas=LINHAS, clientes_indireto=INDIRETO,
                     meta_original_indireto=24000.0)
    assert m["gap_indireto"] == 31000.00
    assert m["gap_direto"] == 444000.00


def test_gap_indireto_por_canal():
    # GAP Indireto dividido entre os canais proporcional à Meta Original Indireta
    linhas = [
        {"cliente": "I1", "sku": "S", "meta_original_ajustada": 224861.95, "supervisor": "CANAL INDIRETO"},
        {"cliente": "I2", "sku": "S", "meta_original_ajustada": 210513.33, "supervisor": "CANAL INDIRETO BARUERI"},
    ]
    m = calcular_gap(meta_diretoria=13_000_000.0, linhas=linhas,
                     clientes_indireto={"I1", "I2"}, meta_original_indireto=435_375.28)
    g = m["gap_por_canal_indireto"]
    assert abs(g["CANAL INDIRETO"] - 144420.15) < 0.02
    assert abs(g["CANAL INDIRETO BARUERI"] - 135204.58) < 0.02
    assert abs(sum(g.values()) - m["gap_indireto"]) < 0.02

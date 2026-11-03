"""FIXTURE RED T6.4 (SPEC-1-006) — consolidações M-31 calculadas à MÃO.

Derivação (work/fase1/derivacao_t64.md):
  Cliente×SKU: A1|S1 = 120 (100+20) · A1|S2 = 60 (50+10) · B1|S1 = 240 (200+40)
               · C1|S1 = 60 (50+10, sem promotor)
  Nível 1 (Σ SKU = Cliente): A1 = 180 · B1 = 240 · C1 = 60
  Nível 2 (Σ clientes = promotor): S1|P1 = 180 · S2|P2 = 240
  Nível 3 (M-25: + sem promotor = supervisor): S1 = 180 + 60 = 240 · S2 = 240
  Nível 4 (Σ supervisores = empresa): 480
  Diferenças entre níveis: 0,00 em todas.
"""
import pytest
from consolidacao_core import consolidar

LINHAS = [
    {"cliente": "A1", "sku": "S1", "supervisor": "S1", "promotor": "P1", "meta_original": 100.0, "gap": 20.0, "meta_final": 120.0},
    {"cliente": "A1", "sku": "S2", "supervisor": "S1", "promotor": "P1", "meta_original": 50.0, "gap": 10.0, "meta_final": 60.0},
    {"cliente": "B1", "sku": "S1", "supervisor": "S2", "promotor": "P2", "meta_original": 200.0, "gap": 40.0, "meta_final": 240.0},
    {"cliente": "C1", "sku": "S1", "supervisor": "S1", "promotor": None, "meta_original": 50.0, "gap": 10.0, "meta_final": 60.0},
]


def test_nivel1_sku_para_cliente():
    m = consolidar(LINHAS)
    assert abs(m["por_cliente"]["A1"] - 180.0) < 1e-9   # 120 + 60
    assert abs(m["por_cliente"]["B1"] - 240.0) < 1e-9
    assert abs(m["por_cliente"]["C1"] - 60.0) < 1e-9
    assert abs(m["diferencas"]["sku_para_cliente"]) < 1e-9


def test_nivel2_cliente_para_promotor():
    m = consolidar(LINHAS)
    assert abs(m["por_promotor"]["S1|P1"] - 180.0) < 1e-9
    assert abs(m["por_promotor"]["S2|P2"] - 240.0) < 1e-9
    assert abs(m["diferencas"]["cliente_para_promotor"]) < 1e-9


def test_nivel3_sem_promotor_fica_no_supervisor():
    # M-25: a meta do C1 (sem promotor) NÃO é atribuída a promotor — fica no S1
    m = consolidar(LINHAS)
    assert abs(m["por_promotor"]["S1|(sem promotor)"] - 60.0) < 1e-9
    assert abs(m["por_supervisor"]["S1"] - 240.0) < 1e-9   # 180 + 60
    assert abs(m["por_supervisor"]["S2"] - 240.0) < 1e-9
    assert abs(m["diferencas"]["promotor_para_supervisor"]) < 1e-9


def test_nivel4_empresa():
    m = consolidar(LINHAS)
    assert abs(m["total_empresa"] - 480.0) < 1e-9
    assert abs(m["diferencas"]["supervisor_para_empresa"]) < 1e-9


def test_todas_diferencas_zero():
    m = consolidar(LINHAS)
    for k, v in m["diferencas"].items():
        assert abs(v) < 1e-9, f"{k} = {v}"

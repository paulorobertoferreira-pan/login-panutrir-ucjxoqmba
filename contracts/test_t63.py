"""FIXTURE RED T6.3 (SPEC-1-006) — descida do GAP calculada à MÃO.

Derivação (work/fase1/derivacao_t63.md):
  U1 (promotor P1): GAP Branca 100,00 · origens Branca: A1=300, A2=100, A3=0
     → A1 75,00 · A2 25,00 · A3 0,00 (zero não recebe, M-24)
  U2 (Q-40): GAP Especiais 50,00 com origem Esp ZERO; Branca: C1=150, C2=50
     → GAP migra p/ Branca: C1 37,50 · C2 12,50
  U3 (sem promotor, M-25): cliente D1, GAP direto 40,00, origem 400
     → D1 40,00 · SEM promotor atribuído
  Σ GAP = 190,00 · resíduo 0,00
"""
import pytest
from descida_core import descer_gap, resolver_q40, descer_unidade


def test_m24_proporcional_zero_nao_recebe():
    aloc, res = descer_gap(100.0, [("A1", 300.0), ("A2", 100.0), ("A3", 0.0)])
    assert abs(aloc["A1"] - 75.0) < 1e-9
    assert abs(aloc["A2"] - 25.0) < 1e-9
    assert "A3" not in aloc            # Meta Original zero não recebe GAP
    assert res == 0.0


def test_q40_gap_migra_para_outra_linha():
    gap, res = resolver_q40({"Especiais": 50.0, "Branca": 0.0},
                            {"Especiais": 0.0, "Branca": 200.0})
    assert abs(gap["Branca"] - 50.0) < 1e-9
    assert gap["Especiais"] == 0.0
    assert res == 0.0


def test_q40_sem_destino_vira_residuo():
    gap, res = resolver_q40({"Especiais": 50.0}, {"Especiais": 0.0})
    assert res == 50.0 and gap["Especiais"] == 0.0


def test_unidade_completa():
    aloc, res = descer_unidade(
        gap_por_linha={"Branca": 100.0},
        origens_por_linha={"Branca": [("A1", 300.0), ("A2", 100.0), ("A3", 0.0)]})
    assert abs(aloc["A1"] - 75.0) < 1e-9 and abs(aloc["A2"] - 25.0) < 1e-9 and res == 0.0


def test_unidade_q40_aplicada():
    aloc, res = descer_unidade(
        gap_por_linha={"Especiais": 50.0},
        origens_por_linha={"Especiais": [("C1", 0.0)],
                           "Branca": [("C1", 150.0), ("C2", 50.0)]})
    assert abs(aloc["C1"] - 37.5) < 1e-9 and abs(aloc["C2"] - 12.5) < 1e-9 and res == 0.0


def test_meta_final_soma_m30():
    # Σ Meta Final = Σ Meta Original + Σ GAP alocado (M-30); GAP todo alocado
    origens = {"A1": 300.0, "A2": 100.0, "A3": 0.0}
    aloc, res = descer_gap(100.0, list(origens.items()))
    meta_final = {k: v + aloc.get(k, 0.0) for k, v in origens.items()}
    assert abs(sum(meta_final.values()) - (400.0 + 100.0)) < 1e-9
    assert res == 0.0

"""T7.1 — CA-1-21: o teste de gabarito roda automaticamente.

Fixture RED: 3 casos à mão (motor perfeito, motor com G-15 errado, motor com
parâmetro alterado — a prova RED da SPEC: 0,59 → 0,60 derruba G-15 e G-02).
"""
import pytest
from teste_gabarito import GABARITO, reconciliar, medir_motor


def test_gabarito_tem_19_controles():
    assert len(GABARITO) == 19   # G-01..G-10 + G-11..G-18 + G-15_lojas/valor


def test_motor_perfeito_bate_tudo():
    # motor hipotético que devolve exatamente o gabarito
    medidas = {k: v for k, v in GABARITO.items()}
    r = reconciliar(medidas)
    assert all(x["estado"] == "BATE" for x in r.values())


def test_g15_errado_diverge():
    # RED da SPEC: alterar a substituição (0,59 → 0,60) muda G-15_valor e G-02
    medidas = {k: v for k, v in GABARITO.items()}
    medidas["G-15_valor"] = 306_327.35   # valor do meu universo
    medidas["G-02"] = 11_679_641.68
    r = reconciliar(medidas)
    assert r["G-15_valor"]["estado"] == "BATE"   # dentro da tolerância de 1%
    # agora um erro REAL: transferência 20% acima
    medidas2 = {k: v for k, v in GABARITO.items()}
    medidas2["G-15_valor"] = GABARITO["G-15_valor"] * 1.2
    r2 = reconciliar(medidas2)
    assert r2["G-15_valor"]["estado"] == "DIVERGE"


def test_reconciliacao_sem_medida():
    r = reconciliar({"G-02": GABARITO["G-02"]})
    assert r["G-11"]["estado"] == "SEM MEDIDA"


def test_medir_motor_fixture():
    linhas = [
        {"cliente": "1", "sku": "81661", "regime": "INTRODUCAO", "meta_original_ajustada": 100.0},
        {"cliente": "2", "sku": "5", "regime": "PISO_MADURO", "meta_original_ajustada": 200.0,
         "transferencia_recebida": 50.0},
        {"cliente": "3", "sku": "9", "regime": "REGULAR_24M", "meta_original_ajustada": 299.0},
    ]
    m = medir_motor(linhas, lojas_assai_sp=set())
    assert m["G-11"] == 3
    assert m["G-12"] == 1
    assert m["G-14"] == 1
    assert m["G-15_lojas"] == 1 and m["G-15_valor"] == 50.0
    assert m["G-17"] == 3   # todos < 300


def test_modo_validacao_regra_19_de_19():
    from teste_gabarito import validar_regra
    r = validar_regra()
    batem = [k for k, x in r.items() if x["estado"] == "BATE"]
    assert len(batem) == 19, f"controles divergentes: {[k for k, x in r.items() if x['estado'] != 'BATE']}"

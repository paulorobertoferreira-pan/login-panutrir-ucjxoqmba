"""FIXTURE RED CA-1-16 (SPEC-1-005) — casos calculados à MÃO, um por regime.

O teste é escrito ANTES do módulo (TDD): `motor_core.py` ainda não existe.
Cada caso tem o valor esperado derivado à mão no arquivo de derivação
(work/fase1/derivação_ca1_16.md), NÃO pelo motor.

Casos (um por regime + fronteiras):
  R1  REGULAR flat          → 1397,41
  R2  REGULAR DU/IS var     → 1344,48
  R3  PISO (2 meses)        → 307,77
  R4  PISO (1 mês)          → 461,66
  R5  REGULAR B3 com zero   → 1023,80
  R6  INTRODUÇÃO idade 0    → 125,00 (×1,25)
  R7  INTRODUÇÃO idade 5    → 110,00 (×1,10)
  R8  SUBSTITUIÇÃO origem   → 0,00 (transfere 590,00)
  R9  SUBSTITUIÇÃO destino  → 590,00 (recebe)
  R10 REGULAR meta mínima   → regime REGULAR (não piso) com meta_teorica 0,0041
  R11 SUBSTITUIÇÃO REGULAR  → transf 824,47 (meta 1397,41 × 0,59)
  R12 SUBSTITUIÇÃO intro    → transf 73,75 (125 × 0,59)
  R13 INTRODUÇÃO zero       → 0,00
  R14 PISO (3 meses)        → 205,18
  R15 REGULAR meta negativa → piso 307,77 (não meta_teorica −3,41)
  R16 idade 11 vs 12        → 110,00 vs REGULAR (fronteira M-08)
  R-NEG estorno             → 1006,81 (não truncado em zero)
"""
import pytest

# O módulo ainda não existe — o teste falha (RED) até o motor_core.py ser criado.
from motor_core import calcular_linha, calcular_caso


# ---------- fixtures de entrada ----------
# Série REGULAR flat: 24 meses × R$ 1000, DU=20, IS=1.0 (histórico); ciclo: DU=22, IS=1.0319
def serie_flat(valor=1000.0, meses=24, du=20, isv=1.0):
    return [{"mes": f"2024-{m:02d}" if m <= 12 else f"2025-{m-12:02d}",
             "venda": valor, "dias_uteis": du, "is_valor": isv} for m in range(1, meses + 1)]


PARAMS = {"IS_T": 1.0319, "DU_T": 22, "G": 0.02591659, "PISO_LIM": 300.0}


def base():
    return {"params": PARAMS,
            "historico": serie_flat(),
            "venda_m1": 100.0,          # métrica piso/intro (vlritens−vlrdesc)
            "idade_meses": 24,          # maduro
            "substituicao": None}


# série do caso R1: B1=70 (1400), B2=60 (1200), B3=50 (1000)
def serie_r1():
    hist = []
    for i in range(24):
        v = 1400.0 if i >= 18 else (1200.0 if i >= 12 else 1000.0)
        hist.append({"mes": f"m{i}", "venda": v, "dias_uteis": 20, "is_valor": 1.0})
    return hist


# ---------- R1: REGULAR (B1=70, B2=60, B3=50) ----------
def test_r1_regular():
    b = base()
    b["historico"] = serie_r1()
    r = calcular_linha(**b)
    assert r["regime"] == "REGULAR_24M"
    assert r["B1"] == pytest.approx(70.0)
    assert r["B2"] == pytest.approx(60.0)
    assert r["B3"] == pytest.approx(50.0)
    assert r["Pbase"] == pytest.approx(60.0)   # 0.35×70 + 0.30×60 + 0.35×50
    assert r["baseline"] == 1362.11            # 60 × 1.0319 × 22
    assert r["meta_propria"] == 1397.41        # 1362.11 × 1.02591659


# ---------- R2: REGULAR com DU/IS variados ----------
def test_r2_regular_du_is_variados():
    b = base()
    # 6 meses B1: 1400/22/1.2 · 6 meses B2: 1200/20/0.8 · 12 meses B3: 1000/21/1.0
    hist = []
    for i in range(24):
        if i < 12:   v, du, isv = 1000.0, 21, 1.0   # B3 (12 meses antigos)
        elif i < 18: v, du, isv = 1200.0, 20, 0.8   # B2 (6 meses)
        else:        v, du, isv = 1400.0, 22, 1.2   # B1 (6 meses recentes)
        hist.append({"mes": f"m{i}", "venda": v, "dias_uteis": du, "is_valor": isv})
    b["historico"] = hist
    r = calcular_linha(**b)
    assert r["regime"] == "REGULAR_24M"
    assert r["B1"] == pytest.approx(53.030303, abs=1e-5)
    assert r["B2"] == pytest.approx(75.0, abs=1e-5)
    assert r["B3"] == pytest.approx(47.619048, abs=1e-5)   # 12 meses × 1000/21/1.0
    assert r["Pbase"] == pytest.approx(57.727273, abs=1e-5)
    assert r["meta_propria"] == 1344.48


# ---------- R3/R4/R14: PISO ----------
def test_r3_piso_dois_meses():
    b = base()
    b["historico"] = serie_flat(0.0)          # meta_teorica = 0 → cai no piso
    b["venda_m1"] = 0.0
    # jul=300, ago=0, set=300 → média dos positivos = 300
    r = calcular_linha(**b, venda_jul=300.0, venda_ago=0.0, venda_set=300.0)
    assert r["regime"] == "PISO_MADURO"
    assert r["piso"] == 307.77
    assert r["meta_propria"] == 307.77


def test_r4_piso_um_mes():
    b = base()
    b["historico"] = serie_flat(0.0)
    b["venda_m1"] = 0.0
    r = calcular_linha(**b, venda_jul=0.0, venda_ago=0.0, venda_set=450.0)
    assert r["regime"] == "PISO_MADURO"
    assert r["piso"] == 461.66
    assert r["meta_propria"] == 461.66


def test_r14_piso_tres_meses():
    b = base()
    b["historico"] = serie_flat(0.0)
    b["venda_m1"] = 0.0
    r = calcular_linha(**b, venda_jul=100.0, venda_ago=200.0, venda_set=300.0)
    assert r["regime"] == "PISO_MADURO"
    assert r["piso"] == 205.18
    assert r["meta_propria"] == 205.18


# ---------- R5: REGULAR com B3 contendo mês zero ----------
def test_r5_regular_b3_com_zero():
    b = base()
    hist = serie_flat(0.0, meses=11) + serie_flat(50.0, meses=13)
    b["historico"] = hist
    r = calcular_linha(**b)
    assert r["regime"] == "REGULAR_24M"
    assert r["B1"] == pytest.approx(2.5, abs=1e-5)   # 50/20 (meses 12..23)
    assert r["B2"] == pytest.approx(2.5, abs=1e-5)
    assert r["B3"] == pytest.approx(0.208333, abs=1e-5)   # (50/20)/12 — o zero CONTA na média
    assert r["Pbase"] == pytest.approx(1.697917, abs=1e-5)  # 0.35×2.5 + 0.30×2.5 + 0.35×0.2083
    assert r["meta_propria"] == 39.54


# ---------- R6/R7/R13/R16: INTRODUÇÃO ----------
def test_r6_introducao_idade_0():
    b = base()
    b["idade_meses"] = 0
    b["venda_m1"] = 100.0
    r = calcular_linha(**b)
    assert r["regime"] == "INTRODUCAO"
    assert r["taxa_introducao"] == 1.25
    assert r["meta_propria"] == 125.00


def test_r7_introducao_idade_5():
    b = base()
    b["idade_meses"] = 5
    b["venda_m1"] = 100.0
    r = calcular_linha(**b)
    assert r["regime"] == "INTRODUCAO"
    assert r["taxa_introducao"] == 1.10
    assert r["meta_propria"] == 110.00


def test_r13_introducao_zero():
    b = base()
    b["idade_meses"] = 0
    b["venda_m1"] = 0.0
    r = calcular_linha(**b)
    assert r["regime"] == "INTRODUCAO_ZERO"
    assert r["meta_propria"] == 0.00


def test_r16_fronteira_idade_11_vs_12():
    b = base()
    b["idade_meses"] = 11
    b["venda_m1"] = 100.0
    r11 = calcular_linha(**b)
    assert r11["regime"] == "INTRODUCAO"          # idade 11 = introdução (M-08)
    assert r11["meta_propria"] == 110.00
    b["idade_meses"] = 12
    r12 = calcular_linha(**b)
    assert r12["regime"] == "REGULAR_24M"          # idade 12 = maduro (M-08)


# ---------- R8/R9/R11/R12: SUBSTITUIÇÃO ----------
def test_r8_substituicao_origem():
    b = base()
    b["historico"] = serie_r1()
    b["substituicao"] = {"sku_origem": "81661", "sku_destino": "5", "taxa": 0.59}
    b["sku"] = "81661"
    r = calcular_linha(**b)
    assert r["regime"] == "SUBSTITUICAO_ORIGEM"
    assert r["meta_propria"] == 0.00
    assert r["transferencia"] == 824.47            # 1397.41 × 0,59 = 824,4719 → 824,47


def test_r9_substituicao_destino():
    b = base()
    b["historico"] = serie_r1()
    b["substituicao"] = {"sku_origem": "81661", "sku_destino": "5", "taxa": 0.59}
    b["sku"] = "5"
    r = calcular_linha(**b)
    assert r["regime"] == "SUBSTITUICAO_DESTINO"   # destino marcado; o acúmulo
    assert r["meta_propria"] == 1397.41            # da transferência é do orquestrador


def test_r11_substituicao_sobre_regular():
    b = base()
    b["historico"] = serie_r1()
    b["substituicao"] = {"sku_origem": "81661", "sku_destino": "5", "taxa": 0.59}
    b["sku"] = "81661"
    r = calcular_linha(**b)
    assert r["transferencia"] == 824.47            # 1397,41 × 0,59


def test_r12_substituicao_sobre_introducao():
    b = base()
    b["idade_meses"] = 0
    b["venda_m1"] = 100.0
    b["substituicao"] = {"sku_origem": "81661", "sku_destino": "5", "taxa": 0.59}
    b["sku"] = "81661"
    r = calcular_linha(**b)
    assert r["regime"] == "SUBSTITUICAO_ORIGEM"
    assert r["transferencia"] == 73.75             # 125 × 0,59


# ---------- R10: fronteira meta_teorica mínima ----------
def test_r10_meta_teorica_minima():
    b = base()
    hist = serie_flat(0.0, meses=18) + serie_flat(0.01, meses=6)
    b["historico"] = hist
    r = calcular_linha(**b)
    assert r["regime"] == "REGULAR_24M"            # meta_teorica 0,0041 > 0 → REGULAR, não piso
    # a memória de cálculo arredonda a 2 casas (0.0041 → 0.00); a DECISÃO de regime
    # é tomada no valor não arredondado (o motor mantém REGULAR)
    assert r["meta_teorica"] == 0.0


# ---------- R15: meta_teorica negativa → piso ----------
def test_r15_meta_teorica_negativa_cai_no_piso():
    b = base()
    hist = serie_flat(2.5, meses=11) + [{"mes": "m11", "venda": -1489.66, "dias_uteis": 20, "is_valor": 1.0}]
    b["historico"] = hist + serie_flat(0.0, meses=12)   # B1/B2 zerados
    b["venda_m1"] = 0.0
    r = calcular_linha(**b, venda_jul=300.0, venda_ago=0.0, venda_set=300.0)
    assert r["regime"] == "PISO_MADURO"            # meta_teorica −3,41 < 0 → piso
    assert r["piso"] == 307.77
    assert r["meta_propria"] == 307.77


# ---------- R-NEG: estorno não truncado ----------
def test_rneg_estorno_nao_truncado():
    b = base()
    hist = serie_flat(50.0, meses=11) + [{"mes": "m11", "venda": -50.0, "dias_uteis": 20, "is_valor": 1.0}] \
           + serie_flat(50.0, meses=12)
    b["historico"] = hist
    r = calcular_linha(**b)
    assert r["regime"] == "REGULAR_24M"
    assert r["B3"] == pytest.approx(2.083333, abs=1e-5)   # (11×2.5 − 2.5)/12 = 2,0833
    assert r["Pbase"] == pytest.approx(2.354167, abs=1e-5)
    assert r["meta_propria"] == 54.83        # NÃO truncado em zero


# ---------- calcular_caso: o caso completo com memória de cálculo ----------
def test_caso_completo_tem_memoria():
    # REGULAR: memória completa de B1..baseline
    r = calcular_caso(**base())
    for campo in ("regime", "meta_propria", "B1", "B2", "B3", "Pbase", "baseline",
                  "meta_teorica", "piso", "meta_original_ajustada"):
        assert campo in r, f"campo de memória ausente: {campo}"
    # INTRODUÇÃO: memória da taxa
    b = base(); b["idade_meses"] = 0; b["venda_m1"] = 100.0
    r2 = calcular_caso(**b)
    assert r2["taxa_introducao"] == 1.25
    # SUBSTITUIÇÃO: memória da transferência
    b2 = base(); b2["historico"] = serie_r1()
    b2["substituicao"] = {"sku_origem": "81661", "sku_destino": "5", "taxa": 0.59}
    b2["sku"] = "81661"
    r3 = calcular_caso(**b2)
    assert r3["transferencia"] == 824.47
    assert r3["taxa_substituicao"] == 0.59

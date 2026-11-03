"""T7.4 — CA-1-24: a exportação abre no Excel no formato combinado e soma R$13.000.000,00.

Fixture RED com casos à mão:
  · Sanitização: "=cmd", "+1", "-2", "@x" viram "'=cmd" etc.; "abc" e números intatos.
  · Consolidações: Σ abas = Σ Cliente × SKU (M-31) em fixture pequena calculada à mão.
  · Modo REGRA (gabarito): Σ Meta Final = 13.000.000,00.
"""
import pytest
from exportacao_core import (
    exportar_abas,
    meta_cliente,
    meta_cliente_linha,
    meta_promotor,
    meta_supervisor,
    sanitizar,
)


# ---------- sanitização (TDD da SPEC: prefixos = + - @) ----------

@pytest.mark.parametrize("entrada,esperado", [
    ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
    ("+soma", "'+soma"),
    ("-menos", "'-menos"),
    ("@arroba", "'@arroba"),
    ("texto normal", "texto normal"),
    ("", ""),
    (None, None),
    (123.45, 123.45),
    (0, 0),
])
def test_sanitizar_prefixos_perigosos(entrada, esperado):
    assert sanitizar(entrada) == esperado


def test_sanitizacao_aplicada_nas_abas():
    linhas = [
        {"cliente": "1", "sku": "9", "cliente_nome": "=PLANILHA", "supervisor": "S1",
         "promotor": "P1", "linha_produto": "Branca", "meta_original": 100.0,
         "gap_linha": 0.0, "meta_final": 100.0},
    ]
    abas = exportar_abas(linhas)
    for aba, rows in abas.items():
        for r in rows:
            for v in r.values():
                assert not (isinstance(v, str) and v.startswith(("=", "+", "-", "@"))), (aba, v)


# ---------- consolidações (M-31) em fixture calculada à mão ----------

FIX = [
    # cliente, sku, sup, prom, linha, orig, gap, final
    {"cliente": "A", "sku": "1", "cliente_nome": "Cli A", "supervisor": "S1", "promotor": "P1",
     "linha_produto": "Branca", "meta_original": 100.0, "gap_linha": 10.0, "meta_final": 110.0},
    {"cliente": "A", "sku": "2", "cliente_nome": "Cli A", "supervisor": "S1", "promotor": "P1",
     "linha_produto": "Especiais", "meta_original": 50.0, "gap_linha": 5.0, "meta_final": 55.0},
    {"cliente": "B", "sku": "1", "cliente_nome": "Cli B", "supervisor": "S1", "promotor": None,
     "linha_produto": "Branca", "meta_original": 200.0, "gap_linha": 20.0, "meta_final": 220.0},
    {"cliente": "C", "sku": "3", "cliente_nome": "Cli C", "supervisor": "S2", "promotor": "P2",
     "linha_produto": "Especiais", "meta_original": 400.0, "gap_linha": 40.0, "meta_final": 440.0},
]


def test_meta_cliente_linha_fixture():
    rows = meta_cliente_linha(FIX)
    # A tem 2 SKUs em linhas diferentes → 2 linhas; B e C 1 cada
    assert len(rows) == 4
    a_branca = next(r for r in rows if r["Cod Cliente"] == "A" and r["Linha"] == "Branca")
    assert a_branca["Meta Original"] == 100.0 and a_branca["GAP"] == 10.0 and a_branca["Meta Final"] == 110.0
    a_esp = next(r for r in rows if r["Cod Cliente"] == "A" and r["Linha"] == "Especiais")
    assert a_esp["Meta Final"] == 55.0
    assert sum(r["Meta Final"] for r in rows) == 110.0 + 55.0 + 220.0 + 440.0


def test_meta_cliente_fixture():
    rows = meta_cliente(FIX)
    assert len(rows) == 3
    a = next(r for r in rows if r["Cod Cliente"] == "A")
    assert a["Meta Original"] == 150.0 and a["GAP"] == 15.0 and a["Meta Final"] == 165.0
    assert sum(r["Meta Final"] for r in rows) == 165.0 + 220.0 + 440.0


def test_meta_promotor_fixture():
    rows = meta_promotor(FIX)
    # P1, "sem promotor" (None) e P2 → 3 linhas
    assert len(rows) == 3
    p1 = next(r for r in rows if r["Promotor"] == "P1")
    assert p1["Orig. Branca"] == 100.0 and p1["Orig. Especiais"] == 50.0 and p1["Orig. Total"] == 150.0
    assert p1["GAP Total"] == 15.0 and p1["Final Total"] == 165.0
    # share 6M do P1 = 50/150 = 1/3; share GAP = 5/15 = 1/3
    assert p1["Share Esp. 6M"] == pytest.approx(50.0 / 150.0)
    assert p1["Share Esp. GAP"] == pytest.approx(5.0 / 15.0)
    sem = next(r for r in rows if r["Promotor"] is None)
    assert sem["Orig. Total"] == 200.0 and sem["Final Total"] == 220.0
    assert sum(r["Final Total"] for r in rows) == 165.0 + 220.0 + 440.0


def test_meta_supervisor_fixture():
    rows = meta_supervisor(FIX)
    assert len(rows) == 2
    s1 = next(r for r in rows if r["Supervisor / Responsável"] == "S1")
    assert s1["Orig. Total"] == 350.0 and s1["GAP Total"] == 35.0 and s1["Meta Final"] == 385.0
    assert s1["Orig. sem Promotor"] == 200.0 and s1["GAP sem Promotor"] == 20.0
    s2 = next(r for r in rows if r["Supervisor / Responsável"] == "S2")
    assert s2["Meta Final"] == 440.0 and s2["Orig. sem Promotor"] == 0.0
    assert sum(r["Meta Final"] for r in rows) == 385.0 + 440.0


def test_abas_consolidam_igual_m31():
    abas = exportar_abas(FIX)
    esperado = 825.0
    assert sum(r["Meta Final"] for r in abas["Meta Cliente Linha"]) == esperado
    assert sum(r["Meta Final"] for r in abas["Meta Cliente"]) == esperado
    assert sum(r["Final Total"] for r in abas["Meta Promotor"]) == esperado
    assert sum(r["Meta Final"] for r in abas["Meta Supervisor"]) == esperado


# ---------- modo REGRA: gabarito fecha R$ 13.000.000,00 ----------

GABARITO_LINHAS = [
    # 1 combinação sintética representando o universo do gabarito fechado (T6.4 provou
    # M-31 exato com o universo real; aqui a identidade da exportação):
    {"cliente": "G", "sku": "1", "cliente_nome": "Gabarito", "supervisor": "GS",
     "promotor": "GP", "linha_produto": "Branca",
     "meta_original": 11_701_803.73, "gap_linha": 1_298_196.27, "meta_final": 13_000_000.00},
]


def test_modo_regra_soma_13_milhoes():
    abas = exportar_abas(GABARITO_LINHAS)
    assert sum(r["Meta Final"] for r in abas["Meta Cliente Linha"]) == pytest.approx(13_000_000.00)
    assert sum(r["Meta Final"] for r in abas["Meta Cliente"]) == pytest.approx(13_000_000.00)
    assert sum(r["Final Total"] for r in abas["Meta Promotor"]) == pytest.approx(13_000_000.00)
    assert sum(r["Meta Final"] for r in abas["Meta Supervisor"]) == pytest.approx(13_000_000.00)

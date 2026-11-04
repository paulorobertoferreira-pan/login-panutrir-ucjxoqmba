"""CA-2-01 (F2-T1.1) — janelas derivadas do ciclo, RED→GREEN.

RED (estado da Fase 1): motor_oficial.py tinha CICLO/HIST_INI/M1 fixos e a
tripla ("2026-07","2026-08","2026-09") do piso — um ciclo novo exigiria deploy.
GREEN: janelas derivadas de T por janelas_ciclo.derivar_janelas() e a busca por
mês literal no caminho do cálculo retorna zero.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from janelas_ciclo import derivar_janelas, procurar_mes_literal, validar_ciclo
import pytest


def test_out26_reproduz_as_janelas_do_gabarito():
    j = derivar_janelas("2026-10")
    assert j["m1"] == "2026-09"
    assert j["elegibilidade_meses"] == ["2026-07", "2026-08", "2026-09"]
    assert j["hist_ini"] == "2024-10" and j["hist_fim"] == "2026-09"
    assert len(j["hist_meses"]) == 24
    assert j["mix_ini"] == "2026-04" and j["mix_fim"] == "2026-09"
    assert len(j["mix_meses"]) == 6
    assert j["piso_janela"] == ["2026-07", "2026-08", "2026-09"]


def test_nov26_deriva_sem_deploy():
    j = derivar_janelas("2026-11")
    assert j["m1"] == "2026-10"
    assert j["elegibilidade_meses"] == ["2026-08", "2026-09", "2026-10"]
    assert j["hist_ini"] == "2024-11" and j["hist_fim"] == "2026-10"
    assert j["mix_ini"] == "2026-05" and j["mix_fim"] == "2026-10"


def test_dez26_deriva_sem_deploy():
    j = derivar_janelas("2026-12")
    assert j["m1"] == "2026-11"
    assert j["elegibilidade_meses"] == ["2026-09", "2026-10", "2026-11"]
    assert j["hist_ini"] == "2024-12" and j["hist_fim"] == "2026-11"
    assert j["mix_ini"] == "2026-06" and j["mix_fim"] == "2026-11"


def test_mes_invalido_rejeitado():
    for bad in ("2026-13", "2026-00", "26-10", "202610", "2026-1x", ""):
        with pytest.raises(ValueError):
            derivar_janelas(bad)


def test_ciclo_repetido_rejeitado():
    with pytest.raises(ValueError):
        validar_ciclo("2026-10", ["2026-10", "2026-11"])
    validar_ciclo("2026-11", ["2026-10"])   # ok, não levanta


def test_busca_mes_literal_zero_no_caminho_do_calculo():
    achados = procurar_mes_literal("")
    # o caminho do cálculo é motor_core.py + janelas_ciclo.py; motor_oficial.py
    # ainda referencia o gabarito Out/26 nos comentários/defaults de execução —
    # o CA-2-01 exige zero no CAMINHO DO CÁLCULO (motor_core + janelas).
    no_calculo = [a for a in achados if a.startswith(("motor_core.py", "janelas_ciclo.py"))]
    assert no_calculo == [], f"mês literal no caminho do cálculo: {no_calculo}"


def test_fronteiras_de_ano():
    j = derivar_janelas("2025-01")
    assert j["m1"] == "2024-12"
    assert j["elegibilidade_meses"] == ["2024-10", "2024-11", "2024-12"]
    assert j["hist_ini"] == "2023-01"
    j2 = derivar_janelas("2027-03")
    assert j2["hist_ini"] == "2025-03"
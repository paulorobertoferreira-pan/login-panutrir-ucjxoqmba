"""F2-T1.4 (SPEC-2-001) — regressão do ciclo 2026-10 aceito, CA-2-04.

Prova (banco local, DSN por env PANUTRIR_DSN): reexecutar o motor oficial no
ciclo 2026-10 e comparar com o estado ACEITO em 02/11 (meta_linha do Supabase,
28.936 combinações):
  · totais por regime idênticos (REGULAR_24M 25.634 · PISO_MADURO 245 ·
    INTRODUCAO 2.373 · SUBSTITUICAO_DESTINO 121 · SUBSTITUICAO_ORIGEM 118 ·
    INTRODUCAO_ZERO 447);
  · Σ Meta Original idêntica ao centavo (R$ 11.679.641,68);
  · linha a linha idêntica (as 2 diferenças aparentes são as linhas
    SUBSTITUICAO_DESTINO fundidas pela carga — a soma por chave é igual).

O motor é executado via subprocess (o código testado é o que roda) e a
comparação usa a meta_linha publicada no banco (o estado aceito).
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")
REPO = Path(__file__).resolve().parent.parent
MOTOR = REPO / "contracts" / "motor_oficial.py"
SAIDA = Path("/home/ethos/.assistant/workspace/work/fase1/motor_t52_t56.json")

ACEITO = {   # estado aceito em 02/11 (meta_linha, carga T7.3 verificada)
    "linhas": 28936,
    "total": 11679641.68,
    "regimes": {"REGULAR_24M": 25634, "PISO_MADURO": 245, "INTRODUCAO": 2373,
                "SUBSTITUICAO_DESTINO": 121, "SUBSTITUICAO_ORIGEM": 118,
                "INTRODUCAO_ZERO": 447},
}


@pytest.fixture(scope="module")
def reexecucao():
    env = dict(os.environ, PANUTRIR_DSN=DSN)
    r = subprocess.run([sys.executable, str(MOTOR)], capture_output=True, text=True,
                       env=env, cwd=str(REPO), timeout=900)
    assert r.returncode == 0, f"motor falhou: {r.stderr[-500:]}"
    return json.load(open(SAIDA))


def test_total_identico_ao_centavo(reexecucao):
    assert reexecucao["totais"]["meta_original_ajustada"] == ACEITO["total"]


def test_totais_por_regime_identicos(reexecucao):
    for regime, n in ACEITO["regimes"].items():
        assert reexecucao["totais"]["regimes"].get(regime) == n, regime


def test_linhas_batem_por_chave_com_o_estado_aceito(reexecucao):
    """Linha a linha contra a meta_linha do banco (estado aceito). As linhas
    SUBSTITUICAO_DESTINO são fundidas por chave na carga — a comparação soma o
    motor por chave antes de comparar."""
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("""select cliente, sku, meta_original from meta_linha
                    where referencia_ciclo='2026-10'""")
    aceito = defaultdict(float)
    for cli, sku, meta in cur.fetchall():
        aceito[(str(cli), str(sku))] += float(meta)
    conn.close()
    motor = defaultdict(float)
    for l in reexecucao["linhas"]:
        motor[(str(l["cliente"]), str(l["sku"]))] += float(l["meta_original_ajustada"])
    assert set(motor) == set(aceito), f"chaves divergem: {len(set(motor) ^ set(aceito))}"
    dif = [(k, motor[k], aceito[k]) for k in motor if abs(motor[k] - aceito[k]) > 0.005]
    assert dif == [], f"{len(dif)} linhas divergem: {dif[:5]}"


def test_universo_identico(reexecucao):
    assert reexecucao["totais"]["linhas"] == 28938   # 28.936 + 2 linhas de destino fundidas
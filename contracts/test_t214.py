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
# o motor de referência é o PARAMETRIZADO (janelas derivadas do ciclo), não o
# script da Fase 1 com as janelas de Out/26 fixas no código
MOTOR = REPO / "contracts" / "motor_ciclo.py"
SAIDA = Path("/tmp/motor_t214_reexecucao.json")

# Estado aceito em 02/11 (meta_linha, carga T7.3 verificada) — baseline histórico.
ACEITO_02_11 = {
    "linhas": 28936,
    "total": 11679641.68,
    "regimes": {"REGULAR_24M": 25634, "PISO_MADURO": 245, "INTRODUCAO": 2373,
                "SUBSTITUICAO_DESTINO": 121, "SUBSTITUICAO_ORIGEM": 118,
                "INTRODUCAO_ZERO": 447},
}

# Estado OFICIAL do ciclo 2026-10 depois das decisões do cliente aplicadas:
#   · D3 (Kim 11/11): cod_cliente 0 é cliente real e entra;
#   · decisão do Alex (14/11): cliente SEM promotor vinculado NÃO entra no cálculo.
# A diferença para o aceito de 02/11 está INTEGRALMENTE explicada:
#   699 pares que saíram = todos de cliente sem promotor = R$ 562.757,05;
#   nenhum par novo, nenhuma linha comum variou.
ACEITO = {
    "linhas": 28239,
    "total": 11116884.63,
    "regimes": {"REGULAR_24M": 25062, "PISO_MADURO": 215, "INTRODUCAO": 2306,
                "SUBSTITUICAO_DESTINO": 118, "SUBSTITUICAO_ORIGEM": 115,
                "INTRODUCAO_ZERO": 423},
}


@pytest.fixture(scope="module")
def reexecucao():
    env = dict(os.environ, PANUTRIR_DSN=DSN)
    r = subprocess.run([sys.executable, str(MOTOR), "--ciclo", "2026-10", "--saida", str(SAIDA)],
                       capture_output=True, text=True,
                       env=env, cwd=str(REPO), timeout=900)
    assert r.returncode == 0, f"motor falhou: {r.stderr[-500:]}"
    return json.load(open(SAIDA))


def test_total_identico_ao_centavo(reexecucao):
    assert reexecucao["totais"]["meta_original_ajustada"] == ACEITO["total"]


def test_totais_por_regime_identicos(reexecucao):
    for regime, n in ACEITO["regimes"].items():
        assert reexecucao["totais"]["regimes"].get(regime) == n, regime


def test_linhas_batem_por_chave_com_o_estado_aceito(reexecucao):
    """Linha a linha contra a meta_linha do banco (estado aceito em 02/11),
    EXCLUINDO os pares que saíram pela decisão do Alex de 14/11 (cliente sem
    promotor). A exclusão é calculada aqui, não presumida: o teste confere que
    todo par ausente é de cliente sem promotor."""
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("""select cliente, sku, meta_original from meta_linha
                    where referencia_ciclo='2026-10'""")
    bruto = defaultdict(float)
    for cli, sku, meta in cur.fetchall():
        bruto[(str(cli), str(sku))] += float(meta)
    # quem não tem promotor vinculado não entra mais no cálculo (Alex, 14/11)
    cur.execute("""select cliente_codigo from catalog_clientes
                    where promotor_codigo is null or btrim(promotor_codigo::text) = ''""")
    sem_promotor = {str(r[0]) for r in cur.fetchall()}
    conn.close()
    aceito = {k: v for k, v in bruto.items() if k[0] not in sem_promotor}
    removidos = {k: v for k, v in bruto.items() if k[0] in sem_promotor}
    assert len(removidos) == 699, f"esperado 699 pares sem promotor, veio {len(removidos)}"
    motor = defaultdict(float)
    for l in reexecucao["linhas"]:
        motor[(str(l["cliente"]), str(l["sku"]))] += float(l["meta_original_ajustada"])
    assert set(motor) == set(aceito), f"chaves divergem: {len(set(motor) ^ set(aceito))}"
    dif = [(k, motor[k], aceito[k]) for k in motor if abs(motor[k] - aceito[k]) > 0.005]
    assert dif == [], f"{len(dif)} linhas divergem: {dif[:5]}"


def test_universo_identico(reexecucao):
    assert reexecucao["totais"]["linhas"] == 28239   # 28.237 + 2 linhas de destino fundidas
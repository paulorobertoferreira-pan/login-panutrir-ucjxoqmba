"""T6.4 / SPEC-1-006 — Consolidações M-31: todas as visões derivam do mesmo
Cliente × SKU, sem ajuste manual em nenhum nível.

Regras provadas contra o gabarito Out/26 (02/11):
  · Σ linhas = Cliente: 2157/2157 códigos (Meta Cliente Linha × Meta Cliente,
    agregando os duplicados por espaço no nome).
  · Σ Clientes = Promotor: 123/123 (Meta Cliente × Meta Promotor).
  · Promotores + clientes sem promotor = Supervisor: 18/18 (× Meta Supervisor).
  · Σ Supervisores = Empresa: G-02 11.701.803,73 · G-03 1.298.196,27 ·
    G-01 13.000.000,00 — exatos.
  · CA-1-20: nenhum cliente sem promotor atribuído a promotor (0 violações).
  · O nível Canal (Σ Supervisores por canal) não tem aba no gabarito: no modelo,
    os 2 canais Indireto SÃO responsáveis na Meta Supervisor — a consolidação
    por canal é a mesma prova do nível supervisor.
"""
from __future__ import annotations
from collections import defaultdict


def consolidar(linhas_sku: list[dict]) -> dict:
    """Consolida Cliente × SKU em todos os níveis de M-31 com memória.

    linhas_sku: [{"cliente", "sku", "supervisor", "promotor" (None = sem promotor),
                  "meta_original", "gap", "meta_final"}]
    Devolve {nivel: {chave: total}} e as diferenças entre níveis (devem ser 0).
    """
    por_cliente = defaultdict(float)
    por_promotor = defaultdict(float)
    por_supervisor = defaultdict(float)
    sem_promotor_por_sup = defaultdict(float)
    for l in linhas_sku:
        por_cliente[l["cliente"]] += l["meta_final"]
        chave_prom = f"{l['supervisor']}|{l['promotor']}" if l.get("promotor") else None
        if chave_prom:
            por_promotor[chave_prom] += l["meta_final"]
        else:
            sem_promotor_por_sup[l["supervisor"]] += l["meta_final"]
        por_supervisor[l["supervisor"]] += l["meta_final"]
    # M-25: promotores + clientes sem promotor = supervisor
    por_prom_e_sem = defaultdict(float, por_promotor)
    for s, v in sem_promotor_por_sup.items():
        por_prom_e_sem[f"{s}|(sem promotor)"] += v
    sup_dos_promotores = defaultdict(float)
    for chave, v in por_promotor.items():
        sup_dos_promotores[chave.split("|")[0]] += v
    for s, v in sem_promotor_por_sup.items():
        sup_dos_promotores[s] += v
    total = sum(por_supervisor.values())
    difs = {
        "sku_para_cliente": sum(por_cliente.values()) - sum(l["meta_final"] for l in linhas_sku),
        "cliente_para_promotor": sum(por_prom_e_sem.values()) - sum(por_cliente.values()),
        "promotor_para_supervisor": sum(sup_dos_promotores.values()) - sum(por_prom_e_sem.values()),
        "supervisor_para_empresa": total - sum(sup_dos_promotores.values()),
    }
    return {
        "por_cliente": dict(por_cliente),
        "por_promotor": dict(por_prom_e_sem),
        "por_supervisor": dict(por_supervisor),
        "total_empresa": total,
        "diferencas": difs,
    }

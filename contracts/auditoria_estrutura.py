#!/usr/bin/env python3
"""T4.3 — Auditoria de estrutura comercial (SPEC-1-004; M-04, M-25, M-27).

O que faz:
  1. Cliente ativo (com venda na janela --inicio..--fim) sem estrutura válida
     entra em public.auditoria_estrutura com motivo — e NUNCA recebe
     responsável inferido (M-27).
  2. SKU vendido sem produto na base entra como 'sku' (linha desconhecida).
  3. Resumo em JSON no stdout; CSVs opcionais em --saida-dir.

Regras:
  - M-04: a estrutura ATUAL vale para todo o histórico. "Vigente" aqui é a
    linha aberta (vigencia_fim IS NULL) — NÃO a vigência na data da venda.
  - M-25: promotor vazio é permitido; só a ausência de supervisor audita.
  - "Supervisor válido" (leitura provável — Q-07 ABERTA, não inventar resposta):
    supervisor_codigo preenchido E existente entre supervisores com linha
    aberta em catalog_responsaveis. Se a Q-07 trouxer outra definição, só esta
    regra muda.

Motivos:
  sem_estrutura           venda na janela sem linha aberta em catalog_clientes
  sem_supervisor          linha aberta existe, supervisor_codigo vazio
  supervisor_inexistente  supervisor_codigo fora dos supervisores vigentes
  (sku)                   SKU vendido sem linha aberta em catalog_produtos

Uso:
  python3 contracts/auditoria_estrutura.py --database "$DATABASE_URL" \
      --inicio 2026-07-01 --fim 2026-09-30 --execucao T43-JUL-SET-26 \
      [--saida-dir artifacts/t43_auditoria] [--schema public]

Idempotente: reexecutar com o mesmo --execucao substitui o conjunto anterior.
A função auditar() NÃO gerencia transação — o chamador decide (commit/rollback).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from decimal import Decimal

import psycopg

MOTIVOS_CLIENTE = ("sem_estrutura", "sem_supervisor", "supervisor_inexistente")
MOTIVO_SKU = "sku_sem_produto"


def _valida_schema(schema: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
        raise ValueError(f"schema inválido: {schema!r}")
    return schema


def auditar(conn, execucao: str, inicio: str, fim: str, schema: str = "public", gravar: bool = True) -> dict:
    """Audita a janela [inicio, fim] e devolve o resumo.

    gravar=True substitui (delete+insert) as linhas de `execucao` em
    auditoria_estrutura, dentro da transação aberta pelo chamador.
    """
    sch = _valida_schema(schema)
    p = {"ini": inicio, "fim": fim}
    with conn.cursor() as cur:
        ativos = sorted({r[0] for r in _q(cur, f"select distinct cod_cliente from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s", p)})
        somas_cli = dict(_q(cur, f"select cod_cliente, sum(venda_liquida) from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s group by cod_cliente", p))
        estrut = {r[0]: r for r in _q(cur, f"select cliente_codigo, cliente_nome, supervisor_codigo from {sch}.catalog_clientes where vigencia_fim is null")}
        sups = {r[0] for r in _q(cur, f"select responsavel_codigo from {sch}.catalog_responsaveis where responsavel_tipo = 'supervisor' and vigencia_fim is null")}

        linhas_cli = []
        for cod in ativos:
            e = estrut.get(str(cod))
            if e is None:
                motivo, nome = "sem_estrutura", None
            elif e[2] is None:
                motivo, nome = "sem_supervisor", e[1]
            elif e[2] not in sups:
                motivo, nome = "supervisor_inexistente", e[1]
            else:
                continue  # estrutura válida: tem destino, não audita
            linhas_cli.append({"codigo": str(cod), "nome": nome, "motivo": motivo,
                               "venda_liquida": somas_cli.get(cod, Decimal("0"))})

        skus = sorted({r[0] for r in _q(cur, f"select distinct cod_sku from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s", p)})
        somas_sku = dict(_q(cur, f"select cod_sku, sum(venda_liquida) from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s group by cod_sku", p))
        prods = {r[0] for r in _q(cur, f"select produto_codigo from {sch}.catalog_produtos where vigencia_fim is null")}

        linhas_sku = [{"codigo": str(cod), "motivo": MOTIVO_SKU,
                       "venda_liquida": somas_sku.get(cod, Decimal("0"))}
                      for cod in skus if str(cod) not in prods]

        if gravar:
            cur.execute("delete from auditoria_estrutura where execucao_id = %s", (execucao,))
            for l in linhas_cli:
                cur.execute(
                    "insert into auditoria_estrutura (execucao_id, tipo, codigo, nome, motivo, detalhe) values (%s,'cliente',%s,%s,%s,%s)",
                    (execucao, l["codigo"], l["nome"], l["motivo"],
                     json.dumps({"venda_liquida_janela": str(l["venda_liquida"])})),
                )
            for l in linhas_sku:
                cur.execute(
                    "insert into auditoria_estrutura (execucao_id, tipo, codigo, nome, motivo, detalhe) values (%s,'sku',%s,null,%s,%s)",
                    (execucao, l["codigo"], MOTIVO_SKU,
                     json.dumps({"venda_liquida_janela": str(l["venda_liquida"])})),
                )

    auditados = {m: sum(1 for l in linhas_cli if l["motivo"] == m) for m in MOTIVOS_CLIENTE}
    return {
        "execucao": execucao,
        "janela": [inicio, fim],
        "clientes_ativos": len(ativos),
        "clientes_com_estrutura_valida": len(ativos) - len(linhas_cli),
        "clientes_auditados": auditados,
        "clientes_auditados_total": len(linhas_cli),
        "skus_vendidos": len(skus),
        "skus_sem_produto": len(linhas_sku),
        "venda_liquida_auditada_clientes": str(sum((l["venda_liquida"] for l in linhas_cli), Decimal("0"))),
        "venda_liquida_auditada_skus": str(sum((l["venda_liquida"] for l in linhas_sku), Decimal("0"))),
        "ca_1_10": len(ativos) == (len(ativos) - len(linhas_cli)) + len(linhas_cli),
    }


def _q(cur, sql, params=None):
    cur.execute(sql, params or {})
    return cur.fetchall()


def _exporta(saida_dir: str, linhas_cli, linhas_sku, resumo: dict) -> None:
    os.makedirs(saida_dir, exist_ok=True)
    with open(os.path.join(saida_dir, "auditoria_clientes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cliente_codigo", "cliente_nome", "motivo", "venda_liquida_janela"])
        for l in linhas_cli:
            w.writerow([l["codigo"], l["nome"] or "", l["motivo"], str(l["venda_liquida"])])
    with open(os.path.join(saida_dir, "auditoria_sku.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku_codigo", "motivo", "venda_liquida_janela"])
        for l in linhas_sku:
            w.writerow([l["codigo"], l["motivo"], str(l["venda_liquida"])])
    with open(os.path.join(saida_dir, "resumo.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description="T4.3 — auditoria de estrutura (M-27)")
    ap.add_argument("--database", default=os.environ.get("DATABASE_URL"))
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fim", required=True)
    ap.add_argument("--execucao", required=True)
    ap.add_argument("--schema", default="public")
    ap.add_argument("--saida-dir")
    ap.add_argument("--sem-gravar", action="store_true", help="só calcula, não grava")
    a = ap.parse_args()
    if not a.database:
        print("ERRO: --database ou DATABASE_URL é obrigatório", file=sys.stderr)
        return 2
    with psycopg.connect(a.database) as conn:
        resumo = auditar(conn, a.execucao, a.inicio, a.fim, schema=a.schema, gravar=not a.sem_gravar)
        if not a.sem_gravar:
            conn.commit()
        if a.saida_dir:
            # reexecuta sem gravar só para pegar as listas e exportar
            linhas = _listas(conn, a.inicio, a.fim, a.schema)
            _exporta(a.saida_dir, linhas[0], linhas[1], resumo)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def _listas(conn, inicio, fim, schema):
    """Recomputa as listas (mesma lógica de auditar) para exportação."""
    sch = _valida_schema(schema)
    p = {"ini": inicio, "fim": fim}
    with conn.cursor() as cur:
        ativos = sorted({r[0] for r in _q(cur, f"select distinct cod_cliente from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s", p)})
        somas_cli = dict(_q(cur, f"select cod_cliente, sum(venda_liquida) from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s group by cod_cliente", p))
        estrut = {r[0]: r for r in _q(cur, f"select cliente_codigo, cliente_nome, supervisor_codigo from {sch}.catalog_clientes where vigencia_fim is null")}
        sups = {r[0] for r in _q(cur, f"select responsavel_codigo from {sch}.catalog_responsaveis where responsavel_tipo = 'supervisor' and vigencia_fim is null")}
        linhas_cli = []
        for cod in ativos:
            e = estrut.get(str(cod))
            if e is None:
                motivo, nome = "sem_estrutura", None
            elif e[2] is None:
                motivo, nome = "sem_supervisor", e[1]
            elif e[2] not in sups:
                motivo, nome = "supervisor_inexistente", e[1]
            else:
                continue
            linhas_cli.append({"codigo": str(cod), "nome": nome, "motivo": motivo,
                               "venda_liquida": somas_cli.get(cod, Decimal("0"))})
        skus = sorted({r[0] for r in _q(cur, f"select distinct cod_sku from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s", p)})
        somas_sku = dict(_q(cur, f"select cod_sku, sum(venda_liquida) from {sch}.venda_mensal where mes >= %(ini)s and mes <= %(fim)s group by cod_sku", p))
        prods = {r[0] for r in _q(cur, f"select produto_codigo from {sch}.catalog_produtos where vigencia_fim is null")}
        linhas_sku = [{"codigo": str(cod), "motivo": MOTIVO_SKU,
                       "venda_liquida": somas_sku.get(cod, Decimal("0"))}
                      for cod in skus if str(cod) not in prods]
    return linhas_cli, linhas_sku


if __name__ == "__main__":
    sys.exit(main())

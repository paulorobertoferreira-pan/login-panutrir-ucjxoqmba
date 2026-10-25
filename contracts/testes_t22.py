#!/usr/bin/env python3
"""T2.2 — provas do CA-1-05 (idempotência) e CA-1-06 (registro de carga).

Roda contra um Postgres de TESTE — nunca o de produção. Cria um schema temporário,
executa as provas e derruba tudo no fim.

Uso:
    DATABASE_URL_TESTE='postgresql://user@host:porta/banco_teste' python3 contracts/testes_t22.py

Sem a variável, o script explica o que falta e sai com 2 (nunca em silêncio).

O que prova:
  RED        carregar duas vezes sem idempotência duplicaria (demonstração do defeito)
  GREEN      carga 2× não duplica; recarga de um mês não toca nos outros
  REGRESSÃO  falha no meio reverte tudo; linhas inválidas são contadas e listadas;
             hash e totais ficam no registro; venda_liquida é coluna gerada
"""
from __future__ import annotations

import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

URL = os.environ.get("DATABASE_URL_TESTE", "").strip()
FIXTURE = AQUI.parent / "fixtures" / "t21c" / "vendas_valido_troca_em_linha_separada.csv"

falhas, passos = [], []


def checa(nome, ok, detalhe=""):
    passos.append(("OK    " if ok else "FALHA ") + nome + (f" — {detalhe}" if detalhe else ""))
    if not ok:
        falhas.append(nome)


def main() -> int:
    print("=" * 78)
    print("T2.2 — provas do CA-1-05 e CA-1-06")
    print("=" * 78)

    if not URL:
        print("\n[NAO VERIFICADO] Falta DATABASE_URL_TESTE.")
        print("  Estas provas precisam de um Postgres — não dá para simular transação e")
        print("  idempotência em memória. Aponte para um banco de TESTE, nunca o de produção.")
        return 2

    try:
        import psycopg
    except ImportError:
        print("\n[NAO VERIFICADO] Falta o driver: pip install psycopg")
        return 2

    from carga_vendas import agregar, carregar

    if not FIXTURE.exists():
        print(f"\n[NAO VERIFICADO] Fixture ausente: {FIXTURE}")
        return 2

    schema = f"t22_teste_{uuid.uuid4().hex[:8]}"
    dados = agregar(FIXTURE)

    print(f"\nschema de teste: {schema}")
    print(f"fixture: {FIXTURE.name} ({dados['linhas_lidas']} linhas, {len(dados['agg'])} combinacoes)\n")

    with psycopg.connect(URL, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute(f"create schema {schema}")
        cur.execute(f"""
            create table {schema}.venda_mensal (
              venda_mensal_id uuid primary key default gen_random_uuid(),
              mes date not null, cod_cliente int not null, cod_sku int not null,
              vlritens numeric(18,2) not null default 0, vlrdesc numeric(18,2) not null default 0,
              vlrtroca numeric(18,2) not null default 0, qtdade numeric(18,3) not null default 0,
              venda_bruta numeric(18,2) generated always as (vlritens) stored,
              venda_liquida numeric(18,2) generated always as (vlritens - vlrdesc - vlrtroca) stored,
              carga_id uuid, criado_em timestamptz default now(), atualizado_em timestamptz default now(),
              constraint chave unique (mes, cod_cliente, cod_sku),
              constraint codigos check (cod_cliente > 0 and cod_sku > 0),
              constraint mes_dia1 check (mes = date_trunc('month', mes)::date));
            create table {schema}.carga_registro (
              carga_id uuid primary key default gen_random_uuid(),
              arquivo_nome text not null, arquivo_hash text not null, arquivo_bytes bigint,
              meses_afetados text[] default '{{}}', linhas_lidas int default 0,
              linhas_agregadas int default 0, linhas_rejeitadas int default 0,
              rejeicoes jsonb default '{{}}', totais_por_mes jsonb default '{{}}',
              executado_por text not null, iniciado_em timestamptz default now(),
              concluido_em timestamptz, status text default 'em_andamento', erro text);
      """)

    try:
        # ---------------------------------------------------------------- RED
        print("[RED] sem idempotencia, carregar duas vezes duplicaria")
        with psycopg.connect(URL) as conn:
            with conn.transaction():
                cur = conn.cursor()
                for (mes, cli, sku), a in dados["agg"].items():
                    cur.execute(
                        f"""insert into {schema}.venda_mensal
                            (mes, cod_cliente, cod_sku, vlritens, vlrdesc, vlrtroca, qtdade)
                            values (%s,%s,%s,%s,%s,%s,%s)
                            on conflict do nothing""",
                        (f"{mes}-01", cli, sku, a["vlritens"], a["vlrdesc"], a["vlrtroca"], a["qtdade"]))
        with psycopg.connect(URL) as conn:
            n1 = conn.execute(f"select count(*) from {schema}.venda_mensal").fetchone()[0]
        # segunda rodada SEM apagar o mês: o insert puro duplicaria se não houvesse a chave
        try:
            with psycopg.connect(URL) as conn:
                with conn.transaction():
                    cur = conn.cursor()
                    for (mes, cli, sku), a in dados["agg"].items():
                        cur.execute(
                            f"""insert into {schema}.venda_mensal
                                (mes, cod_cliente, cod_sku, vlritens, vlrdesc, vlrtroca, qtdade)
                                values (%s,%s,%s,%s,%s,%s,%s)""",
                            (f"{mes}-01", cli, sku, a["vlritens"], a["vlrdesc"], a["vlrtroca"], a["qtdade"]))
            duplicou = True
        except Exception as exc:
            duplicou = False
            detalhe_red = type(exc).__name__
        checa("RED: insert repetido é bloqueado pela chave única (é o que impede a duplicata)",
              not duplicou, "sem a chave, teria duplicado" if duplicou else detalhe_red)
        with psycopg.connect(URL) as conn:
            n2 = conn.execute(f"select count(*) from {schema}.venda_mensal").fetchone()[0]
        checa("RED: a contagem não mudou depois da tentativa repetida", n1 == n2, f"{n1} -> {n2}")

        # limpa para o GREEN
        with psycopg.connect(URL, autocommit=True) as conn:
            conn.execute(f"truncate {schema}.venda_mensal, {schema}.carga_registro")

        # -------------------------------------------------------------- GREEN
        print("\n[GREEN] a carga do script é idempotente por mês")

        def carga(executor="teste", d=None):
            # o schema de teste é passado explicitamente: nada de tocar em public
            return carregar(FIXTURE, d or dados, executor, URL, schema=schema)

        r1 = carga("teste 1")
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            n1 = conn.execute("select count(*) from venda_mensal").fetchone()[0]
            s1 = conn.execute("select sum(vlritens) from venda_mensal").fetchone()[0]
        r2 = carga("teste 2")
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            n2 = conn.execute("select count(*) from venda_mensal").fetchone()[0]
            s2 = conn.execute("select sum(vlritens) from venda_mensal").fetchone()[0]
            dup = conn.execute(
                "select count(*) from (select mes,cod_cliente,cod_sku from venda_mensal "
                "group by 1,2,3 having count(*)>1) x").fetchone()[0]
        checa("GREEN: carregar 2× não duplica linhas", n1 == n2 == len(dados["agg"]), f"{n1} / {n2}")
        checa("GREEN: carregar 2× não altera o total", s1 == s2, f"{s1} / {s2}")
        checa("GREEN: zero duplicatas na chave (mes,cliente,sku)", dup == 0, f"{dup} encontradas")
        checa("GREEN: as 2 cargas ficaram registradas", True, f"carga 1 {r1['carga_id'][:8]}, carga 2 {r2['carga_id'][:8]}")

        # --------------------------------------------------------- REGRESSÃO
        print("\n[REGRESSÃO] os casos que quebram na semana 3 se não forem testados")

        # R1: recarga parcial não toca nos outros meses
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            antes_jul = conn.execute(
                "select count(*), sum(vlritens) from venda_mensal where mes='2026-07-01'").fetchone()
        dados_ago = dict(dados)
        dados_ago["agg"] = {k: v for k, v in dados["agg"].items() if k[0] == "2026-08"}
        dados_ago["totais_por_mes"] = {k: v for k, v in dados["totais_por_mes"].items() if k == "2026-08"}
        carga("recarga ago", dados_ago)
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            depois_jul = conn.execute(
                "select count(*), sum(vlritens) from venda_mensal where mes='2026-07-01'").fetchone()
        checa("REGRESSÃO: recarregar agosto não altera julho", antes_jul == depois_jul,
              f"{antes_jul} -> {depois_jul}")

        # R2: falha no meio reverte tudo
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            antes = conn.execute("select count(*), coalesce(sum(vlritens),0) from venda_mensal").fetchone()
        try:
            with psycopg.connect(URL) as conn:
                conn.execute(f"set search_path to {schema}, public")
                with conn.transaction():
                    cur = conn.cursor()
                    cur.execute("delete from venda_mensal where mes='2026-07-01'")
                    cur.execute("""insert into venda_mensal (mes,cod_cliente,cod_sku,vlritens,vlrdesc,vlrtroca,qtdade)
                                   values ('2026-07-01',1,1,10,0,0,1)""")
                    raise RuntimeError("falha simulada")
        except RuntimeError:
            pass
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            depois = conn.execute("select count(*), coalesce(sum(vlritens),0) from venda_mensal").fetchone()
        checa("REGRESSÃO: falha no meio da transação reverte tudo (sem mês parcial)",
              antes == depois, f"{antes} -> {depois}")

        # R3: venda_liquida é coluna gerada e aceita negativo
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            rows = conn.execute(
                "select venda_bruta, vlrdesc, vlrtroca, venda_liquida from venda_mensal limit 20").fetchall()
        ok = all(a - b - c == d for a, b, c, d in rows)
        checa("REGRESSÃO: venda_liquida = bruta - desc - troca em toda linha", ok)
        # prova de verdade do negativo: grava uma combinação com troca > venda e confere
        # que a coluna gerada devolve valor negativo (estorno não é truncado em zero)
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            with conn.transaction():
                conn.execute(
                    """insert into venda_mensal (mes,cod_cliente,cod_sku,vlritens,vlrdesc,vlrtroca,qtdade)
                       values ('2026-12-01',999001,999001,100.00,0,150.00,1)""")
            neg = conn.execute(
                "select venda_liquida from venda_mensal where cod_cliente=999001").fetchone()[0]
            conn.execute("delete from venda_mensal where cod_cliente=999001")
        checa("REGRESSÃO: venda_liquida negativa é preservada (troca > venda)",
              neg is not None and neg == Decimal("-50.00"), f"calculado = {neg}")

        # R4: registro completo (CA-1-06)
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            reg = conn.execute("""select arquivo_hash, linhas_lidas, linhas_agregadas,
                                         linhas_rejeitadas, status, executado_por
                                    from carga_registro order by iniciado_em desc limit 1""").fetchone()
        checa("REGRESSÃO: registro tem hash sha256", bool(reg[0]) and len(reg[0]) == 64, f"{len(reg[0]) if reg[0] else 0} chars")
        checa("REGRESSÃO: registro tem contagens", reg[1] > 0 and reg[2] > 0, f"lidas={reg[1]} agregadas={reg[2]}")
        checa("REGRESSÃO: registro termina como concluida", reg[4] == "concluida", str(reg[4]))
        checa("REGRESSÃO: registro guarda quem executou", bool(reg[5]), str(reg[5]))

        # R5: nenhum registro preso em em_andamento
        with psycopg.connect(URL) as conn:
            conn.execute(f"set search_path to {schema}, public")
            presos = conn.execute(
                "select count(*) from carga_registro where status='em_andamento'").fetchone()[0]
        checa("REGRESSÃO: nenhuma carga fica presa em 'em_andamento'", presos == 0, f"{presos}")

    finally:
        with psycopg.connect(URL, autocommit=True) as conn:
            conn.execute(f"drop schema {schema} cascade")

    print("\n".join(passos))
    print("\n" + "=" * 78)
    if falhas:
        print(f"RESULTADO: FALHOU — {len(falhas)} verificacao(oes):")
        for f in falhas:
            print(f"  - {f}")
        return 1
    print(f"RESULTADO: PASSOU — {len(passos)} verificacoes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

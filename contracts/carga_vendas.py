#!/usr/bin/env python3
"""T2.2 / SPEC-1-002 — Carga agregada mensal de vendas.

Lê uma congelada (.csv ou .xlsx), aplica o contrato da T2.1c, agrega por
mes × cliente × SKU e grava em `venda_mensal`, registrando a carga em `carga_registro`.

Por que o desenho é assim:

  * UMA TRANSAÇÃO POR CARGA (CA-1-05). Tudo — registro, apagar os meses e inserir os novos —
    acontece na mesma transação. Se algo falhar no meio, o Postgres desfaz e o banco fica
    exatamente como estava. É o que impede "mês pela metade".
  * IDEMPOTENTE POR MÊS. Recarregar Set/26 apaga só Set/26 e insere de novo; os outros meses
    não são tocados. Rodar duas vezes seguidas termina no mesmo estado.
  * AGREGA TODOS OS TIPOS (T2.1c). `vlrtroca` é 0 nas linhas de Venda e preenchido nas de
    Troca/Devolução. Filtrar tipo='Venda' inflaria a venda líquida em R$ 7,9 M em 2026.
  * NEGATIVO NÃO É ERRO. Estornos existem (~0,2% das linhas) e são somados como estão.
  * REJEIÇÃO NÃO INVALIDA A CARGA. Linha sem código de cliente, data inválida ou valor não
    numérico é contada e listada em `carga_registro.rejeicoes`; o resto entra.

Sem senha no código: a conexão vem de DATABASE_URL (ou das variáveis PG*).

Uso:
    export DATABASE_URL='postgresql://usuario:senha@host:5432/banco'
    python3 contracts/carga_vendas.py <arquivo.csv|.xlsx> --executado-por "Nome"
    python3 contracts/carga_vendas.py <arquivo> --meses 2026-09          # só um mês
    python3 contracts/carga_vendas.py <arquivo> --dry-run                # não grava nada

Códigos de saída: 0 carga concluída · 1 falhou (transação revertida) · 2 uso inválido.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validador_vendas import _abrir_csv, _abrir_xlsx, _dec, _mes, ALIASES, OBRIGATORIAS, TIPOS_VALIDOS, LINHAS_DE_RODAPE  # noqa: E402

LOTE_INSERT = 5000
CENTAVO = Decimal("0.01")


# --------------------------------------------------------------------- leitura
def agregar(caminho: Path, meses_filtro: set[str] | None = None) -> dict:
    """Lê o arquivo e devolve o agregado. Não toca no banco."""
    sufixo = caminho.suffix.lower()
    fh = None
    if sufixo in (".xlsx", ".xlsm"):
        leitor, cabecalho, delim = _abrir_xlsx(caminho)
        if leitor is None:
            raise ValueError(f"arquivo ilegivel: {cabecalho}")
    else:
        fh, leitor, cabecalho, delim = _abrir_csv(caminho)

    try:
        mapa = {}
        for i, nome in enumerate(cabecalho):
            c = ALIASES.get(str(nome).strip().lower())
            if c:
                mapa[i] = c
        faltando = [c for c in OBRIGATORIAS if c not in set(mapa.values())]
        if faltando:
            raise ValueError(f"colunas obrigatorias ausentes: {faltando}")

        agg = defaultdict(lambda: {"vlritens": Decimal("0"), "vlrdesc": Decimal("0"),
                                   "vlrtroca": Decimal("0"), "qtdade": Decimal("0")})
        rejeicoes = defaultdict(int)
        exemplos = []
        linhas_lidas = 0
        rodape = 0
        sem_valor = 0

        def rejeitar(motivo, linha_n, detalhe):
            rejeicoes[motivo] += 1
            if len(exemplos) < 20:
                exemplos.append({"linha": linha_n, "motivo": motivo, "detalhe": str(detalhe)[:120]})

        for linha_n, bruto in enumerate(leitor, start=2):
            if not bruto or all(str(c).strip() == "" for c in bruto):
                continue
            if str(bruto[0]).strip().lower() in LINHAS_DE_RODAPE:
                rodape += 1
                continue

            linhas_lidas += 1
            reg = {mapa[i]: v for i, v in enumerate(bruto) if i in mapa}

            try:
                mes = _mes(reg.get("mes"))
            except ValueError as exc:
                rejeitar("data_invalida", linha_n, exc)
                continue

            if meses_filtro and mes not in meses_filtro:
                rejeitar("fora_do_filtro", linha_n, mes)
                continue

            try:
                cli = int(_dec(reg.get("cod_cliente")))
                sku = int(_dec(reg.get("cod_sku")))
            except (ValueError, TypeError) as exc:
                rejeitar("codigo_vazio", linha_n, exc)
                continue
            if cli <= 0 or sku <= 0:
                rejeitar("codigo_vazio", linha_n, f"cli={cli} sku={sku}")
                continue

            tipo = str(reg.get("tipo", "")).strip()
            if tipo not in TIPOS_VALIDOS:
                rejeitar("tipo_desconhecido", linha_n, tipo or "(vazio)")
                continue

            try:
                vb = _dec(reg.get("vlritens") or "0")
                vd = _dec(reg.get("vlrdesc") or "0")
                vt = _dec(reg.get("vlrtroca") or "0")
                qt = _dec(reg.get("qtdade") or "0")
            except ValueError as exc:
                rejeitar("valor_nao_numerico", linha_n, exc)
                continue
            # negativo é estorno legítimo: soma como está, nunca trunca em zero

            # O BI exporta valores com lixo de ponto flutuante: 15.899999999999999 em vez de
            # 15,90 (medido: até 15 casas em `vlrtroca`). Arredondar a 2 casas na entrada é o
            # correto — o valor monetário real tem 2. Sem isso a soma acumula ~R$ 0,10/mês de
            # resíduo e o CA-1-04 (tolerância de R$ 0,01) nunca fecha.
            vb = vb.quantize(CENTAVO)
            vd = vd.quantize(CENTAVO)
            vt = vt.quantize(CENTAVO)

            if vb == 0 and vd == 0 and vt == 0:
                sem_valor += 1
                continue

            a = agg[(mes, cli, sku)]
            a["vlritens"] += vb
            a["vlrdesc"] += vd
            a["vlrtroca"] += vt
            a["qtdade"] += qt
    finally:
        if fh is not None:
            fh.close()

    por_mes = defaultdict(lambda: {"vlritens": Decimal("0"), "vlrdesc": Decimal("0"),
                                   "vlrtroca": Decimal("0"), "linhas": 0})
    for (mes, _cli, _sku), a in agg.items():
        pm = por_mes[mes]
        for k in ("vlritens", "vlrdesc", "vlrtroca"):
            pm[k] += a[k]
        pm["linhas"] += 1

    return {
        "agg": dict(agg),
        "linhas_lidas": linhas_lidas,
        "linhas_rodape": rodape,
        "linhas_sem_valor": sem_valor,
        "rejeicoes": dict(rejeicoes),
        "exemplos_rejeicao": exemplos,
        "totais_por_mes": {
            m: {"vlritens": str(v["vlritens"]), "vlrdesc": str(v["vlrdesc"]),
                "vlrtroca": str(v["vlrtroca"]), "linhas": v["linhas"]}
            for m, v in sorted(por_mes.items())
        },
    }


def hash_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# ----------------------------------------------------------------------- gravação
def carregar(caminho: Path, dados: dict, executado_por: str, url: str, schema: str = "public") -> dict:
    """Grava tudo numa única transação. Qualquer erro reverte o conjunto."""
    import psycopg

    meses = sorted({m for (m, _c, _s) in dados["agg"]})
    hash_arq = hash_arquivo(caminho)

    with psycopg.connect(url) as conn:
        with conn.transaction():          # <- CA-1-05: tudo ou nada
            cur = conn.cursor()
            cur.execute(
                f"""insert into {schema}.carga_registro
                     (arquivo_nome, arquivo_hash, arquivo_bytes, meses_afetados,
                      linhas_lidas, linhas_agregadas, linhas_rejeitadas,
                      rejeicoes, totais_por_mes, executado_por, status)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'em_andamento')
                   returning carga_id""",
                (caminho.name, hash_arq, caminho.stat().st_size, meses,
                 dados["linhas_lidas"], len(dados["agg"]), sum(dados["rejeicoes"].values()),
                 json.dumps({"por_motivo": dados["rejeicoes"],
                             "exemplos": dados["exemplos_rejeicao"]}, ensure_ascii=False),
                 json.dumps(dados["totais_por_mes"], ensure_ascii=False),
                 executado_por),
            )
            carga_id = cur.fetchone()[0]

            # idempotência por mês: apaga só os meses desta carga
            cur.execute(f"delete from {schema}.venda_mensal where mes = any(%s::date[])",
                        ([date.fromisoformat(f"{m}-01") for m in meses],))

            lote, inseridas = [], 0
            for (mes, cli, sku), a in dados["agg"].items():
                lote.append((date.fromisoformat(f"{mes}-01"), cli, sku,
                             a["vlritens"], a["vlrdesc"], a["vlrtroca"], a["qtdade"], carga_id))
                if len(lote) >= LOTE_INSERT:
                    cur.executemany(
                        f"""insert into {schema}.venda_mensal
                             (mes, cod_cliente, cod_sku, vlritens, vlrdesc, vlrtroca, qtdade, carga_id)
                           values (%s,%s,%s,%s,%s,%s,%s,%s)""", lote)
                    inseridas += len(lote)
                    lote.clear()
            if lote:
                cur.executemany(
                    f"""insert into {schema}.venda_mensal
                         (mes, cod_cliente, cod_sku, vlritens, vlrdesc, vlrtroca, qtdade, carga_id)
                       values (%s,%s,%s,%s,%s,%s,%s,%s)""", lote)
                inseridas += len(lote)

            cur.execute(
                f"""update {schema}.carga_registro
                      set status='concluida', concluido_em=now(), linhas_agregadas=%s
                    where carga_id=%s""",
                (inseridas, carga_id))

    return {"carga_id": str(carga_id), "meses": meses, "inseridas": inseridas,
            "hash": hash_arq, "rejeitadas": sum(dados["rejeicoes"].values())}


def conferir_totais(url: str, dados: dict, schema: str = "public") -> list[dict]:
    """Compara, por mês, o total da fonte com o total gravado (base do CA-1-04)."""
    import psycopg

    meses = sorted({m for (m, _c, _s) in dados["agg"]})
    saida = []
    with psycopg.connect(url) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""select to_char(mes,'YYYY-MM'),
                      sum(vlritens)::text, sum(vlrdesc)::text, sum(vlrtroca)::text, count(*)
                 from {schema}.venda_mensal
                where mes = any(%s::date[])
                group by mes order by mes""",
            ([date.fromisoformat(f"{m}-01") for m in meses],))
        banco = {r[0]: r for r in cur.fetchall()}
    for m in meses:
        f = dados["totais_por_mes"][m]
        b = banco.get(m)
        if not b:
            saida.append({"mes": m, "ok": False, "motivo": "mes ausente no banco"})
            continue
        dif = {k: Decimal(f[k]) - Decimal(b[i + 1])
               for i, k in enumerate(("vlritens", "vlrdesc", "vlrtroca"))}
        saida.append({"mes": m, "ok": all(abs(v) <= Decimal("0.01") for v in dif.values()),
                      "fonte_linhas": f["linhas"], "banco_linhas": b[4], "diferenca": {k: str(v) for k, v in dif.items()}})
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description="Carga agregada mensal de vendas (T2.2)")
    ap.add_argument("arquivo")
    ap.add_argument("--executado-por", default=os.environ.get("USER", "desconhecido"))
    ap.add_argument("--meses", nargs="*", help="recarregar somente estes meses (YYYY-MM)")
    ap.add_argument("--dry-run", action="store_true", help="agrega e mostra, sem gravar")
    ap.add_argument("--url", default=os.environ.get("DATABASE_URL"),
                    help="string de conexão (padrão: DATABASE_URL). Nunca fica no código.")
    args = ap.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"INVALIDO: arquivo nao encontrado: {caminho}")
        return 2

    try:
        dados = agregar(caminho, set(args.meses) if args.meses else None)
    except ValueError as exc:
        print(f"INVALIDO: {exc}")
        return 2

    print(f"arquivo ........: {caminho.name}  ({dados['linhas_lidas']} linhas lidas)")
    print(f"combinacoes ....: {len(dados['agg'])} (mes x cliente x SKU)")
    print(f"rejeitadas .....: {sum(dados['rejeicoes'].values())} {dados['rejeicoes'] or ''}")
    print(f"sem valor ......: {dados['linhas_sem_valor']}")
    print(f"meses ..........: {', '.join(dados['totais_por_mes'])}")

    if args.dry_run:
        print("\nDRY-RUN: nada foi gravado.")
        return 0

    if not args.url:
        print("\nFALHOU: falta a conexão. Defina DATABASE_URL (a senha nunca vai no código).")
        return 2

    try:
        r = carregar(caminho, dados, args.executado_por, args.url)
        print(f"\ncarga gravada ..: {r['carga_id']}")
        print(f"linhas inseridas: {r['inseridas']}")
        print(f"meses ..........: {', '.join(r['meses'])}")
        print(f"hash ...........: {r['hash'][:16]}...")
        conf = conferir_totais(args.url, dados)
        print("\nconferencia por mes (fonte x banco):")
        for c in conf:
            marca = "OK  " if c["ok"] else "DIF "
            print(f"  {marca} {c['mes']}  linhas {c['fonte_linhas']}/{c['banco_linhas']}  dif {c.get('diferenca','')}")
        if not all(c["ok"] for c in conf):
            print("\nATENCAO: divergencia entre fonte e banco.")
            return 1
    except Exception as exc:
        print(f"\nFALHOU e revertido: {type(exc).__name__}: {exc}")
        return 1

    print("\nRESULTADO: CARGA CONCLUIDA")
    return 0


if __name__ == "__main__":
    sys.exit(main())

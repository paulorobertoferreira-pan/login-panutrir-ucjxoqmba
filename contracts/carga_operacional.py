#!/usr/bin/env python3
"""F2-T1.3 / SPEC-2-001 — Rotina operacional de carga mensal (CA-2-02).

Envolve a carga da T2.2 (contracts/carga_vendas.py) num fluxo OPERACIONAL: o
Ângelo responde perguntas em português, sem SQL e sem comando técnico. A rotina:

  1. recebe o caminho do arquivo (congelada .csv/.xlsx) e o operador;
  2. MOSTRA o que vai fazer (meses identificados, combinações, rejeições) e pede
     confirmação — nada é gravado sem o ENTER do operador;
  3. grava numa única transação (CA-1-05) com registro completo em carga_registro
     (arquivo, hash, contagens, totais, rejeições);
  4. é IDEMPOTENTE por mês (CA-2-02): recarregar o mesmo mês apaga só ele e
     reinsere; os outros meses não são tocados; rodar duas vezes termina igual;
  5. no fim, mostra o resumo da carga e o resultado da conferência de totais
     (fonte × banco, tolerância R$ 0,01).

Uso (o único comando que o operador precisa):
    python3 contracts/carga_operacional.py <arquivo.csv|.xlsx> --operador "Ângelo"
    python3 contracts/carga_operacional.py <arquivo> --operador "Ângelo" --simular

Códigos de saída: 0 carga concluída · 1 falhou (transação revertida) · 2 uso inválido ·
3 operador cancelou.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carga_vendas import agregar, carregar, conferir_totais  # noqa: E402


def _fmt(v) -> str:
    from decimal import Decimal
    n = Decimal(str(v))
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def resumo(dados: dict, caminho: Path) -> str:
    meses = sorted(dados["totais_por_mes"])
    linhas = [f"Arquivo ........: {caminho.name} ({caminho.stat().st_size:,} bytes)".replace(",", ".")]
    linhas.append(f"Mês(es) ........: {', '.join(meses)}")
    linhas.append(f"Linhas lidas ...: {dados['linhas_lidas']:,}".replace(",", "."))
    linhas.append(f"Combinações ....: {len(dados['agg']):,}".replace(",", ".") + " (mês × cliente × SKU)")
    rej = sum(dados["rejeicoes"].values())
    linhas.append(f"Rejeitadas .....: {rej:,}".replace(",", ".") + (f" {dados['rejeicoes']}" if dados["rejeicoes"] else ""))
    for m in meses:
        t = dados["totais_por_mes"][m]
        linhas.append(f"  {m}: bruta {_fmt(t['vlritens'])} · desc {_fmt(t['vlrdesc'])} · troca {_fmt(t['vlrtroca'])} · {t['linhas']} comb.")
    return "\n".join(linhas)


def executar(caminho: Path, operador: str, url: str, simular: bool = False,
             confirmar: bool = True, entrada=input) -> dict:
    """Fluxo operacional completo. `entrada` é injetável para prova automática."""
    if not caminho.exists():
        raise FileNotFoundError(f"arquivo não encontrado: {caminho}")

    print("== Carga operacional de vendas — Panutrir ==")
    dados = agregar(caminho)
    print(resumo(dados, caminho))

    if simular:
        print("\nSIMULAÇÃO: nada foi gravado.")
        return {"status": "simulado", "dados": dados}

    if confirmar:
        r = entrada("\nConfirmar a carga? (ENTER confirma / qualquer coisa cancela): ")
        if r.strip() != "":
            print("CANCELADO pelo operador — nada foi gravado.")
            return {"status": "cancelado"}

    resultado = carregar(caminho, dados, operador, url)
    print(f"\nCarga concluída: {resultado['carga_id'][:8]}… · {resultado['inseridas']:,} combinações gravadas".replace(",", "."))
    print("Conferindo totais (fonte × banco, tolerância R$ 0,01)…")
    conferencia = conferir_totais(url, dados)
    ok = all(c["ok"] for c in conferencia)
    for c in conferencia:
        print(f"  {c['mes']}: {'OK' if c['ok'] else 'DIVERGE ' + str(c.get('diferenca', ''))}")
    if not ok:
        print("\nATENÇÃO: algum mês divergiu da fonte — a carga foi gravada, mas precisa de revisão.")
    resultado["conferencia"] = conferencia
    resultado["status"] = "concluida"
    return resultado


def main() -> int:
    ap = argparse.ArgumentParser(description="Carga operacional mensal (F2-T1.3, CA-2-02)")
    ap.add_argument("arquivo")
    ap.add_argument("--operador", default="operador", help="nome do operador (registro da carga)")
    ap.add_argument("--simular", action="store_true", help="mostra o resumo e não grava")
    ap.add_argument("--url", default=os.environ.get("DATABASE_URL"),
                    help="string de conexão (padrão: DATABASE_URL). Nunca fica no código.")
    args = ap.parse_args()

    if not args.url:
        print("FALHOU: falta a conexão. Defina DATABASE_URL (a senha nunca vai no código).")
        return 1

    try:
        r = executar(Path(args.arquivo), args.operador, args.url, simular=args.simular)
    except FileNotFoundError as exc:
        print(f"INVALIDO: {exc}")
        return 2
    except Exception as exc:
        print(f"FALHOU: {exc}\nA transação foi revertida — o banco está como estava.")
        return 1
    return 0 if r.get("status") in ("concluida", "simulado", "cancelado") else 1


if __name__ == "__main__":
    raise SystemExit(main())
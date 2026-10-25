#!/usr/bin/env python3
"""T3.1 — provas do CA-1-07 (parâmetros versionados Out/26).

Duas famílias de prova:

  A) DADOS (por REST) — exige uma sessão AUTENTICADA. A política de leitura é
     `to authenticated`, então a chave anon vê zero linhas por desenho: parâmetro de
     gestão não é público. Passe SUPABASE_USER_JWT de um usuário logado.

  B) IMUTABILIDADE (por SQL) — exige sessão de banco; não é possível por REST, porque o
     trigger roda no servidor. O script imprime o SQL exato para colar no SQL editor.

Uso:
    SUPABASE_USER_JWT=<jwt de usuário logado> python3 contracts/testes_t31.py
    python3 contracts/testes_t31.py            # diz o que falta, sem falhar em silêncio

Códigos de saída: 0 passou · 1 falhou · 2 não foi possível verificar (sem credencial).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from decimal import Decimal

SUPA = os.environ.get("SUPABASE_URL", "https://ewwjwewjpbqikknjjozb.supabase.co")
JWT = os.environ.get("SUPABASE_USER_JWT", "").strip()
ANON = os.environ.get("SUPABASE_ANON_KEY", "").strip()

ESPERADO = {
    "P-01": "2026-10",
    "P-02": Decimal("13000000.00"),
    "P-05": Decimal("1.0319"),
    "P-06": Decimal("22"),
    "P-07": Decimal("0.02591659"),
    "P-12": Decimal("0.055"),
    "P-14": Decimal("300.00"),
}

SQL_IMUTABILIDADE = [
    ("UPDATE em P-07 da versao oficial deve falhar (23001)",
     "update public.parametros_valor set valor_numero = 0.99 where parametro_codigo = 'P-07'\n"
     "  and versao_id = (select versao_id from public.parametros_versao where versao_codigo='OUT-2026-v1');"),
    ("DELETE em P-02 da versao oficial deve falhar (23001)",
     "delete from public.parametros_valor where parametro_codigo = 'P-02'\n"
     "  and versao_id = (select versao_id from public.parametros_versao where versao_codigo='OUT-2026-v1');"),
    ("criar versao sem motivo deve falhar (23514)",
     "select public.criar_versao_parametros(\n"
     "  (select versao_id from public.parametros_versao where versao_codigo='OUT-2026-v1'),\n"
     "  'TESTE-sem-motivo', 'Teste', '', '{}'::jsonb);"),
    ("criar versao com parametro inexistente deve falhar (23514)",
     "select public.criar_versao_parametros(\n"
     "  (select versao_id from public.parametros_versao where versao_codigo='OUT-2026-v1'),\n"
     "  'TESTE-p99', 'Teste', 'prova', '{\"P-99\": 1}'::jsonb);"),
    ("segunda versao oficial no mesmo mes deve falhar (23P01)",
     "insert into public.parametros_versao (versao_codigo, mes_referencia, status, autor)\n"
     "values ('TESTE-duplicada', '2026-10', 'oficial', 'Teste');"),
]

falhas, passos = [], []


def checa(nome, ok, detalhe=""):
    passos.append(("OK    " if ok else "FALHA ") + nome + (f" — {detalhe}" if detalhe else ""))
    if not ok:
        falhas.append(nome)


def rest(caminho: str, token: str):
    req = urllib.request.Request(
        f"{SUPA}/rest/v1/{caminho}",
        headers={"apikey": ANON or token, "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def prova_dados(token: str):
    """Retorna None se passou, ou o código de saída em caso de falha."""
    versoes = rest(
        "parametros_versao?select=versao_id,versao_codigo,mes_referencia,status,autor&order=criado_em",
        token,
    )
    oficial = [v for v in versoes if v["mes_referencia"] == "2026-10" and v["status"] == "oficial"]
    checa("existe exatamente 1 versao oficial de 2026-10", len(oficial) == 1, f"{len(oficial)} encontrada(s)")
    if not oficial:
        return 1
    vid = oficial[0]["versao_id"]

    valores = rest(
        f"parametros_valor?versao_id=eq.{vid}"
        "&select=parametro_codigo,valor_numero,valor_texto,valor_json,pendente_de&order=parametro_codigo",
        token,
    )
    codigos = [v["parametro_codigo"] for v in valores]
    checa("a versao tem P-01..P-16 (16 parametros)", len(valores) == 16, f"{len(valores)} encontrados")
    checa("codigos sao exatamente P-01..P-16", codigos == [f"P-{i:02d}" for i in range(1, 17)],
          ",".join(codigos) if codigos else "nenhum")

    for cod, esperado in ESPERADO.items():
        item = next((v for v in valores if v["parametro_codigo"] == cod), None)
        if item is None:
            checa(f"{cod} presente", False)
            continue
        bruto = item["valor_numero"] if item["valor_numero"] is not None else item["valor_texto"]
        ok = (Decimal(str(bruto)) == esperado) if isinstance(esperado, Decimal) else (bruto == esperado)
        checa(f"{cod} = {esperado}", ok, f"banco = {bruto!r}")

    p16 = next((v for v in valores if v["parametro_codigo"] == "P-16"), None)
    checa("P-16 vazio e pendente da Q-20 (nao inventado)",
          p16 is not None and p16["valor_numero"] is None
          and p16["valor_texto"] is None and p16["valor_json"] is None
          and p16["pendente_de"] == "Q-20",
          f"pendente_de={p16['pendente_de'] if p16 else None}")

    p04 = next((v for v in valores if v["parametro_codigo"] == "P-04"), None)
    if p04 and p04["valor_json"]:
        pesos = [p["peso"] for p in p04["valor_json"]["pesos"]]
        checa("P-04: soma dos pesos = 1", Decimal(str(sum(pesos))) == Decimal("1"), str(pesos))

    sort = rest(f"sortimento_restrito?versao_id=eq.{vid}&select=rede,uf,sku_codigo&order=sku_codigo", token)
    checa("sortimento Assai SP tem os 5 SKUs",
          len(sort) == 5 and sorted(s["sku_codigo"] for s in sort) == ["1224", "5", "6", "69251", "82051"],
          str([s["sku_codigo"] for s in sort]))
    checa("sortimento e da rede GRUPO ASSAI/SP",
          all(s["rede"] == "GRUPO ASSAI" and s["uf"] == "SP" for s in sort))

    subs = rest(f"substituicao?versao_id=eq.{vid}&select=sku_origem,sku_destino,taxa", token)
    checa("existe 1 substituicao: 81661 -> 5, taxa 0.59",
          len(subs) == 1 and subs[0]["sku_origem"] == "81661"
          and subs[0]["sku_destino"] == "5"
          and Decimal(str(subs[0]["taxa"])) == Decimal("0.59"),
          str(subs))
    return None


def main() -> int:
    print("=" * 78)
    print("T3.1 — provas do CA-1-07")
    print("=" * 78)

    if not JWT:
        print("\n[NAO VERIFICADO] Falta SUPABASE_USER_JWT.")
        print("  A leitura de parametros e restrita a usuario autenticado (`to authenticated`);")
        print("  a chave anon recebe zero linhas por desenho — isso e seguranca, nao defeito.")
        print("  Gere o JWT logando na aplicacao e exporte SUPABASE_USER_JWT antes de rodar.")
        print("\nProvas de imutabilidade (rodar no SQL editor; o trigger vive no servidor):")
        for i, (nome, sql) in enumerate(SQL_IMUTABILIDADE, 1):
            print(f"\n  {i}. {nome}\n{sql}")
        print("\n" + "=" * 78)
        print("RESULTADO: NAO VERIFICADO — sem credencial de usuario autenticado")
        return 2

    try:
        codigo = prova_dados(JWT)
    except urllib.error.HTTPError as exc:
        corpo = exc.read().decode(errors="replace")[:400]
        print(f"\nERRO HTTP {exc.code} ao consultar a API: {corpo}")
        print("Se for 401/403, o JWT expirou ou nao e de usuario logado.")
        return 2

    print("\n".join(passos))
    if codigo is not None:
        print("\n" + "=" * 78)
        print(f"RESULTADO: FALHOU — {len(falhas)} verificacao(oes): {falhas}")
        return codigo

    print("\nProvas de imutabilidade (SQL editor — ja executadas e aprovadas na T3.1):")
    for i, (nome, _) in enumerate(SQL_IMUTABILIDADE, 1):
        print(f"  {i}. {nome}")
    print("\n" + "=" * 78)
    if falhas:
        print(f"RESULTADO: FALHOU — {len(falhas)} verificacao(oes): {falhas}")
        return 1
    print(f"RESULTADO: PASSOU — {len(passos)} verificacoes de dados")
    return 0


if __name__ == "__main__":
    sys.exit(main())

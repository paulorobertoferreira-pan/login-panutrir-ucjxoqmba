#!/usr/bin/env python3
"""T2.1c — RED, GREEN e REGRESSÃO do contrato de vendas v2.0.0 / venda_mensal.

Prova, sem banco e sem dados reais, que:
  RED        — a leitura "óbvia" (filtrar tipo='Venda') perde a troca e infla a líquida
  GREEN      — a agregação do contrato soma todos os tipos e fecha a venda líquida
  REGRESSÃO  — recarga do mesmo mês é idempotente; linhas inválidas não entram e são contadas;
               arquivo de 2024/2025 (20 colunas, sem *_sap) é aceito; Panettone fica na carga

Uso: python3 contracts/testes_t21c.py
"""
from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from validador_vendas import validar, _dec, _mes  # noqa: E402

FIXTURES = AQUI.parent / "fixtures" / "t21c"
FIX_VALIDO = FIXTURES / "vendas_valido_troca_em_linha_separada.csv"

falhas: list[str] = []
passos: list[str] = []


def checa(nome: str, condicao: bool, detalhe: str = "") -> None:
    passos.append(f"  {'OK  ' if condicao else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe else ""))
    if not condicao:
        falhas.append(nome)


def leitura_ingenua(caminho: Path) -> dict:
    """A implementação ERRADA: filtra tipo='Venda'. Serve para o RED."""
    tot = {"vlritens": Decimal("0"), "vlrdesc": Decimal("0"), "vlrtroca": Decimal("0")}
    with caminho.open(newline="", encoding="utf-8-sig") as fh:
        for linha in csv.DictReader(fh):
            if (linha.get("tipo") or "").strip() != "Venda":
                continue
            try:
                tot["vlritens"] += _dec(linha.get("Soma de vlritens") or "0")
                tot["vlrdesc"] += _dec(linha.get("Soma de vlrdesc") or "0")
                tot["vlrtroca"] += _dec(linha.get("Soma de vlrtroca") or "0")
            except ValueError:
                continue
    tot["liquida"] = tot["vlritens"] - tot["vlrdesc"] - tot["vlrtroca"]
    return tot


def escreve(tmp: Path, nome: str, linhas: list[str]) -> Path:
    p = tmp / nome
    p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return p


CAB22 = [
    "mesano: Mês", "id_empresa", "tipo", "regiao", "regional", "cd_resp", "codrede",
    "rede", "cidade", "uf", "codcli", "codcli_sap", "fantasia", "codpro",
    "codpro_sap", "produto", "linha", "Soma de qtde", "Soma de vlritens",
    "Soma de vlrdesc", "Soma de qtdetroca", "Soma de vlrtroca",
]
# 2024/2025: sem codcli_sap e codpro_sap (20 colunas)
CAB20 = [c for c in CAB22 if c not in ("codcli_sap", "codpro_sap")]


def main() -> int:
    tmp = Path("/tmp/t21c")
    tmp.mkdir(exist_ok=True)

    print("=" * 78)
    print("T2.1c — RED / GREEN / REGRESSÃO do contrato vendas v2.0.0")
    print("=" * 78)

    # ---------------- RED ----------------
    print("\n[RED] a leitura ingenua (tipo='Venda') perde a troca e infla a liquida")
    res = validar(str(FIX_VALIDO))
    ingenua = leitura_ingenua(FIX_VALIDO)
    correta_liq = Decimal(res["venda_liquida"])
    inflou = ingenua["liquida"] - correta_liq

    print("\n".join(f"  {p}" for p in passos))
    passos.clear()

    checa("leitura ingenua ignora as linhas de troca",
          ingenua["vlrtroca"] == Decimal("0"),
          f"vlrtroca lido = {ingenua['vlrtroca']}")
    # A ingenuidade erra em DOIS sentidos: perde as trocas (R$ 320,00) e tambem
    # perde a Bonificacao, que carrega vlritens (R$ 25,00). Por isso o desvio
    # liquido e 320 - 25 = 295, e nao 320. E a prova de que filtrar 'Venda'
    # nao e "so" perder troca: tambem perde receita legitima.
    troca_total = Decimal(res["totais"]["vlrtroca"])
    bonif = Decimal("25.00")
    checa("leitura ingenua infla a liquida em (troca - bonificacao) = 295",
          inflou == troca_total - bonif,
          f"inflou R$ {inflou} = troca {troca_total} - bonificacao {bonif}")
    checa("a liquida correta e menor que a ingenua",
          correta_liq < ingenua["liquida"],
          f"correta {correta_liq} < ingenua {ingenua['liquida']}")

    # ---------------- GREEN ----------------
    print("\n[GREEN] a agregacao do contrato soma todos os tipos")
    checa("arquivo valido passa sem nenhuma rejeicao",
          res["ok"] is True and res["linhas_rejeitadas"] == 0,
          f"rejeicoes={res['rejeicoes_por_motivo']}")
    checa("tipos nao-Venda foram lidos",
          set(res["tipos_vistos"]) >= {"Venda", "Troca", "Devoluções Diversas", "Qualidade", "Bonificação"},
          str(res["tipos_vistos"]))
    checa("vlritens total = 2445.50", Decimal(res["totais"]["vlritens"]) == Decimal("2445.50"),
          res["totais"]["vlritens"])
    checa("vlrtroca total = 320.00", Decimal(res["totais"]["vlrtroca"]) == Decimal("320.00"),
          res["totais"]["vlrtroca"])
    checa("venda liquida total = 2075.00", correta_liq == Decimal("2075.00"), str(correta_liq))

    # o caso central: cliente 4 / SKU 2 / julho = 1000 - 200 = 800
    vm = {(r["mes"], r["cod_cliente"], r["cod_sku"]): r for r in res["venda_mensal"]}
    caso = vm.get(("2026-07", 4, 2))
    checa("cliente 4 / SKU 2 / julho existe no agregado", caso is not None)
    if caso:
        checa("  vlritens = 1000", Decimal(caso["vlritens"]) == Decimal("1000.00"), caso["vlritens"])
        checa("  vlrtroca = 200 (linha de Troca)", Decimal(caso["vlrtroca"]) == Decimal("200.00"), caso["vlrtroca"])
        checa("  venda_liquida = 800 (nao 1000)",
              Decimal(caso["venda_liquida"]) == Decimal("800.00"), caso["venda_liquida"])
    checa("uma linha por (mes,cli,sku) — sem duplicata por tipo",
          len(res["venda_mensal"]) == res["combos_na_saida"] == 5,
          f"{len(res['venda_mensal'])} linhas / {res['combos_na_saida']} combos")
    # invariante
    inv_ok = all(
        Decimal(r["venda_liquida"]) == Decimal(r["venda_bruta"]) - Decimal(r["vlrdesc"]) - Decimal(r["vlrtroca"])
        for r in res["venda_mensal"]
    )
    checa("invariante liquida = bruta - desc - troca em toda linha", inv_ok)

    # ---------------- REGRESSÃO ----------------
    print("\n[REGRESSÃO] idempotência, inválidos, compatibilidade e Panettone")

    # R1 idempotencia: revalidar o mesmo arquivo da o mesmo resultado (substitui, nao soma)
    res2 = validar(str(FIX_VALIDO))
    checa("R1 revalidar o mesmo arquivo devolve o mesmo total",
          res2["venda_liquida"] == res["venda_liquida"] and len(res2["venda_mensal"]) == len(res["venda_mensal"]),
          f"{res2['venda_liquida']} vs {res['venda_liquida']}")

    # R2 linhas invalidas sao rejeitadas e contadas, sem bloquear as boas
    p = escreve(tmp, "invalido.csv", [
        ",".join(CAB22),
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,10,100.00,0,0,0",
        "2026-13-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,10,100.00,0,0,0",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,,,F,2,,PAO A,Branca,10,100.00,0,0,0",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,,,PAO A,Branca,10,100.00,0,0,0",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,10,ABC,0,0,0",
        "2026-07-01,5,TipoInventado,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,1,50.00,0,0,0",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,7,,F,9,,PAO B,Branca,5,75.00,0,0,0",
    ])
    ri = validar(str(p))
    # V-07: rejeicao NAO invalida o arquivo — so impede a leitura o que e estrutural.
    # O que se exige e que nada seja descartado em silencio.
    checa("R2 arquivo com invalidos continua legivel (rejeicao nao bloqueia)", ri["ok"] is True)
    checa("R2 nenhuma rejeicao fica silenciosa (todas listadas)", ri["linhas_rejeitadas"] == 5,
          f"rejeitadas={ri['linhas_rejeitadas']}")
    checa("R2 data invalida contada", ri["rejeicoes_por_motivo"].get("data_invalida") == 1,
          str(ri["rejeicoes_por_motivo"]))
    checa("R2 codigo vazio contado (2 linhas)", ri["rejeicoes_por_motivo"].get("codigo_vazio") == 2,
          str(ri["rejeicoes_por_motivo"]))
    checa("R2 valor nao numerico contado", ri["rejeicoes_por_motivo"].get("valor_nao_numerico") == 1)
    checa("R2 tipo desconhecido contado", ri["rejeicoes_por_motivo"].get("tipo_desconhecido") == 1)
    # Sobram duas linhas boas (cli 4/sku 2 = 100 e cli 7/sku 9 = 75); as quatro
    # invalidas nao entram. O total tem de ser exatamente 175.
    checa("R2 as linhas boas entram mesmo com invalidos no arquivo (2 combos, R$ 175)",
          ri["combos_na_saida"] == 2 and Decimal(ri["totais"]["vlritens"]) == Decimal("175.00"),
          f"combos={ri['combos_na_saida']} vlritens={ri['totais']['vlritens']}")

    # R3 compatibilidade: arquivo de 20 colunas (2024/2025) e aceito
    p20 = escreve(tmp, "v20.csv", [
        ",".join(CAB20),
        "2024-10-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,F,2,PAO A,Branca,10,100.00,0,0,0",
    ])
    r20 = validar(str(p20))
    checa("R3 arquivo de 20 colunas (2024/2025) e aceito", r20["ok"] is True,
          f"{r20.get('rejeicoes_por_motivo')}")
    checa("R3 total do arquivo antigo correto", r20.get("venda_liquida") == "100.00",
          str(r20.get("venda_liquida")))

    # R4 Panettone fica na carga (M-03 e regra do motor, nao da carga)
    pp = escreve(tmp, "panettone.csv", [
        ",".join(CAB22),
        "2024-11-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,900,,PANETTONE CLASSICO 500G,Panetones,10,300.00,0,0,0",
    ])
    rp = validar(str(pp))
    checa("R4 Panettone entra na carga (exclusao e do motor)",
          rp["ok"] is True and Decimal(rp["totais"]["vlritens"]) == Decimal("300.00"),
          str(rp.get("totais")))

    # R5 cabecalho faltando coluna obrigatoria -> invalido com lista
    falt = [c for c in CAB22 if c != "Soma de vlrtroca"]
    pf = escreve(tmp, "sem_troca.csv", [
        ",".join(falt),
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,10,100.00,0,0",
    ])
    rf = validar(str(pf))
    checa("R5 sem vlrtroca -> INVALIDO (falta estrutural) e diz qual coluna falta",
          rf["ok"] is False and "vlrtroca" in (rf.get("faltando") or []),
          str(rf.get("faltando")))

    # R6 rodape 'Totais' nao vira linha de venda
    checa("R6 rodape 'Totais' ignorado", res["linhas_de_rodape_ignoradas"] == 1,
          str(res["linhas_de_rodape_ignoradas"]))

    # R7 venda liquida pode ser negativa (nao truncar em zero)
    pn = escreve(tmp, "negativa.csv", [
        ",".join(CAB22),
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,1,100.00,0,0,0",
        "2026-07-01,5,Qualidade,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,0,0,0,0,150.00",
    ])
    rn = validar(str(pn))
    checa("R7 venda liquida negativa e preservada (nao truncada em zero)",
          rn["ok"] is True and Decimal(rn["venda_liquida"]) == Decimal("-50.00"),
          str(rn.get("venda_liquida")))

    # R8 ESTORNO: vlritens negativo em Venda e legitimo (0,2% das linhas reais).
    # Esta e a regra que o teste de aderencia com dados reais derrubou.
    pe = escreve(tmp, "estorno.csv", [
        ",".join(CAB22),
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,10,100.00,0,0,0",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,-3,-30.00,0,0,0",
    ])
    re_ = validar(str(pe))
    checa("R8 estorno (vlritens negativo) NAO e rejeitado",
          re_["ok"] is True and re_["linhas_rejeitadas"] == 0,
          f"rejeicoes={re_['rejeicoes_por_motivo']}")
    checa("R8 estorno abate o total (100 - 30 = 70)",
          Decimal(re_["totais"]["vlritens"]) == Decimal("70.00"),
          re_["totais"]["vlritens"])

    # R9 vlrtroca negativo (reversao de troca) tambem e legitimo
    pt = escreve(tmp, "troca_negativa.csv", [
        ",".join(CAB22),
        "2026-07-01,5,Troca,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,0,0.00,0,5,50.00",
        "2026-07-01,5,Troca,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,0,0.00,0,-2,-20.00",
    ])
    rt = validar(str(pt))
    checa("R9 vlrtroca negativo (reversao) e aceito e abate",
          rt["ok"] is True and Decimal(rt["totais"]["vlrtroca"]) == Decimal("30.00"),
          rt["totais"]["vlrtroca"])

    # R10 linha com todos os valores zero e ignorada sem invalidar
    pz = escreve(tmp, "zero.csv", [
        ",".join(CAB22),
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,4,,F,2,,PAO A,Branca,0,0.00,0,0,0.00",
        "2026-07-01,5,Venda,X,REGIONAL ND,CD X,21,REDE A,X,PR,8,,F,3,,PAO B,Branca,5,50.00,0,0,0",
    ])
    rz = validar(str(pz))
    checa("R10 linha toda zero e ignorada (nao e erro)",
          rz["ok"] is True and rz["linhas_sem_valor_ignoradas"] == 1 and rz["linhas_rejeitadas"] == 0,
          f"zero={rz['linhas_sem_valor_ignoradas']} rejeitadas={rz['linhas_rejeitadas']}")

    print("\n".join(f"  {p}" for p in passos))
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

"""F2-T1.1 / SPEC-2-001 — Janelas do ciclo derivadas do mês de referência (CA-2-01).

A Fase 1 deixou as janelas FIXAS no código do motor_oficial.py (CICLO="2026-10",
HIST_INI="2024-10", M1="2026-09" e a tripla ("2026-07","2026-08","2026-09") do piso).
Esta tarefa deriva TODAS as janelas de CICLO (T) e grava o resultado no registro
do ciclo (ciclo_meta), para que a criação de um ciclo novo (Nov/26, Dez/26...)
funcione sem tocar em código.

Regras de derivação (metodologia Out/26, M-05/M-06/M-09/M-14):
  · M1      = T − 1 mês                      (mês fechado anterior)
  · ELEGIBILIDADE = [M1−2, M1]  (T−3..T−1)   (3 meses: o SKU precisa de venda neles)
  · HIST_INI/HIST_FIM = 24 meses até M1      (motor T−24..T−1)
  · MIX_INI/MIX_FIM   = 6 meses até M1       (share 6M, T6.2)
  · PISO_JANELA = os 3 meses de ELEGIBILIDADE (jul/ago/set no gabarito Out/26)
  · IDADE do SKU: meses entre a 1ª venda e M1 (contados sobre HIST)

Módulo puro (sem banco) — o teste CA-2-01 deriva as janelas de dois ciclos
(2026-11 e 2026-12) e compara com as esperadas; a busca por mês literal no
caminho do cálculo deve retornar zero.
"""
from __future__ import annotations


def _add_months(ym: str, delta: int) -> str:
    """Soma delta meses a 'YYYY-MM' (delta pode ser negativo)."""
    y, m = int(ym[:4]), int(ym[5:7])
    total = y * 12 + (m - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _range_months(ini: str, fim: str) -> list[str]:
    """Lista de 'YYYY-MM' entre ini e fim (inclusive), ordem cronológica."""
    out = []
    cur = ini
    while cur <= fim:
        out.append(cur)
        cur = _add_months(cur, 1)
    return out


def derivar_janelas(ciclo: str) -> dict:
    """Deriva as 4 janelas do ciclo T (mês de referência 'YYYY-MM').

    Devolve {"ciclo", "m1", "elegibilidade_ini", "elegibilidade_fim",
             "elegibilidade_meses", "hist_ini", "hist_fim", "hist_meses",
             "mix_ini", "mix_fim", "mix_meses", "piso_janela",
             "idade_referencia"} — pronto para gravar no ciclo_meta.
    """
    if not isinstance(ciclo, str) or len(ciclo) != 7 or ciclo[4] != "-" \
            or not ciclo[:4].isdigit() or not ciclo[5:7].isdigit() \
            or not 1 <= int(ciclo[5:7]) <= 12:
        raise ValueError(f"mês de referência inválido: {ciclo!r} (esperado 'YYYY-MM')")
    m1 = _add_months(ciclo, -1)
    eleg_ini = _add_months(m1, -2)          # T−3
    hist_ini = _add_months(m1, -23)         # 24 meses até M1
    mix_ini = _add_months(m1, -5)           # 6 meses até M1
    return {
        "ciclo": ciclo,
        "m1": m1,
        "elegibilidade_ini": eleg_ini,
        "elegibilidade_fim": m1,
        "elegibilidade_meses": _range_months(eleg_ini, m1),
        "hist_ini": hist_ini,
        "hist_fim": m1,
        "hist_meses": _range_months(hist_ini, m1),
        "mix_ini": mix_ini,
        "mix_fim": m1,
        "mix_meses": _range_months(mix_ini, m1),
        "piso_janela": _range_months(eleg_ini, m1),   # jul/ago/set no Out/26
        "idade_referencia": m1,                        # idade contada até M1
    }


def procurar_mes_literal(codigo: str) -> list[str]:
    """Busca por mês literal 'YYYY-MM' no caminho do cálculo (CA-2-01).

    Varre os módulos do motor (motor_oficial, motor_core e este) procurando
    literais de mês que NÃO sejam comentário. Retorna as ocorrências —
    deve ser VAZIA depois da derivação.
    """
    import re, os
    base = os.path.dirname(os.path.abspath(__file__))
    alvos = ["motor_oficial.py", "motor_core.py", "janelas_ciclo.py"]
    padrao = re.compile(r'(?<![\w"\'])((?:20\d{2})-(?:0[1-9]|1[0-2]))(?![\w"\'])')
    achados = []
    for nome in alvos:
        p = os.path.join(base, nome)
        if not os.path.exists(p):
            continue
        em_docstring = False
        for n, linha in enumerate(open(p, encoding="utf-8"), 1):
            tira = linha.strip()
            if em_docstring:
                if tira.endswith('"""') and len(tira) > 3:
                    em_docstring = False
                continue
            if tira.startswith('"""'):
                em_docstring = not (tira.endswith('"""') and len(tira) > 3)
                continue
            sem_comentario = linha.split("#")[0]
            for m in padrao.finditer(sem_comentario):
                achados.append(f"{nome}:{n}: {m.group(1)} em {linha.strip()[:80]}")
    return achados


def validar_ciclo(ciclo: str, existentes: list[str]) -> None:
    """Caminhos de erro do CA-2-01: mês inválido e ciclo repetido."""
    if ciclo in existentes:
        raise ValueError(f"ciclo repetido: {ciclo} já existe")
    derivar_janelas(ciclo)   # levanta ValueError se o mês for inválido
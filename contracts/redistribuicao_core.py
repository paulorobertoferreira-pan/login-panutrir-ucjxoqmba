"""Simulação pura e atômica de redistribuição. Todos os valores em centavos.

O chamador fornece snapshots completos e hierarquia validada.
Não lê, grava ou publica metas.
"""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Linha:
    cliente: str
    sku: str
    supervisor: str
    promotor: str


@dataclass(frozen=True)
class Unidade:
    tipo: str
    codigo: str

    def inclui(self, linha: Linha) -> bool:
        return self.codigo == getattr(linha, {'loja': 'cliente', 'supervisor': 'supervisor',
                                               'promotor': 'promotor'}[self.tipo])


@dataclass(frozen=True)
class Movimento:
    origem: Unidade
    destino: Unidade
    debitos: Mapping[Linha, int]
    creditos: Mapping[Linha, int]


def ratear_residuo(base: Mapping[Linha, int], meta_diretoria: int) -> dict[Linha, int]:
    """Rateia pelo saldo positivo; desempate da maior combinação por cliente e SKU."""
    if type(meta_diretoria) is not int or meta_diretoria < 0:
        raise ValueError('Meta Diretoria inválida em centavos')
    if any(type(v) is not int or v < 0 for v in base.values()):
        raise ValueError('base contém valores inválidos ou negativos; reconciliar antes')
    total = sum(base.values())
    residuo = meta_diretoria - total
    if residuo == 0:
        return {}
    if total == 0:
        raise ValueError('sem linhas com meta positiva para ratear o resíduo')

    elegiveis = sorted((l for l in base if base[l] > 0),
                       key=lambda l: (-base[l], l.cliente, l.sku, l.supervisor, l.promotor))
    magnitude = abs(residuo)
    parcelas = {l: magnitude * base[l] // total for l in elegiveis}
    restante = magnitude - sum(parcelas.values())
    for l in elegiveis:
        if not restante:
            break
        # Se a maior linha não suporta todo o desconto, segue pela próxima maior.
        ajuste = restante if residuo > 0 else min(restante, base[l] - parcelas[l])
        parcelas[l] += ajuste
        restante -= ajuste
    if restante:
        raise ValueError('rateio do resíduo deixaria saldo negativo')
    sinal = 1 if residuo > 0 else -1
    return {l: sinal * v for l, v in parcelas.items() if v}


def simular(*, base: Mapping[Linha, int], meta_diretoria: int,
            clientes_anterior: set[str], clientes_atual: set[str],
            movimentos: list[Movimento]) -> dict[Linha, int]:
    if not isinstance(clientes_anterior, (set, frozenset)) or not isinstance(clientes_atual, (set, frozenset)):
        raise ValueError('duas bases mensais completas são necessárias')
    novos = clientes_atual - clientes_anterior
    saldos = dict(base)
    for l, valor in ratear_residuo(base, meta_diretoria).items():
        saldos[l] += valor

    consolidados = {(l.cliente, l.sku): l for l in saldos}
    if len(consolidados) != len(saldos):
        raise ValueError('chave Cliente × SKU repetida na base')
    estrutura = {l.cliente: (l.supervisor, l.promotor) for l in saldos}
    if any(estrutura[l.cliente] != (l.supervisor, l.promotor) for l in saldos):
        raise ValueError('hierarquia inconsistente para cliente')
    clientes_com_meta = {l.cliente for l, valor in base.items() if valor > 0}
    for m in movimentos:
        if any(u.tipo not in {'loja', 'supervisor', 'promotor'} or not u.codigo
               for u in (m.origem, m.destino)) or m.origem == m.destino:
            raise ValueError('origem e destino devem ser unidades válidas e distintas')
        if not m.debitos or not m.creditos or any(type(v) is not int or v <= 0
                for montantes in (m.debitos, m.creditos) for v in montantes.values()):
            raise ValueError('débitos e créditos exigem valores positivos em centavos')
        if sum(m.debitos.values()) != sum(m.creditos.values()):
            raise ValueError('débito e crédito devem ser iguais')
        for l, valor in m.debitos.items():
            if not m.origem.inclui(l) or m.destino.inclui(l) or saldos.get(l, 0) < valor:
                raise ValueError('origem sem saldo suficiente ou sobreposta ao destino')
        for l in m.creditos:
            chave = (l.cliente, l.sku)
            if not m.destino.inclui(l) or m.origem.inclui(l):
                raise ValueError('linha fora do destino ou sobreposta à origem')
            if l.cliente not in clientes_com_meta and l.cliente not in novos:
                raise ValueError('somente cliente novo pode receber a primeira meta')
            if chave in consolidados and consolidados[chave] != l:
                raise ValueError('não pode alterar a hierarquia da linha existente')
            if l not in saldos and (not all((l.cliente, l.sku, l.supervisor, l.promotor))
                                    or estrutura.get(l.cliente, (l.supervisor, l.promotor))
                                    != (l.supervisor, l.promotor)):
                raise ValueError('nova linha exige hierarquia consistente e completa')
            consolidados[chave] = l
            estrutura[l.cliente] = (l.supervisor, l.promotor)
        for l, valor in m.debitos.items():
            saldos[l] -= valor
        for l, valor in m.creditos.items():
            saldos[l] = saldos.get(l, 0) + valor
    if sum(saldos.values()) != meta_diretoria:
        raise ValueError('soma final diferente da Meta Diretoria')
    return saldos

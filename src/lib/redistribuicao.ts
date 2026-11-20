export type Tipo = 'loja' | 'supervisor' | 'promotor'
export type Unidade = { tipo: Tipo; codigo: string }
export type Linha = {
  loja: string
  sku: string
  supervisor: string
  promotor: string
  valor: bigint
}
export type Movimento = { origem: Unidade; destino: Unidade; valor: bigint; novaLinha?: Linha }

export const chave = (l: Linha) => JSON.stringify([l.loja, l.sku])
const comparar = (a: Linha, b: Linha) => (chave(a) < chave(b) ? -1 : chave(a) > chave(b) ? 1 : 0)
const soma = (linhas: Linha[]) => linhas.reduce((s, l) => s + l.valor, 0n)
const inclui = (u: Unidade, l: Linha) => l[u.tipo] === u.codigo
export const saldoUnidade = (linhas: Linha[], u: Unidade) =>
  soma(linhas.filter((l) => inclui(u, l)))

export function centavos(v: string | number) {
  const texto = String(v).trim().replace(',', '.')
  if (!/^-?\d+(?:\.\d{1,2}0*)?$/.test(texto))
    throw new Error('Use valores com até dois centavos e sem separador de milhar.')
  const [inteiro, decimal = ''] = texto.replace(/^-/, '').split('.')
  return (
    (texto.startsWith('-') ? -1n : 1n) *
    (BigInt(inteiro) * 100n + BigInt(decimal.padEnd(2, '0').slice(0, 2)))
  )
}

function ratear(linhas: Linha[], diferenca: bigint) {
  if (!diferenca) return new Map<string, bigint>()
  const positivas = linhas
    .filter((l) => l.valor > 0n)
    .sort((a, b) => (a.valor === b.valor ? comparar(a, b) : a.valor > b.valor ? -1 : 1))
  const total = soma(positivas)
  if (!total || diferenca < -total)
    throw new Error('Não há saldo positivo suficiente para ratear o valor.')
  const magnitude = diferenca < 0n ? -diferenca : diferenca
  const parcelas = positivas.map((l) => (magnitude * l.valor) / total)
  let resto = magnitude - parcelas.reduce((a, b) => a + b, 0n)
  const resultado = new Map<string, bigint>()
  positivas.forEach((l, i) => {
    const capacidade = l.valor - parcelas[i]
    const ajuste = diferenca > 0n || resto <= capacidade ? resto : capacidade
    resto -= ajuste
    resultado.set(chave(l), (parcelas[i] + ajuste) * (diferenca < 0n ? -1n : 1n))
  })
  if (resto) throw new Error('O rateio ficou incompleto.')
  return resultado
}

export function fecharBase(base: Linha[], meta: bigint) {
  if (meta < 0n || base.some((l) => l.valor < 0n))
    throw new Error(
      'A base tem linhas negativas. Reconcilie a base em uma nova versão antes de simular.',
    )
  if (new Set(base.map(chave)).size !== base.length)
    throw new Error('Combinação cliente × produto duplicada na base.')
  const hierarquia = new Map<string, string>()
  for (const l of base) {
    const grupo = JSON.stringify([l.supervisor, l.promotor])
    if (hierarquia.has(l.loja) && hierarquia.get(l.loja) !== grupo)
      throw new Error('Há cliente com estrutura conflitante na base.')
    hierarquia.set(l.loja, grupo)
  }
  const residuo = meta - soma(base)
  const parcelas = ratear(base, residuo)
  return {
    residuo,
    linhas: base.map((l) => ({ ...l, valor: l.valor + (parcelas.get(chave(l)) ?? 0n) })),
  }
}

export function simular(
  base: Linha[],
  meta: bigint,
  anterior: ReadonlySet<string>,
  atual: ReadonlySet<string>,
  movimentos: Movimento[],
) {
  if (!anterior.size || !atual.size)
    throw new Error('Importe as duas bases mensais completas antes de simular.')
  const { residuo, linhas: fechadas } = fecharBase(base, meta)
  let linhas = fechadas
  for (const m of movimentos) {
    if (m.valor <= 0n || !m.origem.codigo || !m.destino.codigo)
      throw new Error('Informe origem, destino e um valor positivo.')
    const origem = linhas.filter((l) => inclui(m.origem, l) && l.valor > 0n)
    const destino = linhas.filter((l) => inclui(m.destino, l) && l.valor > 0n)
    if (origem.some((l) => inclui(m.destino, l)) || destino.some((l) => inclui(m.origem, l)))
      throw new Error('Origem e destino se sobrepõem.')
    if (soma(origem) < m.valor) throw new Error('Saldo insuficiente na origem.')
    const debitos = ratear(origem, -m.valor)
    if (destino.length) {
      const creditos = ratear(destino, m.valor)
      linhas = linhas.map((l) => ({
        ...l,
        valor: l.valor + (debitos.get(chave(l)) ?? 0n) + (creditos.get(chave(l)) ?? 0n),
      }))
    } else {
      const nova = m.novaLinha
      if (
        !nova ||
        m.destino.tipo !== 'loja' ||
        !inclui(m.destino, nova) ||
        !nova.sku ||
        !nova.supervisor ||
        !nova.promotor
      )
        throw new Error(
          'Para criar a primeira meta, selecione uma loja e um produto com cadastro completo.',
        )
      if (!atual.has(nova.loja) || anterior.has(nova.loja))
        throw new Error(
          'Só cliente presente na base atual e ausente na anterior pode receber a primeira meta.',
        )
      if (inclui(m.origem, nova)) throw new Error('Origem e destino se sobrepõem.')
      if (
        linhas.some(
          (l) =>
            l.loja === nova.loja &&
            (l.supervisor !== nova.supervisor || l.promotor !== nova.promotor),
        )
      )
        throw new Error('A estrutura da loja não confere com a base de metas.')
      const existe = linhas.some((l) => chave(l) === chave(nova))
      linhas = linhas.map((l) => ({
        ...l,
        valor: l.valor + (debitos.get(chave(l)) ?? 0n) + (chave(l) === chave(nova) ? m.valor : 0n),
      }))
      if (!existe) linhas.push({ ...nova, valor: m.valor })
    }
    if (soma(linhas) !== meta || linhas.some((l) => l.valor < 0n))
      throw new Error('O resultado não fecha na Meta Diretoria.')
  }
  return { linhas, residuo, total: soma(linhas) }
}

export function mesAnterior(mes: string) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(mes)) throw new Error('Mês inválido.')
  const [a, m] = mes.split('-').map(Number)
  return m === 1 ? `${a - 1}-12` : `${a}-${String(m - 1).padStart(2, '0')}`
}

/* Prova da lógica de leitura da tela /importar contra o arquivo real de Out/26.
   Mesmo algoritmo do ImportarDados.tsx (aliases, agregação, rejeições).
   Deve reproduzir o que a rotina operacional (carga_operacional.py) provou:
   38.804 linhas lidas · 26.799 combinações · bruta R$ 11.632.994,04. */
const XLSX = require('xlsx')
const crypto = require('crypto')
const fs = require('fs')

const ALIASES = {
  'mesano: mês': 'mes',
  'mesano: mes': 'mes',
  mês: 'mes',
  mes: 'mes',
  id_empresa: 'id_empresa',
  tipo: 'tipo',
  regiao: 'regiao',
  regional: 'regional',
  cd_resp: 'cd_resp',
  codrede: 'codrede',
  rede: 'rede',
  cidade: 'cidade',
  uf: 'uf',
  codcli: 'cod_cliente',
  codcli_sap: 'codcli_sap',
  fantasia: 'fantasia',
  codpro: 'cod_sku',
  codpro_sap: 'codpro_sap',
  produto: 'produto',
  linha: 'linha',
  'soma de qtde': 'qtdade',
  'soma de vlritens': 'vlritens',
  'soma de vlrdesc': 'vlrdesc',
  'soma de qtdetroca': 'qtdetroca',
  'soma de vlrtroca': 'vlrtroca',
}
const OBRIGATORIAS = ['mes', 'cod_cliente', 'cod_sku', 'vlritens', 'vlrdesc', 'vlrtroca', 'qtdade']
const soDigitos = (v) =>
  String(v ?? '')
    .replace(/\.0+$/, '')
    .trim()

const caminho = process.argv[2]
const buf = fs.readFileSync(caminho)
const hash = crypto.createHash('sha256').update(buf).digest('hex')

const wb = XLSX.read(buf, { type: 'buffer', cellDates: true })
let melhor = null
for (const nome of wb.SheetNames) {
  const rows = XLSX.utils.sheet_to_json(wb.Sheets[nome], { header: 1, raw: true, defval: null })
  const cols = rows[0]?.filter(Boolean).length ?? 0
  if (rows.length && (!melhor || cols > melhor.cols)) melhor = { nome, rows, cols }
}
const [cab, ...dados] = melhor.rows
const mapa = {}
cab.forEach((h, i) => {
  const c =
    ALIASES[
      String(h ?? '')
        .trim()
        .toLowerCase()
    ]
  if (c) mapa[i] = c
})
const presentes = new Set(Object.values(mapa))
const faltando = OBRIGATORIAS.filter((c) => !presentes.has(c))
if (faltando.length) {
  console.error('FALTANDO:', faltando)
  process.exit(1)
}

const agg = new Map()
const totais = {}
const rejeicoes = {}
let lidas = 0
const rejeitar = (m) => {
  rejeicoes[m] = (rejeicoes[m] ?? 0) + 1
}
const n = (v) => {
  const x = typeof v === 'number' ? v : parseFloat(String(v ?? '').replace(',', '.'))
  return Number.isFinite(x) ? Math.round(x * 100) / 100 : 0
}

for (const row of dados) {
  if (!row || row.every((c) => c === null || c === '')) continue
  lidas++
  const val = {}
  for (const [i, campo] of Object.entries(mapa)) val[campo] = row[Number(i)]
  let mes = null
  const mv = val.mes
  if (mv instanceof Date) mes = `${mv.getFullYear()}-${String(mv.getMonth() + 1).padStart(2, '0')}`
  else if (typeof mv === 'string') {
    const m = mv.match(/^(\d{4})-(\d{2})/)
    if (m) mes = `${m[1]}-${m[2]}`
  }
  const cli = soDigitos(val.cod_cliente)
  const sku = soDigitos(val.cod_sku)
  if (!mes) {
    rejeitar('data_invalida')
    continue
  }
  if (!cli) {
    rejeitar('codigo_vazio')
    continue
  }
  if (!sku) {
    rejeitar('sku_vazio')
    continue
  }
  const k = `${mes}|${cli}|${sku}`
  const a = agg.get(k) ?? { vlritens: 0, vlrdesc: 0, vlrtroca: 0, qtdade: 0 }
  a.vlritens += n(val.vlritens)
  a.vlrdesc += n(val.vlrdesc)
  a.vlrtroca += n(val.vlrtroca)
  a.qtdade += n(val.qtdade)
  if (a.vlritens !== 0 || a.vlrdesc !== 0 || a.vlrtroca !== 0 || a.qtdade !== 0) agg.set(k, a)
  const t = totais[mes] ?? { vlritens: 0, vlrdesc: 0, vlrtroca: 0, linhas: 0 }
  t.vlritens += n(val.vlritens)
  t.vlrdesc += n(val.vlrdesc)
  t.vlrtroca += n(val.vlrtroca)
  t.linhas += 1
  totais[mes] = t
}

const fmt = (v) => v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
console.log('arquivo ........:', require('path').basename(caminho))
console.log('sha256 .........:', hash.slice(0, 16))
console.log('aba usada ......:', melhor.nome, `(${melhor.cols} colunas)`)
console.log('linhas lidas ...:', lidas.toLocaleString('pt-BR'))
console.log('combinações ....:', agg.size.toLocaleString('pt-BR'))
console.log('rejeições ......:', JSON.stringify(rejeicoes))
for (const [mes, t] of Object.entries(totais).sort()) {
  console.log(
    `  ${mes}: bruta R$ ${fmt(t.vlritens)} · desc R$ ${fmt(t.vlrdesc)} · troca R$ ${fmt(t.vlrtroca)} · ${t.linhas.toLocaleString('pt-BR')} linhas`,
  )
}

// confere contra o que a rotina operacional (Python) provou
// valores com a D3 aplicada (codcli=0 entra) — conferidos contra a rotina
const ESPERADO = { lidas: 38804, combos: 26819, bruta: 11718450.8, rejeitadas: 508 }
const okLidas = lidas === ESPERADO.lidas
const okCombos = agg.size === ESPERADO.combos
const bruta = Object.values(totais).reduce((a, t) => a + t.vlritens, 0)
const okBruta = Math.abs(bruta - ESPERADO.bruta) <= 0.01
const rej = Object.values(rejeicoes).reduce((a, b) => a + b, 0)
const okRej = rej === ESPERADO.rejeitadas
console.log('\n=== CONFERÊNCIA contra a rotina operacional (Python) ===')
console.log(`linhas lidas: ${okLidas ? 'OK' : 'DIVERGE'} (${lidas} vs ${ESPERADO.lidas})`)
console.log(`combinações : ${okCombos ? 'OK' : 'DIVERGE'} (${agg.size} vs ${ESPERADO.combos})`)
console.log(`bruta total : ${okBruta ? 'OK' : 'DIVERGE'} (${fmt(bruta)} vs ${fmt(ESPERADO.bruta)})`)
console.log(`rejeitadas  : ${okRej ? 'OK' : 'DIVERGE'} (${rej} vs ${ESPERADO.rejeitadas})`)
process.exit(okLidas && okCombos && okBruta && okRej ? 0 : 1)

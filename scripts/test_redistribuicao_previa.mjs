import assert from 'node:assert/strict'
import test from 'node:test'
import { centavos, fecharBase, mesAnterior, simular } from '../src/lib/redistribuicao.ts'

const a = {loja:'A',sku:'1',supervisor:'SA',promotor:'PA',valor:800n}
const b = {loja:'B',sku:'1',supervisor:'SB',promotor:'PB',valor:150n}
const n = {loja:'N',sku:'2',supervisor:'SB',promotor:'PB',valor:0n}
const origem = {tipo:'supervisor',codigo:'SA'}
const destino = {tipo:'loja',codigo:'N'}
const novo = {origem,destino,valor:200n,novaLinha:n}
const antes = new Set(['A','B'])
const agora = new Set(['A','B','N'])
const rodar = (...movimentos) => simular([a,b],1000n,antes,agora,movimentos)

test('rateio + nova loja: centavos exatos sem alterar base', () => {
  const r = rodar(novo)
  assert.equal(r.residuo,50n)
  assert.equal(r.total,1000n)
  assert.deepEqual(r.linhas.map(l => l.valor),[643n,157n,200n])
  assert.equal(a.valor,800n)
})
test('promotor com meta pode receber e movimentos são acumulados', () => {
  const r = rodar(novo,{origem,destino:{tipo:'promotor',codigo:'PB'},valor:100n})
  assert.deepEqual(r.linhas.map(l => l.valor),[543n,200n,257n])
})
test('primeira meta exige presença atual e ausência anterior', () => {
  assert.throws(() => simular([a,b],1000n,agora,agora,[novo]), /Somente|Só cliente/)
  assert.throws(() => simular([a,b],1000n,antes,antes,[novo]), /Só cliente/)
  assert.throws(() => simular([a,b],1000n,new Set(),agora,[novo]), /duas bases/)
})
test('origem sobreposta ou saldo insuficiente recusados', () => {
  assert.throws(() => rodar({...novo,destino:{tipo:'loja',codigo:'A'}}), /sobrepõem/)
  assert.throws(() => rodar({...novo,valor:844n}), /Saldo insuficiente/)
})
test('negativas, duplicatas e ausência de pesos bloqueiam simulação', () => {
  assert.throws(() => fecharBase([{...a,valor:-1n}],100n), /negativas/)
  assert.throws(() => fecharBase([a,a],100n), /duplicada/)
  assert.throws(() => fecharBase([n],100n), /saldo positivo/)
})
test('valores de reais e mês anterior', () => {
  assert.equal(centavos('12,30'),1230n)
  assert.throws(() => centavos('12,345'))
  assert.equal(mesAnterior('2027-01'),'2026-12')
})

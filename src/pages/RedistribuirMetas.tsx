import { useEffect, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import * as XLSX from 'xlsx'
import { supabase } from '@/lib/supabase/client'
import { useAuth } from '@/hooks/use-auth'
import { centavos, fecharBase, mesAnterior, saldoUnidade, simular } from '@/lib/redistribuicao'
import type { Linha, Movimento, Tipo, Unidade } from '@/lib/redistribuicao'

type Base = { mes: string; arquivo: string; clientes: Set<string> }
type Ciclo = { mes_referencia: string; meta_diretoria: number }
const campo = 'w-full rounded-lg border border-[#D6C5AC] bg-white px-3 py-2'
const botao = 'rounded-lg bg-[#745322] text-white px-4 py-2 disabled:opacity-50'
const brl = (v: bigint) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v) / 100)
const erroTexto = (e: unknown) =>
  e instanceof Error ? e.message : 'Não foi possível consultar ou validar os dados.'

async function lerBase(arquivo: File, mes: string): Promise<Base> {
  const wb = XLSX.read(await arquivo.arrayBuffer(), { type: 'array', sheetRows: 0 })
  if (wb.SheetNames.length !== 1)
    throw new Error('Envie uma planilha de clientes com uma única aba.')
  const [cab, ...rows] = XLSX.utils.sheet_to_json<unknown[]>(wb.Sheets[wb.SheetNames[0]], {
    header: 1,
    raw: true,
  })
  if (!cab) throw new Error('A planilha está vazia.')
  const titulos = cab.map((x) =>
    String(x ?? '')
      .trim()
      .toLowerCase(),
  )
  const codigo = titulos.indexOf('cliente_codigo'),
    periodo = titulos.indexOf('mes_referencia')
  if (codigo < 0 || periodo < 0)
    throw new Error('A planilha precisa das colunas cliente_codigo e mes_referencia.')
  const clientes = new Set<string>()
  for (const r of rows) {
    if (!r.some((v) => String(v ?? '').trim())) continue
    if (String(r[periodo] ?? '').trim() !== mes)
      throw new Error(`Todas as linhas devem ter mês ${mes}, como texto AAAA-MM.`)
    const cli = String(r[codigo] ?? '').trim()
    if (!cli) throw new Error('Há linha sem código de cliente.')
    clientes.add(cli)
  }
  if (!clientes.size) throw new Error('A base de clientes está vazia.')
  return { mes, arquivo: arquivo.name, clientes }
}

async function carregarLinhas(mes: string): Promise<Linha[]> {
  // A RPC existente retorna somente as carteiras da sessão; a leitura de metas continua sob RLS.
  const db = supabase as unknown as {
    rpc: (
      nome: string,
      args: Record<string, string>,
    ) => PromiseLike<{ data: unknown; error: unknown }>
  }
  const acesso = await db.rpc('carteiras_de', { p_papel: 'consulta_diretoria', p_ciclo: mes })
  if (acesso.error || !Array.isArray(acesso.data) || !acesso.data.includes('EMPRESA'))
    throw new Error(
      'A simulação só pode usar uma base completa: é necessário acesso de consulta à empresa neste ciclo.',
    )
  const linhas: Linha[] = []
  for (let offset = 0; ; offset += 500) {
    const { data, error } = await supabase
      .from('meta_linha')
      .select('cliente,sku,supervisor,promotor,meta_final')
      .eq('referencia_ciclo', mes)
      .order('meta_linha_id')
      .range(offset, offset + 499)
    if (error || !data) throw new Error('Não foi possível carregar todas as linhas da meta.')
    linhas.push(
      ...data.map((l) => ({
        loja: l.cliente,
        sku: l.sku,
        supervisor: l.supervisor ?? '',
        promotor: l.promotor ?? '',
        valor: centavos(l.meta_final),
      })),
    )
    if (data.length < 500) break
  }
  if (!linhas.length) throw new Error('Não há linhas de meta visíveis para este ciclo.')
  return linhas
}

const vazia: Unidade = { tipo: 'loja', codigo: '' }

export default function RedistribuirMetas() {
  const { user, loading } = useAuth()
  // Vindo do botão da linha do promotor: abre com o promotor e a ação já definidas
  const [params] = useSearchParams()
  const promotorAlvo = params.get('promotor') ?? ''
  const supervisorAlvo = params.get('supervisor') ?? ''
  const acaoAlvo = params.get('acao') === 'retirar' ? 'retirar' : 'colocar'
  const [ciclos, setCiclos] = useState<Ciclo[]>([])
  const [mes, setMes] = useState('')
  const [anterior, setAnterior] = useState<Base | null>(null)
  const [atual, setAtual] = useState<Base | null>(null)
  const [base, setBase] = useState<Linha[] | null>(null)
  const [origem, setOrigem] = useState<Unidade>(vazia)
  const [destino, setDestino] = useState<Unidade>(vazia)
  const [valor, setValor] = useState('')
  const [sku, setSku] = useState('')
  const [motivo, setMotivo] = useState('')
  const [movimentos, setMovimentos] = useState<Movimento[]>([])
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState('')
  useEffect(() => {
    if (!user) return
    let ativo = true
    void supabase
      .from('ciclo_meta')
      .select('mes_referencia,meta_diretoria')
      .eq('status', 'publicado')
      .order('mes_referencia', { ascending: false })
      .then(({ data, error }) => {
        if (!ativo) return
        if (error) setErro('Não foi possível listar os ciclos publicados.')
        else setCiclos(data ?? [])
      })
    return () => {
      ativo = false
    }
  }, [user])
  if (loading) return <p className="p-8">Carregando sessão…</p>
  if (!user) return <Navigate to="/" replace />
  const ciclo = ciclos.find((c) => c.mes_referencia === mes)
  const meta = ciclo ? centavos(ciclo.meta_diretoria) : 0n
  const anteriorMes = mes ? mesAnterior(mes) : ''
  let resultado: ReturnType<typeof simular> | null = null
  let erroPrevia = ''
  try {
    if (base && anterior && atual)
      resultado = simular(base, meta, anterior.clientes, atual.clientes, movimentos)
  } catch (e) {
    erroPrevia = erroTexto(e)
  }
  const saldoOrigem = resultado && saldoUnidade(resultado.linhas, origem)
  const saldoDestino = resultado && saldoUnidade(resultado.linhas, destino)
  const primeiraMeta = destino.tipo === 'loja' && !!destino.codigo && saldoDestino === 0n

  async function acao(fn: () => Promise<void>) {
    setOcupado(true)
    setErro('')
    try {
      await fn()
    } catch (e) {
      setErro(erroTexto(e))
    } finally {
      setOcupado(false)
    }
  }
  function incluir() {
    void acao(async () => {
      if (!base || !anterior || !atual) return
      const movimento: Movimento = { origem, destino, valor: centavos(valor) }
      if (primeiraMeta) {
        if (!atual.clientes.has(destino.codigo) || anterior.clientes.has(destino.codigo))
          throw new Error('Somente um cliente novo pode receber a primeira meta.')
        const dia = `${mes}-01`
        const [cliente, produto] = await Promise.all([
          supabase
            .from('catalog_clientes')
            .select('supervisor_codigo,promotor_codigo')
            .eq('cliente_codigo', destino.codigo)
            .lte('vigencia_inicio', dia)
            .or(`vigencia_fim.is.null,vigencia_fim.gt.${dia}`)
            .maybeSingle(),
          supabase
            .from('catalog_produtos')
            .select('produto_codigo')
            .eq('produto_codigo', sku.trim())
            .eq('ativo', true)
            .eq('is_panettone', false)
            .lte('vigencia_inicio', dia)
            .or(`vigencia_fim.is.null,vigencia_fim.gt.${dia}`)
            .maybeSingle(),
        ])
        if (
          cliente.error ||
          produto.error ||
          !cliente.data?.supervisor_codigo ||
          !cliente.data.promotor_codigo ||
          !produto.data
        )
          throw new Error(
            'A loja precisa de supervisor e promotor vigentes e o produto precisa estar ativo no ciclo.',
          )
        movimento.novaLinha = {
          loja: destino.codigo,
          sku: produto.data.produto_codigo,
          supervisor: cliente.data.supervisor_codigo,
          promotor: cliente.data.promotor_codigo,
          valor: 0n,
        }
      }
      if (
        acaoAlvo === 'colocar' &&
        promotorAlvo &&
        destino.codigo !== promotorAlvo &&
        origem.codigo !== promotorAlvo
      )
        throw new Error('Para este promotor, escolha-o como origem ou destino da transferência.')
      if (acaoAlvo === 'retirar' && promotorAlvo && destino.codigo === promotorAlvo)
        throw new Error('Toda a meta já está alocada: aqui só é possível retirar meta do promotor.')
      const lista = [...movimentos, movimento]
      simular(base, meta, anterior.clientes, atual.clientes, lista)
      setMovimentos(lista)
      setValor('')
    })
  }
  function baixar() {
    if (!resultado || !base || !anterior || !atual || !motivo.trim()) return
    const rascunho = {
      tipo: 'pre_visualizacao_nao_oficial',
      mes,
      autor: user!.email,
      motivo: motivo.trim(),
      bases: [anterior.arquivo, atual.arquivo],
      meta_diretoria_centavos: meta,
      residuo_centavos: resultado.residuo,
      movimentos,
    }
    const blob = new Blob(
      [JSON.stringify(rascunho, (_k, v) => (typeof v === 'bigint' ? String(v) : v), 2)],
      { type: 'application/json' },
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rascunho-redistribuicao-${mes}.json`
    a.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const unidade = (titulo: string, u: Unidade, set: (u: Unidade) => void) => (
    <div className="space-y-1">
      <label>
        {titulo}
        <select
          className={campo}
          value={u.tipo}
          onChange={(e) => set({ tipo: e.target.value as Tipo, codigo: '' })}
        >
          <option value="loja">Loja</option>
          <option value="supervisor">Supervisor</option>
          <option value="promotor">Promotor</option>
        </select>
      </label>
      <label>
        Código — {titulo.toLowerCase()}
        <input
          className={campo}
          value={u.codigo}
          onChange={(e) => set({ ...u, codigo: e.target.value.trim() })}
        />
      </label>
    </div>
  )

  return (
    <main className="min-h-screen bg-[#FAF6EF] text-[#2C1E12] p-5 sm:p-10">
      <div className="mx-auto max-w-4xl space-y-5">
        <Link className="underline" to="/dashboard">
          Voltar ao painel
        </Link>
        <h1 className="font-serif text-3xl font-bold">Redistribuir metas</h1>
        {promotorAlvo && (
          <p className="rounded-lg bg-[#FAF6EF] p-3">
            Promotor <strong>{promotorAlvo}</strong>
            {supervisorAlvo && <> · supervisor {supervisorAlvo}</>}.{' '}
            {acaoAlvo === 'retirar'
              ? 'Toda a meta já está alocada: só é possível retirar meta deste promotor.'
              : 'Há meta a alocar: é possível colocar meta neste promotor.'}
          </p>
        )}
        <p>
          Simule transferências sem mudar a meta publicada. O total deve fechar na Meta Diretoria,
          até o centavo.
        </p>
        {(erro || erroPrevia) && (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-800">
            {erro || erroPrevia}
          </p>
        )}
        <fieldset disabled={ocupado} className="space-y-4 rounded-xl border bg-white p-4">
          <label>
            Ciclo de referência
            <select
              className={campo}
              value={mes}
              onChange={(e) => {
                setMes(e.target.value)
                setAnterior(null)
                setAtual(null)
                setBase(null)
                setMovimentos([])
                setOrigem(vazia)
                setDestino(vazia)
                setValor('')
                setSku('')
                setMotivo('')
                setErro('')
              }}
            >
              <option value="">Selecione um ciclo publicado</option>
              {ciclos.map((c) => (
                <option key={c.mes_referencia}>{c.mes_referencia}</option>
              ))}
            </select>
          </label>
          {mes && (
            <>
              <p>
                Envie as duas bases completas de clientes. Use uma aba com{' '}
                <code>cliente_codigo</code> e <code>mes_referencia</code> (texto AAAA-MM). Não use
                apenas as lojas que venderam.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  [anteriorMes, anterior, setAnterior],
                  [mes, atual, setAtual],
                ].map(([periodo, b, setter]) => {
                  const mm = periodo as string
                  const fonte = b as Base | null
                  const set = setter as (valor: Base | null) => void
                  return (
                    <label key={mm}>
                      Base de clientes — {mm}
                      <input
                        className={campo}
                        type="file"
                        accept=".xlsx"
                        onChange={(e) => {
                          const f = e.currentTarget.files?.[0]
                          set(null)
                          setMovimentos([])
                          if (f) void acao(async () => set(await lerBase(f, mm)))
                        }}
                      />
                      {fonte && `${fonte.arquivo} · ${fonte.clientes.size} clientes`}
                    </label>
                  )
                })}
              </div>
              <button
                className={botao}
                disabled={!anterior || !atual}
                onClick={() =>
                  void acao(async () => {
                    const linhas = await carregarLinhas(mes)
                    fecharBase(linhas, meta)
                    setBase(linhas)
                    setMovimentos([])
                  })
                }
              >
                Carregar base da meta
              </button>
            </>
          )}
        </fieldset>
        {resultado && (
          <fieldset disabled={ocupado} className="space-y-4 rounded-xl border bg-white p-4">
            <p>
              <strong>Meta Diretoria e total da prévia:</strong> {brl(resultado.total)} ·{' '}
              <strong>Resíduo rateado:</strong> {brl(resultado.residuo)}
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {unidade('Origem', origem, setOrigem)}
              {unidade('Destino', destino, setDestino)}
            </div>
            <p>
              Saldo atual: {brl(saldoOrigem ?? 0n)} na origem e {brl(saldoDestino ?? 0n)} no
              destino.
            </p>
            {primeiraMeta && (
              <label>
                Produto para primeira meta da loja
                <input className={campo} value={sku} onChange={(e) => setSku(e.target.value)} />
              </label>
            )}
            <label>
              Valor da transferência (R$)
              <input
                className={campo}
                inputMode="decimal"
                placeholder="Ex.: 1500,00"
                value={valor}
                onChange={(e) => setValor(e.target.value)}
              />
            </label>
            <button className={botao} onClick={incluir}>
              Adicionar à prévia
            </button>
            {movimentos.length > 0 && (
              <>
                <ol className="list-decimal pl-5">
                  {movimentos.map((m, i) => (
                    <li key={i}>
                      {m.origem.tipo} {m.origem.codigo}: −{brl(m.valor)} → {m.destino.tipo}{' '}
                      {m.destino.codigo}: +{brl(m.valor)}
                    </li>
                  ))}
                </ol>
                <button
                  className="underline"
                  onClick={() => setMovimentos(movimentos.slice(0, -1))}
                >
                  Desfazer última transferência
                </button>
                <label className="block">
                  Motivo do rascunho
                  <input
                    className={campo}
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                  />
                </label>
                <button className={botao} disabled={!motivo.trim()} onClick={baixar}>
                  Baixar rascunho
                </button>
                <p className="text-sm">O rascunho não é salvo nem publicado no sistema.</p>
              </>
            )}
          </fieldset>
        )}
        {ocupado && <p role="status">Conferindo dados…</p>}
      </div>
    </main>
  )
}

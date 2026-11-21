import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LogOut,
  ChevronRight,
  Calculator,
  RefreshCw,
  Building2,
  Users,
  Package,
  Search,
  X,
  Shuffle,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { PanutrirLogo } from '@/components/PanutrirLogo'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { BuscaPromotor, type OpcaoPromotor } from '@/components/BuscaPromotor'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { centavos } from '@/lib/redistribuicao'

type Alvo = {
  promotor: string
  supervisor: string | null
  cliente?: string
  sku?: string
  nome?: string
}
type EstadoAjuste = { habilitado: boolean; revisao?: number; motivo?: string }
async function consultarAjuste(mes: string, args: Record<string, unknown> = {}) {
  const db = supabase as unknown as {
    rpc: (
      nome: string,
      args: Record<string, unknown>,
    ) => PromiseLike<{ data: EstadoAjuste | null; error: { message: string } | null }>
  }
  const { data, error } = await db.rpc('transferir_meta_vigente', { p_mes: mes, ...args })
  if (error || !data) throw new Error(error?.message ?? 'Não foi possível consultar o ajuste.')
  return data
}

const MES_TAG_PDV = '2026-10'
type PdvMarcado = {
  cliente_codigo: string
  cliente_nome: string
  supervisor_codigo: string | null
  promotor_codigo: string | null
  tag_pdv: string | null
}

interface AggRow {
  supervisor?: string | null
  promotor?: string | null
  regime?: string
  o?: number | string | null
  g?: number | string | null
  f?: number | string | null
  n?: number | string | null
  c?: number | string | null
}

interface LinhaRow {
  meta_linha_id: string
  cliente: string
  sku: string
  cliente_nome: string | null
  produto_nome: string | null
  linha_produto: string | null
  supervisor: string | null
  promotor: string | null
  regime: string
  meta_original: number | string
  gap_linha: number | string
  meta_final: number | string
  memoria: Record<string, unknown> | null
}

const REGIME_LABEL: Record<string, string> = {
  REGULAR_24M: 'Regular 24M',
  PISO_MADURO: 'Piso técnico',
  INTRODUCAO: 'Introdução',
  INTRODUCAO_ZERO: 'Introdução (sem venda)',
  SUBSTITUICAO_ORIGEM: 'Substituição (origem)',
  SUBSTITUICAO_DESTINO: 'Substituição (destino)',
}

// Memória de cálculo: como cada regime chega ao número (metodologia Out/26, M-05..M-16)
const REGIME_COMO: Record<string, string> = {
  REGULAR_24M:
    'Pbase = 0,35×B1 + 0,30×B2 + 0,35×B3 — B1 = 6 meses mais recentes, B2 = 6 anteriores, B3 = 12 mais antigos (cada mês ÷ dias úteis ÷ IS). Baseline = Pbase × IS_T × DU_T. Meta teórica = baseline × (1 + G). Venda líquida de 3 termos (vlritens − vlrdesc − vlrtroca).',
  PISO_MADURO:
    'Piso = média dos meses com venda > 0 × (1 + G). Dispara quando a meta teórica ≤ 0. Métrica: vlritens − vlrdesc.',
  INTRODUCAO:
    'Meta = venda de setembro × taxa (1,25 se idade 0; 1,10 caso contrário). Métrica: vlritens − vlrdesc.',
  INTRODUCAO_ZERO: 'Introdução sem venda em setembro → meta zero (M-13).',
  SUBSTITUICAO_ORIGEM:
    'PlufiNut Assaí: meta zerada; 59% do histórico do par é transferido ao Pão de Leite da mesma loja (taxa 0,59).',
  SUBSTITUICAO_DESTINO:
    'Pão de Leite Assaí: meta própria + transferência recebida do PlufiNut (59% do histórico do par).',
}

const CAMPOS_MEMORIA: Array<[string, string, (v: unknown) => string]> = [
  ['idade_meses', 'Idade (meses)', (v) => fmtNum(v, 0)],
  ['vl_m1', 'Venda M1 (métrica do piso)', (v) => fmtBRL(v as number)],
  ['B1', 'Bloco B1 — 6 meses mais recentes', (v) => fmtNum(v, 6)],
  ['B2', 'Bloco B2 — 6 meses anteriores', (v) => fmtNum(v, 6)],
  ['B3', 'Bloco B3 — 12 meses mais antigos', (v) => fmtNum(v, 6)],
  ['Pbase', 'Pbase = 0,35·B1 + 0,30·B2 + 0,35·B3', (v) => fmtNum(v, 6)],
  ['baseline', 'Baseline = Pbase × IS × DU', (v) => fmtBRL(v as number)],
  ['meta_teorica', 'Meta teórica = baseline × (1+G)', (v) => fmtBRL(v as number)],
  ['piso', 'Piso técnico', (v) => fmtBRL(v as number)],
  ['taxa_introducao', 'Taxa de introdução', (v) => fmtNum(v, 2)],
  ['taxa_substituicao', 'Taxa de substituição', (v) => fmtNum(v, 2)],
  ['transferencia', 'Transferência gerada (origem)', (v) => fmtBRL(v as number)],
  ['transferencia_recebida', 'Transferência recebida (destino)', (v) => fmtBRL(v as number)],
  ['meta_propria', 'Meta própria', (v) => fmtBRL(v as number)],
  ['agregado_de', 'Linhas agregadas nesta chave', (v) => fmtNum(v, 0)],
]

function fmtBRL(v: number | string | null | undefined) {
  return v == null ? '—' : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function fmtNum(v: unknown, dec = 2) {
  return v == null || v === ''
    ? '—'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec })
}

function MemoriaPanel({ linha, onClose }: { linha: LinhaRow; onClose: () => void }) {
  const m = (linha.memoria ?? {}) as Record<string, unknown>
  return (
    <Card className="border-[#D99A2B]/40 bg-white shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base font-serif flex items-center gap-2">
              <Calculator className="w-4 h-4 text-[#D99A2B]" />
              Memória de cálculo — {linha.cliente_nome ?? linha.cliente} ·{' '}
              {linha.produto_nome ?? linha.sku}
            </CardTitle>
            <CardDescription className="text-xs">
              Cliente {linha.cliente} × SKU {linha.sku} · Linha {linha.linha_produto ?? '—'}
            </CardDescription>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-[#FAF6EF]" title="Fechar">
            <X className="w-4 h-4 text-[#7A6A5A]" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] p-4 space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#7A6A5A]">
            Regime: {REGIME_LABEL[linha.regime] ?? linha.regime}
          </p>
          <p className="text-xs text-[#2C1E12] leading-relaxed">
            {REGIME_COMO[linha.regime] ?? '—'}
          </p>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="border-[#E5D9C8]">
              <TableHead className="text-[#7A6A5A]">Passo</TableHead>
              <TableHead className="text-[#7A6A5A] text-right">Valor</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {CAMPOS_MEMORIA.filter(([k]) => m[k] != null).map(([k, label, fmt]) => (
              <TableRow key={k} className="border-[#E5D9C8]">
                <TableCell className="text-xs text-[#7A6A5A]">{label}</TableCell>
                <TableCell className="text-right font-mono text-xs text-[#2C1E12]">
                  {fmt(m[k])}
                </TableCell>
              </TableRow>
            ))}
            <TableRow className="border-[#E5D9C8] bg-[#FAF6EF]/60">
              <TableCell className="text-xs font-semibold text-[#2C1E12]">Meta Original</TableCell>
              <TableCell className="text-right font-mono text-xs font-semibold">
                {fmtBRL(linha.meta_original)}
              </TableCell>
            </TableRow>
            <TableRow className="border-[#E5D9C8]">
              <TableCell className="text-xs text-[#7A6A5A]">
                GAP da linha {m.via_gap ? `— ${String(m.via_gap)}` : ''}
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {fmtBRL(linha.gap_linha)}
              </TableCell>
            </TableRow>
            <TableRow className="border-[#E5D9C8] bg-[#D99A2B]/10">
              <TableCell className="text-xs font-bold text-[#2C1E12]">
                Meta Final = Original + GAP
              </TableCell>
              <TableCell className="text-right font-mono text-xs font-bold">
                {fmtBRL(linha.meta_final)}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export default function ConsultaDrillDown() {
  const navigate = useNavigate()
  const { user, session, loading, signOut } = useAuth()
  const [nivel, setNivel] = useState<'empresa' | 'supervisor' | 'promotor'>('empresa')
  const [sup, setSup] = useState<string | null>(null)
  const [prom, setProm] = useState<string | null>(null)
  const [aggs, setAggs] = useState<AggRow[]>([])
  const [totais, setTotais] = useState<{ o: number; g: number; f: number; n: number } | null>(null)
  const [regimes, setRegimes] = useState<AggRow[]>([])
  const [linhas, setLinhas] = useState<LinhaRow[]>([])
  const [aberta, setAberta] = useState<LinhaRow | null>(null)
  const [nomes, setNomes] = useState<Record<string, string>>({})
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [filtroPromotor, setFiltroPromotor] = useState('')
  const [supervisoresSelecionados, setSupervisoresSelecionados] = useState<string[]>([])
  const [apenasNovosPdvs, setApenasNovosPdvs] = useState(false)
  const [pdvsMarcados, setPdvsMarcados] = useState<PdvMarcado[]>([])
  const [estadoPdvs, setEstadoPdvs] = useState<'carregando' | 'pronto' | 'erro'>('carregando')
  const [mes, setMes] = useState('2026-10')
  const [ciclos, setCiclos] = useState<string[]>([])
  const [estado, setEstado] = useState<EstadoAjuste | null>(null)
  const [contrapartes, setContrapartes] = useState<AggRow[]>([])
  const [alvo, setAlvo] = useState<Alvo | null>(null)
  const [contraparte, setContraparte] = useState('')
  const [acao, setAcao] = useState('adicionar')
  const [valorAjuste, setValorAjuste] = useState('')
  const [motivoAjuste, setMotivoAjuste] = useState('')
  const [erroAjuste, setErroAjuste] = useState('')
  const [avisoAjuste, setAvisoAjuste] = useState('')
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    if (!user || !session) return
    let ativo = true
    void supabase
      .from('ciclo_meta')
      .select('mes_referencia')
      .eq('status', 'publicado')
      .order('mes_referencia', { ascending: false })
      .then(({ data, error }) => {
        if (!ativo || error || !data?.length) return
        setCiclos(data.map((c) => c.mes_referencia))
        setMes(data[0].mes_referencia)
      })
    return () => {
      ativo = false
    }
  }, [user, session])
  useEffect(() => {
    if (!user || !session) return
    let ativo = true
    setEstado(null)
    setContrapartes([])
    void consultarAjuste(mes)
      .then(async (r) => {
        if (ativo) setEstado(r)
        if (!r.habilitado) return
        const { data, error } = await supabase
          .from('vw_meta_promotor')
          .select('supervisor,promotor,f:meta_final')
          .eq('referencia_ciclo', mes)
          .gt('meta_final', 0)
          .order('promotor')
          .order('supervisor')
        if (ativo && !error) setContrapartes((data ?? []) as AggRow[])
      })
      .catch(() => {
        if (ativo) setEstado(null)
      })
    return () => {
      ativo = false
    }
  }, [mes, user, session])

  useEffect(() => {
    if (!user || !session || !apenasNovosPdvs || mes !== MES_TAG_PDV) return
    let ativo = true
    setEstadoPdvs('carregando')
    const dia = `${MES_TAG_PDV}-01`
    void supabase
      .from('catalog_clientes')
      .select('cliente_codigo,cliente_nome,supervisor_codigo,promotor_codigo,tag_pdv')
      .in('tag_pdv', ['novo_na_base', 'lacuna'])
      .lte('vigencia_inicio', dia)
      .or(`vigencia_fim.is.null,vigencia_fim.gt.${dia}`)
      .order('cliente_codigo')
      .then(({ data, error }) => {
        if (!ativo) return
        setPdvsMarcados(error ? [] : (data ?? []))
        setEstadoPdvs(error ? 'erro' : 'pronto')
      })
    return () => {
      ativo = false
    }
  }, [user, session, mes, apenasNovosPdvs])

  function abrirAjuste(a: Alvo) {
    setValorAjuste('')
    setMotivoAjuste('')
    setErroAjuste('')
    setAvisoAjuste('')
    setContraparte('')
    setAcao('adicionar')
    setAlvo(a)
  }
  function abrirDetalhe(l: LinhaRow, porProduto: boolean) {
    if (!l.promotor) return
    abrirAjuste({
      promotor: l.promotor,
      supervisor: l.supervisor,
      cliente: l.cliente,
      sku: porProduto ? l.sku : undefined,
      nome: porProduto
        ? `${l.cliente_nome ?? l.cliente} · ${l.produto_nome ?? l.sku}`
        : (l.cliente_nome ?? l.cliente),
    })
  }
  async function salvarAjuste(e: React.FormEvent) {
    e.preventDefault()
    if (!alvo || !estado?.habilitado || salvando || contraparte === '') return
    setSalvando(true)
    setErroAjuste('')
    try {
      const valor = centavos(valorAjuste)
      if (valor <= 0n) throw new Error('Informe um valor positivo.')
      const outro = contrapartes[Number(contraparte)]
      if (!outro?.promotor) throw new Error('Selecione a contraparte.')
      if (outro.promotor === alvo.promotor && (outro.supervisor ?? null) === alvo.supervisor)
        throw new Error('Origem e destino não podem ser o mesmo promotor.')
      const unidade = {
        promotor: alvo.promotor,
        supervisor: alvo.supervisor,
        cliente: alvo.cliente,
        sku: alvo.sku,
      }
      const contraria = { promotor: outro.promotor, supervisor: outro.supervisor ?? null }
      const r = await consultarAjuste(mes, {
        p_origem: acao === 'adicionar' ? contraria : unidade,
        p_destino: acao === 'adicionar' ? unidade : contraria,
        p_valor: `${valor / 100n}.${String(valor % 100n).padStart(2, '0')}`,
        p_motivo: motivoAjuste.trim(),
        p_revisao: estado.revisao,
      })
      if (!r.habilitado) throw new Error(r.motivo ?? 'Ciclo não habilitado.')
      setEstado(r)
      setAlvo(null)
      setAvisoAjuste('Transferência aplicada à meta vigente. A Meta Diretoria não mudou.')
      await carregar()
    } catch (erro) {
      setErroAjuste(erro instanceof Error ? erro.message : 'Não foi possível salvar.')
      try {
        setEstado(await consultarAjuste(mes))
        await carregar()
      } catch {
        /* mantém o erro */
      }
    } finally {
      setSalvando(false)
    }
  }

  useEffect(() => {
    if (!loading && !user && !session) navigate('/', { replace: true })
  }, [user, session, loading, navigate])

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    setAberta(null)
    try {
      if (nivel === 'empresa') {
        const [regR, supR] = await Promise.all([
          supabase
            .from('vw_meta_regime')
            .select('regime, n:combinacoes, o:meta_original, g:gap_linha, f:meta_final')
            .eq('referencia_ciclo', mes)
            .order('regime'),
          // Nível promotor: cada linha traz também o supervisor a que pertence
          supabase
            .from('vw_meta_promotor')
            .select(
              'supervisor, promotor, n:combinacoes, c:clientes, o:meta_original, g:gap_linha, f:meta_final',
            )
            .eq('referencia_ciclo', mes)
            .order('meta_final', { ascending: false }),
        ])
        if (regR.error) throw regR.error
        if (supR.error) throw supR.error
        const regs = (regR.data ?? []) as AggRow[]
        const sups = (supR.data ?? []) as AggRow[]
        const t = regs.reduce<{ o: number; g: number; f: number; n: number }>(
          (a, r) => ({
            o: Number(a.o) + Number(r.o ?? 0),
            g: Number(a.g) + Number(r.g ?? 0),
            f: Number(a.f) + Number(r.f ?? 0),
            n: Number(a.n) + Number(r.n ?? 0),
          }),
          { o: 0, g: 0, f: 0, n: 0 },
        )
        setTotais(t)
        setRegimes(regs)
        setAggs(sups)
        setLinhas([])
      } else if (nivel === 'supervisor' && sup) {
        const { data, error } = await supabase
          .from('vw_meta_promotor')
          .select('promotor, n:combinacoes, c:clientes, o:meta_original, g:gap_linha, f:meta_final')
          .eq('referencia_ciclo', mes)
          .eq('supervisor', sup)
          .order('meta_final', { ascending: false })
        if (error) throw error
        setAggs((data ?? []) as AggRow[])
        setLinhas([])
      } else if (nivel === 'promotor' && sup && prom) {
        const { data, error } = await supabase
          .from('vw_meta_linha_vigente' as 'meta_linha')
          .select('*')
          .eq('referencia_ciclo', mes)
          .eq('supervisor', sup)
          .eq('promotor', prom)
          .order('meta_final', { ascending: false })
          .limit(300)
        if (error) throw error
        setLinhas((data ?? []) as LinhaRow[])
        setAggs([])
      }
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    }
    setCarregando(false)
  }, [nivel, sup, prom, mes])

  useEffect(() => {
    if (user && session) carregar()
  }, [user, session, carregar])

  // Nomes dos responsáveis (melhor esforço — se a leitura falhar, ficam os códigos)
  useEffect(() => {
    ;(
      supabase as unknown as {
        from: (t: string) => { select: (s: string) => Promise<{ data: unknown }> }
      }
    )
      .from('catalog_responsaveis')
      .select('responsavel_codigo, responsavel_rotulo')
      .then(({ data }) => {
        if (data) {
          const map: Record<string, string> = {}
          for (const r of data as Array<{ responsavel_codigo: string; responsavel_rotulo: string }>)
            map[r.responsavel_codigo] = r.responsavel_rotulo
          setNomes(map)
        }
      })
      .catch(() => {})
  }, [])

  const handleSignOut = async () => {
    await signOut()
    navigate('/', { replace: true })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF6EF]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-[#D99A2B] border-t-transparent rounded-full animate-spin" />
          <p className="font-sans text-sm text-[#7A6A5A]">Carregando ambiente...</p>
        </div>
      </div>
    )
  }

  const userEmail = user?.email || session?.user?.email || 'colaborador@panutrir.com.br'
  const userName =
    user?.user_metadata?.name ||
    userEmail
      .split('@')[0]
      .replace('.', ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase())

  const nomeResp = (codigo: string | null | undefined) =>
    codigo ? (nomes[codigo] ? `${nomes[codigo]} (${codigo})` : `Responsável ${codigo}`) : '—'

  const irParaSupervisor = (codigo: string) => {
    setSup(codigo)
    setProm(null)
    setNivel('supervisor')
  }
  const irParaPromotorDireto = (codigo: string, supervisor: string | null | undefined) => {
    setSup(supervisor ?? null)
    setProm(codigo)
    setNivel('promotor')
  }
  const irParaPromotor = (codigo: string) => {
    setProm(codigo)
    setNivel('promotor')
  }
  const voltar = () => {
    if (nivel === 'promotor') setNivel('supervisor')
    else if (nivel === 'supervisor') {
      setSup(null)
      setNivel('empresa')
    }
  }

  const filtroNorm = filtroPromotor.trim().toLowerCase()
  const mostrarPdvs = apenasNovosPdvs && mes === MES_TAG_PDV
  const supervisoresDisponiveis = [
    ...new Set([
      ...aggs.flatMap((r) => (r.supervisor ? [r.supervisor] : [])),
      ...(mostrarPdvs
        ? pdvsMarcados.flatMap((pdv) => (pdv.supervisor_codigo ? [pdv.supervisor_codigo] : []))
        : []),
      ...supervisoresSelecionados,
    ]),
  ].sort((a, b) => nomeResp(a).localeCompare(nomeResp(b), 'pt-BR'))
  const pdvsFiltrados = pdvsMarcados.filter((pdv) => {
    if (nivel !== 'empresa' && pdv.supervisor_codigo !== sup) return false
    if (nivel === 'promotor' && pdv.promotor_codigo !== prom) return false
    if (
      supervisoresSelecionados.length &&
      !supervisoresSelecionados.includes(pdv.supervisor_codigo ?? '')
    )
      return false
    if (!filtroNorm) return true
    const codigo = pdv.promotor_codigo ?? ''
    return `${nomes[codigo] ?? ''} ${codigo}`.toLowerCase().includes(filtroNorm)
  })
  const aggsFiltrados =
    nivel === 'empresa'
      ? aggs.filter((r) => {
          if (
            supervisoresSelecionados.length &&
            !supervisoresSelecionados.includes(r.supervisor ?? '')
          )
            return false
          const promotor = r.promotor ?? ''
          return (
            !filtroNorm || `${nomes[promotor] ?? ''} ${promotor}`.toLowerCase().includes(filtroNorm)
          )
        })
      : aggs

  // Promotores que podem ser a contraparte: o próprio promotor do alvo fica fora (origem ≠ destino)
  const opcoesContraparte: OpcaoPromotor[] = contrapartes.flatMap((r, i) =>
    r.promotor &&
    (r.promotor !== alvo?.promotor || (r.supervisor ?? null) !== (alvo?.supervisor ?? null))
      ? [
          {
            valor: String(i),
            rotulo: `${nomeResp(r.promotor)} · ${nomeResp(r.supervisor)}`,
            busca: `${nomes[r.promotor] ?? ''} ${r.promotor} ${nomes[r.supervisor ?? ''] ?? ''}`,
          },
        ]
      : [],
  )

  const totAgg = (rows: AggRow[]) => ({
    o: rows.reduce((s, r) => s + Number(r.o ?? 0), 0),
    g: rows.reduce((s, r) => s + Number(r.g ?? 0), 0),
    f: rows.reduce((s, r) => s + Number(r.f ?? 0), 0),
  })

  return (
    <div className="min-h-screen bg-[#FAF6EF] text-[#2C1E12] flex flex-col font-sans">
      <Dialog
        open={!!alvo}
        onOpenChange={(aberto) => {
          if (!aberto && !salvando) setAlvo(null)
        }}
      >
        {alvo && (
          <DialogContent>
            <DialogTitle>Redistribuir meta — {alvo.nome ?? nomeResp(alvo.promotor)}</DialogTitle>
            <DialogDescription>
              Ao salvar, o valor sai da origem e entra no destino imediatamente. A Meta Diretoria
              não muda.
            </DialogDescription>
            <form className="space-y-3" onSubmit={salvarAjuste}>
              <label className="block">
                Operação
                <select
                  className="block w-full rounded border p-2"
                  value={acao}
                  onChange={(e) => setAcao(e.target.value)}
                  disabled={salvando}
                >
                  <option value="adicionar">Adicionar meta</option>
                  <option value="retirar">Retirar meta</option>
                </select>
              </label>
              <label className="block">
                {acao === 'adicionar'
                  ? 'Retirar de qual promotor?'
                  : 'Transferir para qual promotor?'}
                <BuscaPromotor
                  id="contraparte-promotor"
                  opcoes={opcoesContraparte}
                  valor={contraparte}
                  onChange={setContraparte}
                  disabled={salvando}
                />
              </label>
              <label className="block">
                Valor (R$)
                <Input
                  required
                  inputMode="decimal"
                  value={valorAjuste}
                  onChange={(e) => setValorAjuste(e.target.value)}
                  disabled={salvando}
                  placeholder="Ex.: 1000,00"
                />
              </label>
              <label className="block">
                Motivo
                <Input
                  required
                  maxLength={500}
                  value={motivoAjuste}
                  onChange={(e) => setMotivoAjuste(e.target.value)}
                  disabled={salvando}
                />
              </label>
              {erroAjuste && (
                <p role="alert" className="text-sm text-red-700">
                  {erroAjuste}
                </p>
              )}
              <div className="flex justify-end gap-2">
                <button
                  className="rounded-lg border px-3 py-2"
                  type="button"
                  disabled={salvando}
                  onClick={() => setAlvo(null)}
                >
                  Cancelar
                </button>
                <button
                  className="rounded-lg bg-[#745322] px-3 py-2 text-white disabled:opacity-50"
                  disabled={
                    salvando || !estado?.habilitado || contraparte === '' || !motivoAjuste.trim()
                  }
                >
                  {salvando ? 'Salvando…' : 'Salvar ajuste'}
                </button>
              </div>
            </form>
          </DialogContent>
        )}
      </Dialog>
      {avisoAjuste && (
        <p role="status" className="bg-green-50 p-3 text-center text-green-900">
          {avisoAjuste}
        </p>
      )}
      <header className="border-b border-[#E5D9C8] bg-white sticky top-0 z-20 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <PanutrirLogo variant="dark" size="sm" showSlogan={false} />
            <span className="hidden sm:inline-block text-[#E5D9C8]">|</span>
            <span className="hidden sm:inline-block font-sans text-xs tracking-wider uppercase font-semibold text-[#7A6A5A]">
              Controle de Metas
            </span>
          </div>
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-sm font-semibold text-[#2C1E12]">{userName}</span>
              <span className="text-xs text-[#7A6A5A] font-mono">{userEmail}</span>
            </div>
            <button
              onClick={handleSignOut}
              className="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-[#E5D9C8] text-xs font-semibold text-[#7A6A5A] hover:text-[#C44133] hover:border-[#C44133]/40 hover:bg-[#FDE8E6]/40 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sair</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-6 animate-fade-in">
        <div className="space-y-2">
          <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight">
            Consulta Drill-down — Ciclo {mes}
          </h1>
          <p className="font-sans text-sm text-[#7A6A5A] max-w-3xl">
            Navegue de Empresa a Cliente × SKU. Cada linha abre a memória de cálculo que explica o
            número (regime, blocos B1/B2/B3, baseline, piso, transferência e via do GAP) sem
            precisar da planilha.
          </p>
        </div>

        <label className="block text-sm">
          Ciclo publicado
          <select
            className="ml-2 rounded border bg-white p-2"
            value={mes}
            disabled={salvando}
            onChange={(e) => {
              setMes(e.target.value)
              setApenasNovosPdvs(false)
              setEstadoPdvs('carregando')
              setEstado(null)
              setAlvo(null)
              setNivel('empresa')
              setSup(null)
              setProm(null)
              setAggs([])
              setLinhas([])
              setRegimes([])
              setTotais(null)
              setSupervisoresSelecionados([])
              setAvisoAjuste('')
            }}
          >
            {(ciclos.length ? ciclos : [mes]).map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        {estado?.motivo && <p className="text-sm text-[#7A6A5A]">{estado.motivo}</p>}

        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-xs font-semibold flex-wrap">
          <button
            onClick={() => {
              setSup(null)
              setProm(null)
              setNivel('empresa')
            }}
            className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border transition-colors ${
              nivel === 'empresa'
                ? 'bg-[#3E2A1E] text-[#FAF6EF] border-[#3E2A1E]'
                : 'bg-white border-[#E5D9C8] text-[#7A6A5A] hover:bg-[#FAF6EF]'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" /> Empresa
          </button>
          {sup && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-[#7A6A5A]" />
              <button
                onClick={() => {
                  setProm(null)
                  setNivel('supervisor')
                }}
                className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border transition-colors ${
                  nivel === 'supervisor'
                    ? 'bg-[#3E2A1E] text-[#FAF6EF] border-[#3E2A1E]'
                    : 'bg-white border-[#E5D9C8] text-[#7A6A5A] hover:bg-[#FAF6EF]'
                }`}
              >
                <Users className="w-3.5 h-3.5" /> Supervisor {nomes[sup] ?? sup}
              </button>
            </>
          )}
          {prom && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-[#7A6A5A]" />
              <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border bg-[#3E2A1E] text-[#FAF6EF] border-[#3E2A1E]">
                <Package className="w-3.5 h-3.5" /> Promotor {nomes[prom] ?? prom}
              </span>
            </>
          )}
          {nivel !== 'empresa' && (
            <button
              onClick={voltar}
              className="ml-2 px-2.5 py-1.5 rounded-lg border border-[#E5D9C8] bg-white text-[#7A6A5A] hover:bg-[#FAF6EF]"
            >
              Voltar
            </button>
          )}
        </div>

        {/* Totais da empresa */}
        {nivel === 'empresa' && totais && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="border-[#E5D9C8] bg-white shadow-sm p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#7A6A5A]">
                Meta Original
              </p>
              <p className="font-serif text-lg font-bold">{fmtBRL(totais.o)}</p>
            </Card>
            <Card className="border-[#E5D9C8] bg-white shadow-sm p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#7A6A5A]">
                GAP alocado
              </p>
              <p className="font-serif text-lg font-bold">{fmtBRL(totais.g)}</p>
            </Card>
            <Card className="border-[#E5D9C8] bg-white shadow-sm p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#7A6A5A]">
                Meta Final
              </p>
              <p className="font-serif text-lg font-bold">{fmtBRL(totais.f)}</p>
            </Card>
            <Card className="border-[#E5D9C8] bg-white shadow-sm p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#7A6A5A]">
                Combinações
              </p>
              <p className="font-serif text-lg font-bold">{fmtNum(totais.n, 0)}</p>
            </Card>
          </div>
        )}

        {/* Distribuição por regime (nível empresa) */}
        {nivel === 'empresa' && regimes.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {regimes.map((r) => (
              <Badge
                key={r.regime}
                className="bg-white text-[#2C1E12] border border-[#E5D9C8] hover:bg-[#FAF6EF] font-normal"
              >
                {REGIME_LABEL[r.regime ?? ''] ?? r.regime}: {fmtNum(r.n, 0)} · {fmtBRL(r.f)}
              </Badge>
            ))}
          </div>
        )}

        {/* Filtro de promotor (topo da tela, nível empresa) */}
        {nivel === 'empresa' && (
          <div className="flex flex-wrap items-start gap-3">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7A6A5A] pointer-events-none" />
              <Input
                value={filtroPromotor}
                onChange={(e) => setFiltroPromotor(e.target.value)}
                placeholder="Buscar promotor…"
                className="pl-9 bg-white border-[#E5D9C8] text-sm text-[#2C1E12] placeholder:text-[#7A6A5A] focus-visible:ring-[#D99A2B]"
              />
              {filtroPromotor && (
                <button
                  onClick={() => setFiltroPromotor('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-[#FAF6EF]"
                  title="Limpar filtro"
                >
                  <X className="w-3.5 h-3.5 text-[#7A6A5A]" />
                </button>
              )}
            </div>
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="rounded-lg border border-[#E5D9C8] bg-white px-3 py-2 text-sm"
                >
                  Supervisores:{' '}
                  {supervisoresSelecionados.length
                    ? `${supervisoresSelecionados.length} selecionado(s)`
                    : 'Todos'}{' '}
                  ▾
                </button>
              </PopoverTrigger>
              <PopoverContent align="start" aria-label="Filtrar supervisores" className="w-80">
                <button
                  type="button"
                  onClick={() => setSupervisoresSelecionados([])}
                  className="mb-2 text-sm underline"
                >
                  Limpar seleção
                </button>
                <fieldset className="max-h-64 space-y-1 overflow-y-auto">
                  <legend className="sr-only">Supervisores</legend>
                  {supervisoresDisponiveis.map((codigo) => (
                    <label
                      key={codigo}
                      className="flex cursor-pointer items-center gap-2 rounded p-1 text-sm hover:bg-[#FAF6EF]"
                    >
                      <input
                        type="checkbox"
                        checked={supervisoresSelecionados.includes(codigo)}
                        onChange={(e) => {
                          const marcado = e.currentTarget.checked
                          setSupervisoresSelecionados((atual) =>
                            marcado ? [...atual, codigo] : atual.filter((c) => c !== codigo),
                          )
                        }}
                      />
                      {nomeResp(codigo)}
                    </label>
                  ))}
                  {supervisoresDisponiveis.length === 0 && (
                    <p className="text-sm">Nenhum supervisor disponível.</p>
                  )}
                </fieldset>
              </PopoverContent>
            </Popover>
          </div>
        )}

        {mes === MES_TAG_PDV && (
          <div className="flex items-center gap-2">
            <Switch
              id="toggle-novos-pdvs"
              checked={mostrarPdvs}
              onCheckedChange={(marcado) => {
                setEstadoPdvs('carregando')
                setApenasNovosPdvs(marcado)
              }}
            />
            <Label htmlFor="toggle-novos-pdvs" className="cursor-pointer text-sm font-medium">
              Mostrar apenas PDVs novos
            </Label>
          </div>
        )}
        {mostrarPdvs && (
          <Card className="border-[#E5D9C8] bg-white">
            <CardContent className="space-y-3 pt-6">
              <p className="text-sm text-[#7A6A5A]">
                PDVs marcados na comparação de outubro com setembro, incluindo lacunas e PDVs sem
                meta.
              </p>
              {estadoPdvs === 'carregando' ? (
                <p role="status">Carregando PDVs…</p>
              ) : estadoPdvs === 'erro' ? (
                <p role="alert">Não foi possível consultar as marcações de PDVs.</p>
              ) : pdvsFiltrados.length === 0 ? (
                <p>Nenhum PDV novo encontrado com os filtros selecionados.</p>
              ) : (
                <>
                  <p className="text-sm font-semibold">{pdvsFiltrados.length} PDV(s)</p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>PDV</TableHead>
                        <TableHead>Supervisor</TableHead>
                        <TableHead>Promotor</TableHead>
                        <TableHead>Marcação</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pdvsFiltrados.map((pdv) => (
                        <TableRow key={pdv.cliente_codigo}>
                          <TableCell>
                            {pdv.cliente_nome} · {pdv.cliente_codigo}
                          </TableCell>
                          <TableCell>{nomeResp(pdv.supervisor_codigo)}</TableCell>
                          <TableCell>{nomeResp(pdv.promotor_codigo)}</TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {pdv.tag_pdv === 'lacuna' ? 'Lacuna' : 'Novo na base'}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {erro && (
          <div className="rounded-xl border border-[#C44133]/30 bg-[#FDE8E6]/50 p-4 text-sm text-[#C44133]">
            Erro ao carregar: {erro}
          </div>
        )}

        {!mostrarPdvs &&
          (carregando ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-3 border-[#D99A2B] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Tabela de agregados (empresa/supervisor) */}
              {aggsFiltrados.length > 0 && (
                <Card className="border-[#E5D9C8] bg-white shadow-sm">
                  <CardContent className="pt-6">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-[#E5D9C8]">
                          <TableHead className="text-[#7A6A5A]">Promotor</TableHead>
                          {nivel === 'empresa' && (
                            <TableHead className="text-[#7A6A5A]">Supervisor</TableHead>
                          )}
                          <TableHead className="text-[#7A6A5A] text-right">Combinações</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">Meta Original</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">GAP</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">Meta Final</TableHead>
                          <TableHead className="text-[#7A6A5A] text-center">Redistribuir</TableHead>
                          <TableHead className="text-[#7A6A5A] text-center">Abrir</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {aggsFiltrados.map((r, i) => {
                          const codigo = r.promotor
                          return (
                            <TableRow
                              key={`${codigo ?? 'sem'}-${r.supervisor ?? 'sem'}-${i}`}
                              className="border-[#E5D9C8] cursor-pointer hover:bg-[#FAF6EF]/60"
                              onClick={() =>
                                codigo &&
                                (nivel === 'empresa'
                                  ? irParaPromotorDireto(codigo, r.supervisor)
                                  : irParaPromotor(codigo))
                              }
                            >
                              <TableCell className="text-xs font-semibold">
                                {nomeResp(r.promotor)}
                              </TableCell>
                              {nivel === 'empresa' && (
                                <TableCell className="text-xs text-[#7A6A5A]">
                                  {nomeResp(r.supervisor)}
                                </TableCell>
                              )}
                              <TableCell className="text-right font-mono text-xs">
                                {fmtNum(r.n, 0)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-xs">
                                {fmtBRL(r.o)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-xs">
                                {fmtBRL(r.g)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-xs font-semibold">
                                {fmtBRL(r.f)}
                              </TableCell>
                              <TableCell className="text-center">
                                {codigo && estado?.habilitado && Number(r.f) > 0 && (
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      abrirAjuste({
                                        promotor: codigo,
                                        supervisor: r.supervisor ?? sup ?? null,
                                      })
                                    }}
                                    className="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs"
                                  >
                                    <Shuffle className="w-3.5 h-3.5" /> Redistribuir
                                  </button>
                                )}
                              </TableCell>
                              <TableCell className="text-center">
                                <ChevronRight className="w-4 h-4 text-[#D99A2B] inline" />
                              </TableCell>
                            </TableRow>
                          )
                        })}
                        <TableRow className="border-[#E5D9C8] bg-[#FAF6EF]/60">
                          <TableCell className="text-xs font-bold">Total</TableCell>
                          {nivel === 'empresa' && <TableCell />}
                          {(() => {
                            const t = totAgg(aggsFiltrados)
                            return (
                              <>
                                <TableCell className="text-right font-mono text-xs font-bold">
                                  {fmtBRL(t.o)}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-bold">
                                  {fmtBRL(t.g)}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-bold">
                                  {fmtBRL(t.f)}
                                </TableCell>
                              </>
                            )
                          })()}
                          <TableCell />
                          <TableCell />
                        </TableRow>
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}
              {nivel === 'empresa' &&
                !carregando &&
                aggs.length > 0 &&
                aggsFiltrados.length === 0 && (
                  <Card className="border-[#E5D9C8] bg-white shadow-sm">
                    <CardContent className="py-10 text-center text-sm text-[#7A6A5A]">
                      Nenhum promotor encontrado com os filtros selecionados.
                    </CardContent>
                  </Card>
                )}

              {/* Tabela de linhas (promotor) */}
              {linhas.length > 0 && (
                <Card className="border-[#E5D9C8] bg-white shadow-sm">
                  <CardContent className="pt-6">
                    <p className="text-xs text-[#7A6A5A] mb-3">
                      {linhas.length} combinações Cliente × SKU (limite de exibição: 300, ordenadas
                      pela Meta Final) · Promotor: {nomeResp(prom)} · Supervisor: {nomeResp(sup)}
                    </p>
                    <Table>
                      <TableHeader>
                        <TableRow className="border-[#E5D9C8]">
                          <TableHead className="text-[#7A6A5A]">Cliente</TableHead>
                          <TableHead className="text-[#7A6A5A]">Produto</TableHead>
                          <TableHead className="text-[#7A6A5A]">Regime</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">Meta Original</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">GAP</TableHead>
                          <TableHead className="text-[#7A6A5A] text-right">Meta Final</TableHead>
                          <TableHead className="text-[#7A6A5A] text-center">Redistribuir</TableHead>
                          <TableHead className="text-[#7A6A5A] text-center">Memória</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {linhas.map((l) => (
                          <TableRow
                            key={l.meta_linha_id}
                            className="border-[#E5D9C8] cursor-pointer hover:bg-[#FAF6EF]/60"
                            onClick={() =>
                              setAberta(aberta?.meta_linha_id === l.meta_linha_id ? null : l)
                            }
                          >
                            <TableCell className="text-xs">
                              <span className="font-semibold">{l.cliente_nome ?? l.cliente}</span>
                              <span className="text-[#7A6A5A] font-mono"> · {l.cliente}</span>
                            </TableCell>
                            <TableCell className="text-xs">
                              <span className="font-semibold">{l.produto_nome ?? l.sku}</span>
                              <span className="text-[#7A6A5A] font-mono"> · {l.sku}</span>
                            </TableCell>
                            <TableCell>
                              <Badge className="bg-[#D99A2B]/10 text-[#D99A2B] border border-[#D99A2B]/30 text-[10px]">
                                {REGIME_LABEL[l.regime] ?? l.regime}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-mono text-xs">
                              {fmtBRL(l.meta_original)}
                            </TableCell>
                            <TableCell className="text-right font-mono text-xs">
                              {Number(l.gap_linha) !== 0 ? (
                                fmtBRL(l.gap_linha)
                              ) : (
                                <span className="text-[#7A6A5A]">—</span>
                              )}
                            </TableCell>
                            <TableCell className="text-right font-mono text-xs font-semibold">
                              {fmtBRL(l.meta_final)}
                            </TableCell>
                            <TableCell className="text-center whitespace-nowrap">
                              {estado?.habilitado && l.promotor && (
                                <div className="flex justify-center gap-2">
                                  <button
                                    type="button"
                                    className="rounded border px-2 py-1 text-xs"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      void abrirDetalhe(l, false)
                                    }}
                                  >
                                    Loja
                                  </button>
                                  {Number(l.meta_final) > 0 && (
                                    <button
                                      type="button"
                                      className="rounded border px-2 py-1 text-xs"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        void abrirDetalhe(l, true)
                                      }}
                                    >
                                      Produto
                                    </button>
                                  )}
                                </div>
                              )}
                            </TableCell>
                            <TableCell className="text-center">
                              <Calculator className="w-4 h-4 text-[#D99A2B] inline" />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {aberta && <MemoriaPanel linha={aberta} onClose={() => setAberta(null)} />}
            </>
          ))}

        <div className="flex items-center justify-between text-xs text-[#7A6A5A]">
          <span>Fonte: motor oficial T5.x + GAP descido T6.1/T6.3 · Ciclo {mes}</span>
          <button
            onClick={carregar}
            className="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-[#E5D9C8] font-semibold hover:bg-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Atualizar
          </button>
        </div>
      </main>

      <footer className="border-t border-[#E5D9C8] py-4 bg-white text-center text-xs text-[#7A6A5A]">
        Panutrir Alimentos © {new Date().getFullYear()} — Sistema de Controle de Metas
      </footer>
    </div>
  )
}

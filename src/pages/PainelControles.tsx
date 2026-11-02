import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LogOut,
  Target,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  RefreshCw,
  CheckCircle2,
  ClipboardCheck,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { PanutrirLogo } from '@/components/PanutrirLogo'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface ControleGabarito {
  controle_id: string
  modo: 'VALIDACAO_REGRA' | 'EXECUCAO'
  controle: string
  gabarito: string | number
  medido: string | number | null
  diferenca: string | number | null
  diferenca_pct: string | number | null
  tolerancia: string | number
  estado: 'BATE' | 'DIVERGE' | 'SEM MEDIDA'
  referencia_ciclo: string
}

const DESCRICAO_CONTROLE: Record<string, string> = {
  'G-01': 'Meta Final (M-30)',
  'G-02': 'Σ Meta Original',
  'G-03': 'GAP total',
  'G-04': 'Meta Final Indireto',
  'G-05': 'Meta Original Indireto',
  'G-06': 'GAP Indireto',
  'G-07': 'GAP Direto',
  'G-08': 'Média do mix (Q-42)',
  'G-09': 'GAP Branca',
  'G-10': 'GAP Especiais',
  'G-11': 'Combinações Cliente × SKU (M-05)',
  'G-12': 'Combinações em introdução (M-12)',
  'G-13': 'Introdução com último mês = 0 (M-13)',
  'G-14': 'Combinações com piso técnico (M-14)',
  'G-15_lojas': 'Lojas com substituição (M-15)',
  'G-15_valor': 'Valor da substituição',
  'G-16': 'PlufiNut fora Assaí ativas (M-16)',
  'G-17': 'Combinações REVISAR < R$300 (M-26)',
  'G-18': 'Clientes sem estrutura válida (M-27)',
}

const NOTA_DIVERGENCIA: Record<string, string> = {
  'G-03': 'GAP é inverso à Meta Original — converge com D2/D3 (universo)',
  'G-07': 'GAP Direto é inverso à Meta Original — converge com D2/D3 (universo)',
  'G-09': 'Mix por linha exige a carteira do gabarito (carteiras mudaram pós-set/26)',
  'G-10': 'Mix por linha exige a carteira do gabarito (carteiras mudaram pós-set/26)',
}

const NOTA_SEM_MEDIDA: Record<string, string> = {
  'G-09': 'Mix real por promotor no universo provisório não reproduz o controle',
  'G-10': 'Mix real por promotor no universo provisório não reproduz o controle',
}

const fmtBRL = (v: string | number | null) =>
  v == null
    ? '—'
    : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const fmtNum = (v: string | number | null, dec = 0) =>
  v == null ? '—' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec })

const fmtPct = (v: string | number | null) =>
  v == null ? '—' : `${(Number(v) * 100).toFixed(2).replace('.', ',')}%`

function EstadoBadge({ estado }: { estado: ControleGabarito['estado'] }) {
  if (estado === 'BATE')
    return (
      <Badge className="bg-[#2E7D32]/10 text-[#2E7D32] border border-[#2E7D32]/30 hover:bg-[#2E7D32]/15 gap-1">
        <CheckCircle2 className="w-3 h-3" /> Bate
      </Badge>
    )
  if (estado === 'DIVERGE')
    return (
      <Badge className="bg-[#C44133]/10 text-[#C44133] border border-[#C44133]/30 hover:bg-[#C44133]/15 gap-1">
        <AlertTriangle className="w-3 h-3" /> Diverge
      </Badge>
    )
  return (
    <Badge className="bg-[#7A6A5A]/10 text-[#7A6A5A] border border-[#7A6A5A]/30 hover:bg-[#7A6A5A]/15 gap-1">
      <HelpCircle className="w-3 h-3" /> Sem medida
    </Badge>
  )
}

export default function PainelControles() {
  const navigate = useNavigate()
  const { user, session, loading, signOut } = useAuth()
  const [controles, setControles] = useState<ControleGabarito[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user && !session) {
      navigate('/', { replace: true })
    }
  }, [user, session, loading, navigate])

  const carregar = async () => {
    setCarregando(true)
    setErro(null)
    const { data, error } = await supabase
      .from('controle_gabarito')
      .select('*')
      .eq('referencia_ciclo', '2026-10')
      .order('modo')
      .order('controle')
    if (error) setErro(error.message)
    else setControles((data ?? []) as ControleGabarito[])
    setCarregando(false)
  }

  useEffect(() => {
    if (user && session) carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, session])

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

  const resumo = (modo: ControleGabarito['modo']) => {
    const linhas = controles.filter((c) => c.modo === modo)
    return {
      bate: linhas.filter((c) => c.estado === 'BATE').length,
      diverge: linhas.filter((c) => c.estado === 'DIVERGE').length,
      sem: linhas.filter((c) => c.estado === 'SEM MEDIDA').length,
      total: linhas.length,
    }
  }
  const rRegra = resumo('VALIDACAO_REGRA')
  const rExec = resumo('EXECUCAO')

  const userEmail = user?.email || session?.user?.email || 'colaborador@panutrir.com.br'
  const userName =
    user?.user_metadata?.name ||
    userEmail.split('@')[0].replace('.', ' ').replace(/\b\w/g, (l) => l.toUpperCase())

  const tabela = (modo: ControleGabarito['modo']) => {
    const linhas = controles.filter((c) => c.modo === modo)
    if (linhas.length === 0)
      return <p className="text-sm text-[#7A6A5A] py-6 text-center">Nenhum controle registrado.</p>
    return (
      <Table>
        <TableHeader>
          <TableRow className="border-[#E5D9C8]">
            <TableHead className="text-[#7A6A5A]">Controle</TableHead>
            <TableHead className="text-[#7A6A5A]">Descrição</TableHead>
            <TableHead className="text-[#7A6A5A] text-right">Gabarito</TableHead>
            <TableHead className="text-[#7A6A5A] text-right">Medido</TableHead>
            <TableHead className="text-[#7A6A5A] text-right">Diferença</TableHead>
            <TableHead className="text-[#7A6A5A] text-right">Tolerância</TableHead>
            <TableHead className="text-[#7A6A5A] text-center">Estado</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {linhas.map((c) => {
            const isValor = ['G-01', 'G-02', 'G-03', 'G-04', 'G-05', 'G-06', 'G-07', 'G-09', 'G-10', 'G-15_valor'].includes(c.controle)
            const isRatio = c.controle === 'G-08'
            const fmt = (v: string | number | null) => (isRatio ? fmtNum(v, 6) : isValor ? fmtBRL(v) : fmtNum(v))
            return (
              <TableRow key={c.controle_id} className="border-[#E5D9C8]">
                <TableCell className="font-mono text-xs font-semibold text-[#2C1E12]">{c.controle}</TableCell>
                <TableCell className="text-xs text-[#7A6A5A]">{DESCRICAO_CONTROLE[c.controle] ?? '—'}</TableCell>
                <TableCell className="text-right font-mono text-xs text-[#2C1E12]">{fmt(c.gabarito)}</TableCell>
                <TableCell className="text-right font-mono text-xs text-[#2C1E12]">{fmt(c.medido)}</TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {c.diferenca != null && Number(c.diferenca) !== 0 ? (
                    <span className={Number(c.diferenca) > 0 ? 'text-[#C44133]' : 'text-[#2E7D32]'}>
                      {isValor ? fmtBRL(c.diferenca) : fmtNum(c.diferenca, isRatio ? 8 : 0)}
                      {c.diferenca_pct ? ` (${fmtPct(c.diferenca_pct)})` : ''}
                    </span>
                  ) : (
                    <span className="text-[#7A6A5A]">—</span>
                  )}
                </TableCell>
                <TableCell className="text-right font-mono text-xs text-[#7A6A5A]">{fmtPct(c.tolerancia)}</TableCell>
                <TableCell className="text-center">
                  <EstadoBadge estado={c.estado} />
                  {c.estado === 'DIVERGE' && NOTA_DIVERGENCIA[c.controle] && (
                    <p className="text-[10px] text-[#7A6A5A] mt-1 max-w-[180px] mx-auto leading-snug">
                      {NOTA_DIVERGENCIA[c.controle]}
                    </p>
                  )}
                  {c.estado === 'SEM MEDIDA' && NOTA_SEM_MEDIDA[c.controle] && (
                    <p className="text-[10px] text-[#7A6A5A] mt-1 max-w-[180px] mx-auto leading-snug">
                      {NOTA_SEM_MEDIDA[c.controle]}
                    </p>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    )
  }

  return (
    <div className="min-h-screen bg-[#FAF6EF] text-[#2C1E12] flex flex-col font-sans">
      {/* Barra Superior */}
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
              title="Encerrar sessão"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sair</span>
            </button>
          </div>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-8 animate-fade-in">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="w-6 h-6 text-[#D99A2B]" />
            <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight">
              Painel de Controles — Ciclo Out/26
            </h1>
          </div>
          <p className="font-sans text-sm text-[#7A6A5A] max-w-3xl">
            Reconciliação automática contra o gabarito Out/26 (teste T7.1). O modo{' '}
            <strong className="text-[#2C1E12]">Validação da Regra</strong> confere as medidas provadas
            das T6.x com o universo do gabarito — prova de que a regra implementada reproduz o modelo
            do cliente. O modo <strong className="text-[#2C1E12]">Execução</strong> mede o universo
            provisório do motor (−0,23% + carteiras pós-set/26).
          </p>
        </div>

        {/* Resumo */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="border-[#E5D9C8] bg-white shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-serif flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#2E7D32]" />
                Validação da Regra
              </CardTitle>
              <CardDescription className="text-xs">
                Universo do gabarito — medidas provadas nas T6.x
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-2 flex-wrap">
              <Badge className="bg-[#2E7D32]/10 text-[#2E7D32] border border-[#2E7D32]/30">
                {rRegra.bate}/{rRegra.total} batem
              </Badge>
              {rRegra.diverge > 0 && (
                <Badge variant="destructive">{rRegra.diverge} divergem</Badge>
              )}
              {rRegra.sem > 0 && (
                <Badge className="bg-[#7A6A5A]/10 text-[#7A6A5A] border border-[#7A6A5A]/30">
                  {rRegra.sem} sem medida
                </Badge>
              )}
            </CardContent>
          </Card>
          <Card className="border-[#E5D9C8] bg-white shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-serif flex items-center gap-2">
                <Target className="w-4 h-4 text-[#D99A2B]" />
                Execução
              </CardTitle>
              <CardDescription className="text-xs">
                Universo provisório do motor — resíduo documentado
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-2 flex-wrap">
              <Badge className="bg-[#2E7D32]/10 text-[#2E7D32] border border-[#2E7D32]/30">
                {rExec.bate}/{rExec.total} batem
              </Badge>
              {rExec.diverge > 0 && (
                <Badge variant="destructive">{rExec.diverge} divergem (esperado)</Badge>
              )}
              {rExec.sem > 0 && (
                <Badge className="bg-[#7A6A5A]/10 text-[#7A6A5A] border border-[#7A6A5A]/30">
                  {rExec.sem} sem medida
                </Badge>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Tabelas por modo */}
        <Tabs defaultValue="validacao" className="space-y-4">
          <TabsList className="bg-[#E5D9C8]/50">
            <TabsTrigger value="validacao">Validação da Regra</TabsTrigger>
            <TabsTrigger value="execucao">Execução</TabsTrigger>
          </TabsList>
          <TabsContent value="validacao">
            <Card className="border-[#E5D9C8] bg-white shadow-sm">
              <CardContent className="pt-6">{tabela('VALIDACAO_REGRA')}</CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="execucao">
            <Card className="border-[#E5D9C8] bg-white shadow-sm">
              <CardContent className="pt-6">{tabela('EXECUCAO')}</CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {erro && (
          <div className="rounded-xl border border-[#C44133]/30 bg-[#FDE8E6]/50 p-4 text-sm text-[#C44133]">
            Erro ao carregar controles: {erro}
          </div>
        )}

        {/* Rodapé do painel */}
        <div className="flex items-center justify-between text-xs text-[#7A6A5A]">
          <span>
            Fonte: teste automatizado de reconciliação (T7.1) · Ciclo 2026-10 · Reconciliação linha a
            linha pendente da Q-21 (planilha do cliente)
          </span>
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

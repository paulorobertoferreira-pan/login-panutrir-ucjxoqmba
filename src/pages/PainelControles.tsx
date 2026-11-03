import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, HelpCircle, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { PanutrirLogo } from '@/components/PanutrirLogo'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { Tables } from '@/lib/supabase/types'

type ControleGabarito = Tables<'controle_gabarito'>

const DESCRICAO_CONTROLE: Record<string, string> = {
  'G-01': 'Meta Final (M-30)',
  'G-02': 'Σ Meta Original',
  'G-03': 'GAP total',
  'G-04': 'GAP Diretoria (dado)',
  'G-05': 'Meta Indireto',
  'G-06': 'GAP Indireto',
  'G-07': 'GAP Direto',
  'G-08': 'Share Especial médio',
  'G-09': 'GAP Branca',
  'G-10': 'GAP Especiais',
  'G-11': 'Combinações Cliente × SKU',
  'G-12': 'Introduções',
  'G-13': 'Introduções com meta zero',
  'G-14': 'Piso técnico',
  'G-15_lojas': 'Lojas da substituição Assaí',
  'G-15_valor': 'Valor da substituição',
  'G-16': 'PlufiNut fora do Assaí',
  'G-17': 'Combinações REVISAR < R$300 (M-26)',
  'G-18': 'Clientes em auditoria de estrutura',
}

const NOTA_DIVERGENCIA: Record<string, string> = {
  'G-03': 'GAP é inverso à Meta Original — converge com D2/D3 (universo)',
  'G-07': 'GAP Direto é inverso à Meta Original — converge com D2/D3',
}

const NOTA_SEM_MEDIDA: Record<string, string> = {
  'G-09': 'Mix por linha exige a carteira do gabarito (shares por promotor)',
  'G-10': 'Mix por linha exige a carteira do gabarito (shares por promotor)',
}

function fmtBRL(v: number | string | null | undefined) {
  return v == null
    ? '—'
    : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function fmtNum(v: number | string | null | undefined, dec = 0) {
  return v == null
    ? '—'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec })
}

function fmtPct(v: number | string | null | undefined) {
  return v == null ? '—' : `${(Number(v) * 100).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
}

function EstadoBadge({ estado }: { estado: string }) {
  if (estado === 'BATE')
    return (
      <Badge className="bg-[#2E7D32]/10 text-[#2E7D32] border border-[#2E7D32]/30 hover:bg-[#2E7D32]/15 gap-1">
        <CheckCircle2 className="w-3 h-3" /> Bate
      </Badge>
    )
  if (estado === 'DIVERGE')
    return (
      <Badge className="bg-[#C44133]/10 text-[#C44133] border border-[#C44133]/30 hover:bg-[#C44133]/15 gap-1">
        <XCircle className="w-3 h-3" /> Diverge
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
  const [, setCarregando] = useState(true)
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
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sair</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-6">
        <div className="space-y-2">
          <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight">
            Painel de Controles — Ciclo Out/26
          </h1>
          <p className="font-sans text-sm text-[#7A6A5A] max-w-3xl">
            Cada controle do gabarito do cliente ao lado do valor medido no sistema. O modo
            "Validação da Regra" confere a regra implementada com o universo do gabarito; o modo
            "Execução" mede o universo provisório em produção.
          </p>
        </div>

        {/* Cards de resumo */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="border-[#E5D9C8] bg-white shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-serif">Validação da Regra</CardTitle>
              <CardDescription className="text-xs">
                A regra implementada reproduz o modelo do gabarito?
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-4">
              <span className="font-serif text-3xl font-bold text-[#2E7D32]">
                {rRegra.bate}/{rRegra.total}
              </span>
              <div className="flex gap-2">
                {rRegra.diverge > 0 && (
                  <Badge className="bg-[#C44133]/10 text-[#C44133] border border-[#C44133]/30">{rRegra.diverge} diverge</Badge>
                )}
                {rRegra.sem > 0 && (
                  <Badge className="bg-[#7A6A5A]/10 text-[#7A6A5A] border border-[#7A6A5A]/30">{rRegra.sem} sem medida</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-[#E5D9C8] bg-white shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-serif">Execução</CardTitle>
              <CardDescription className="text-xs">
                O universo provisório em produção bate com o gabarito?
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-4">
              <span className="font-serif text-3xl font-bold text-[#2E7D32]">
                {rExec.bate}/{rExec.total}
              </span>
              <div className="flex gap-2">
                {rExec.diverge > 0 && (
                  <Badge className="bg-[#C44133]/10 text-[#C44133] border border-[#C44133]/30">{rExec.diverge} diverge</Badge>
                )}
                {rExec.sem > 0 && (
                  <Badge className="bg-[#7A6A5A]/10 text-[#7A6A5A] border border-[#7A6A5A]/30">{rExec.sem} sem medida</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {erro && (
          <div className="rounded-xl border border-[#C44133]/30 bg-[#FDE8E6]/50 p-4 text-sm text-[#C44133]">
            Erro ao carregar: {erro}
          </div>
        )}

        <Card className="border-[#E5D9C8] bg-white shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-serif">Controles do ciclo</CardTitle>
                <CardDescription className="text-xs">
                  Fonte: teste de gabarito da T7.1, gravado na tabela controle_gabarito
                </CardDescription>
              </div>
              <button
                onClick={carregar}
                className="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-[#E5D9C8] text-xs font-semibold text-[#7A6A5A] hover:bg-[#FAF6EF] transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Atualizar
              </button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#D99A2B] mb-3">
                  Modo: Validação da Regra
                </p>
                {tabela('VALIDACAO_REGRA')}
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#D99A2B] mb-3">
                  Modo: Execução
                </p>
                {tabela('EXECUCAO')}
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      <footer className="border-t border-[#E5D9C8] py-4 bg-white text-center text-xs text-[#7A6A5A]">
        Panutrir Alimentos © {new Date().getFullYear()} — Sistema de Controle de Metas
      </footer>
    </div>
  )
}

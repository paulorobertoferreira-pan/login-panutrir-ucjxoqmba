import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Target, ListChecks, Search, Download, Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { PanutrirLogo } from '@/components/PanutrirLogo'

interface ResumoCiclo {
  meta_original: number | null
  gap: number | null
  meta_final: number | null
  combinacoes: number | null
}

interface ControleResumo {
  estado: string
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, session, loading, signOut } = useAuth()
  const [totais, setTotais] = useState<ResumoCiclo | null>(null)
  const [controles, setControles] = useState<ControleResumo[]>([])
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    if (!loading && !user && !session) {
      navigate('/', { replace: true })
    }
  }, [user, session, loading, navigate])

  useEffect(() => {
    if (user && session) {
      ;(async () => {
        const [regR, ctlR] = await Promise.all([
          supabase
            .from('vw_meta_regime')
            .select('meta_original, gap_linha, meta_final, combinacoes')
            .eq('referencia_ciclo', '2026-10'),
          supabase
            .from('controle_gabarito')
            .select('estado')
            .eq('referencia_ciclo', '2026-10')
            .eq('modo', 'VALIDACAO_REGRA'),
        ])
        if (regR.data) {
          const t = (regR.data as Array<Record<string, number | null>>).reduce(
            (a, r) => ({
              meta_original: (a.meta_original ?? 0) + Number(r.meta_original ?? 0),
              gap: (a.gap ?? 0) + Number(r.gap_linha ?? 0),
              meta_final: (a.meta_final ?? 0) + Number(r.meta_final ?? 0),
              combinacoes: (a.combinacoes ?? 0) + Number(r.combinacoes ?? 0),
            }),
            { meta_original: 0, gap: 0, meta_final: 0, combinacoes: 0 } as ResumoCiclo,
          )
          setTotais(t)
        }
        if (ctlR.data) setControles(ctlR.data as ControleResumo[])
        setCarregando(false)
      })()
    }
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

  const userEmail = user?.email || session?.user?.email || 'colaborador@panutrir.com.br'
  const userName =
    user?.user_metadata?.name ||
    userEmail.split('@')[0].replace('.', ' ').replace(/\b\w/g, (l) => l.toUpperCase())

  const fmtBRL = (v: number | null | undefined) =>
    v == null ? '—' : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  const fmtNum = (v: number | null | undefined) =>
    v == null ? '—' : Number(v).toLocaleString('pt-BR')

  const bate = controles.filter((c) => c.estado === 'BATE').length
  const totalCtl = controles.length
  const pct = totalCtl > 0 ? Math.round((bate / totalCtl) * 100) : null

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
              <LogOut className="w-3.5 h-3.5" />
              <span>Sair</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-6 animate-fade-in">
        <div className="space-y-1">
          <h2 className="font-serif text-xl sm:text-2xl font-bold text-[#2C1E12] flex items-center gap-2">
            <Target className="w-5 h-5 text-[#D99A2B]" />
            Ciclo Out/26
          </h2>
          <p className="font-sans text-sm text-[#7A6A5A]">
            Resumo do ciclo de metas de Outubro/2026 — acesse o painel de controles ou a consulta
            drill-down.
          </p>
        </div>

        {carregando ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-[#D99A2B] animate-spin" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
                <div className="flex items-center justify-between text-[#7A6A5A]">
                  <span className="text-xs font-medium uppercase tracking-wider">Meta Original</span>
                  <Target className="w-4 h-4 text-[#D99A2B]" />
                </div>
                <p className="font-serif text-2xl font-bold text-[#2C1E12]">
                  {fmtBRL(totais?.meta_original)}
                </p>
              </div>

              <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
                <div className="flex items-center justify-between text-[#7A6A5A]">
                  <span className="text-xs font-medium uppercase tracking-wider">GAP Distribuído</span>
                  <ListChecks className="w-4 h-4 text-[#D99A2B]" />
                </div>
                <p className="font-serif text-2xl font-bold text-[#2C1E12]">{fmtBRL(totais?.gap)}</p>
              </div>

              <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
                <div className="flex items-center justify-between text-[#7A6A5A]">
                  <span className="text-xs font-medium uppercase tracking-wider">Meta Final</span>
                  <Target className="w-4 h-4 text-[#2E7D32]" />
                </div>
                <p className="font-serif text-2xl font-bold text-[#2C1E12]">
                  {fmtBRL(totais?.meta_final)}
                </p>
                <p className="text-[11px] text-[#7A6A5A]">
                  {fmtNum(totais?.combinacoes)} combinações Cliente × SKU
                </p>
              </div>
            </div>

            {pct != null && (
              <div className="p-5 rounded-xl bg-white border border-[#E5D9C8] space-y-2">
                <div className="flex items-center justify-between text-[#7A6A5A]">
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Reconciliação — Validação da Regra
                  </span>
                  <span className="font-serif text-sm font-bold text-[#2C1E12]">
                    {bate}/{totalCtl}
                  </span>
                </div>
                <div className="w-full bg-[#E5D9C8] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#2E7D32] h-full" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )}
          </>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => navigate('/controles')}
            className="text-left p-5 rounded-xl bg-white border border-[#E5D9C8] hover:border-[#D99A2B]/50 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="font-serif text-base font-bold text-[#2C1E12]">Painel de Controles</p>
                <p className="text-xs text-[#7A6A5A]">
                  Controles do gabarito lado a lado com o medido (G-01..G-18)
                </p>
              </div>
              <ListChecks className="w-5 h-5 text-[#D99A2B] group-hover:scale-110 transition-transform" />
            </div>
          </button>

          <button
            onClick={() => navigate('/consulta')}
            className="text-left p-5 rounded-xl bg-white border border-[#E5D9C8] hover:border-[#D99A2B]/50 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="font-serif text-base font-bold text-[#2C1E12]">Consulta Drill-down</p>
                <p className="text-xs text-[#7A6A5A]">
                  De Empresa a Cliente × SKU, com a memória de cálculo de cada número
                </p>
              </div>
              <Search className="w-5 h-5 text-[#D99A2B] group-hover:scale-110 transition-transform" />
            </div>
          </button>
        </div>

        <div className="pt-4 border-t border-[#E5D9C8] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#7A6A5A]">
          <div className="flex items-center gap-2">
            <Download className="w-4 h-4 text-[#2E7D32]" />
            <span>
              Exportação Cliente × SKU: <strong className="text-[#2C1E12]">XLSX</strong> (4 abas no
              layout do gabarito) — disponível no painel
            </span>
          </div>
          <div className="font-mono text-[11px] text-[#7A6A5A]">
            ID da sessão: {user?.id?.substring(0, 8)}...
          </div>
        </div>
      </main>

      <footer className="border-t border-[#E5D9C8] py-4 bg-white text-center text-xs text-[#7A6A5A]">
        Panutrir Alimentos © {new Date().getFullYear()} — Sistema de Controle de Metas
      </footer>
    </div>
  )
}
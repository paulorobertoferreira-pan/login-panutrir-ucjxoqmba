import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Target, CheckCircle2, TrendingUp, Award, UserCheck, Shield } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { PanutrirLogo } from '@/components/PanutrirLogo'

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, session, loading, signOut } = useAuth()

  useEffect(() => {
    if (!loading && !user && !session) {
      navigate('/', { replace: true })
    }
  }, [user, session, loading, navigate])

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

            <div className="w-9 h-9 rounded-full bg-[#D99A2B]/15 text-[#D99A2B] font-serif font-bold text-sm flex items-center justify-center border border-[#D99A2B]/30">
              {userName.charAt(0)}
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
        {/* Banner de Boas-vindas */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#3E2A1E] to-[#5C3F2D] text-[#FAF6EF] p-6 sm:p-10 shadow-lg border border-[#3E2A1E]">
          <div className="relative z-10 space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF6EF]/10 border border-[#D99A2B]/40 text-xs font-medium text-[#FAF6EF]">
              <Shield className="w-3.5 h-3.5 text-[#D99A2B]" />
              <span>Sessão autenticada via Supabase</span>
            </div>
            <h1 className="font-serif text-2xl sm:text-4xl font-bold tracking-tight">
              Olá, {userName}!
            </h1>
            <p className="font-sans text-sm sm:text-base text-[#FAF6EF]/85 leading-relaxed">
              Você está conectado com sucesso ao Sistema de Controle de Metas da Panutrir.
            </p>
          </div>

          {/* Efeito decorativo sutil no card */}
          <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 pointer-events-none flex items-center justify-center">
            <Target className="w-64 h-64 text-[#FAF6EF]" />
          </div>
        </div>

        {/* Status de Construção do Módulo */}
        <div className="bg-white rounded-2xl border border-[#E5D9C8] p-6 sm:p-8 space-y-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5D9C8]">
            <div className="space-y-1">
              <h2 className="font-serif text-xl sm:text-2xl font-bold text-[#2C1E12] flex items-center gap-2">
                <Target className="w-6 h-6 text-[#D99A2B]" />
                <span>Dashboard de Metas Operacionais</span>
              </h2>
              <p className="font-sans text-sm text-[#7A6A5A]">
                Módulo em construção — a autenticação foi concluída com sucesso.
              </p>
            </div>
            <span className="self-start sm:self-center px-3 py-1 rounded-full bg-[#D99A2B]/15 text-[#D99A2B] text-xs font-semibold uppercase tracking-wider">
              Em Construção
            </span>
          </div>

          {/* Grid de Cards Resumo para pré-visualização */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
              <div className="flex items-center justify-between text-[#7A6A5A]">
                <span className="text-xs font-medium uppercase tracking-wider">
                  Meta Mensal de Pães
                </span>
                <TrendingUp className="w-4 h-4 text-[#D99A2B]" />
              </div>
              <p className="font-serif text-2xl font-bold text-[#2C1E12]">94.2%</p>
              <div className="w-full bg-[#E5D9C8] h-2 rounded-full overflow-hidden">
                <div className="bg-[#D99A2B] h-full w-[94%]" />
              </div>
            </div>

            <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
              <div className="flex items-center justify-between text-[#7A6A5A]">
                <span className="text-xs font-medium uppercase tracking-wider">
                  Conformidade e Qualidade
                </span>
                <CheckCircle2 className="w-4 h-4 text-[#2E7D32]" />
              </div>
              <p className="font-serif text-2xl font-bold text-[#2C1E12]">99.1%</p>
              <div className="w-full bg-[#E5D9C8] h-2 rounded-full overflow-hidden">
                <div className="bg-[#2E7D32] h-full w-[99%]" />
              </div>
            </div>

            <div className="p-5 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] space-y-2">
              <div className="flex items-center justify-between text-[#7A6A5A]">
                <span className="text-xs font-medium uppercase tracking-wider">
                  Eficiência da Linha
                </span>
                <Award className="w-4 h-4 text-[#D99A2B]" />
              </div>
              <p className="font-serif text-2xl font-bold text-[#2C1E12]">91.8%</p>
              <div className="w-full bg-[#E5D9C8] h-2 rounded-full overflow-hidden">
                <div className="bg-[#D99A2B] h-full w-[92%]" />
              </div>
            </div>
          </div>

          {/* Dados do Usuário Ativo */}
          <div className="pt-4 border-t border-[#E5D9C8] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#7A6A5A]">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-[#2E7D32]" />
              <span>
                Colaborador autenticado: <strong className="text-[#2C1E12]">{userEmail}</strong>
              </span>
            </div>
            <div className="font-mono text-[11px] text-[#7A6A5A]">
              ID da sessão: {user?.id?.substring(0, 8)}...
            </div>
          </div>
        </div>
      </main>

      {/* Rodapé */}
      <footer className="border-t border-[#E5D9C8] py-4 bg-white text-center text-xs text-[#7A6A5A]">
        Panutrir Alimentos © {new Date().getFullYear()} — Sistema de Controle de Metas
      </footer>
    </div>
  )
}

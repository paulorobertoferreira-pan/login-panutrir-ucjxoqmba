import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Eye,
  Loader2,
  LogOut,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { PanutrirLogo } from '@/components/PanutrirLogo'

type OperationKey =
  | 'criar_configurar_ciclo'
  | 'importar'
  | 'homologar'
  | 'editar_catalogo'
  | 'fechar_snapshot'
  | 'exportar'

type Operation = {
  key: OperationKey
  label: string
  description: string
  expectedForTestAccount: 'allowed' | 'denied'
}

type AuditEvent = {
  event_id: string
  operation_key: OperationKey
  decision: 'allowed' | 'denied'
  reason: string | null
  correlation_id: string
  created_at: string
  target_type: string | null
}

type RoleAssignment = {
  role_key: string
}

type SupabaseError = {
  message: string
}

type QueryResponse<T> = {
  data: T[] | null
  error: SupabaseError | null
}

type QueryBuilder<T> = {
  select: (columns: string) => QueryBuilder<T>
  eq: (column: string, value: string) => QueryBuilder<T>
  is: (column: string, value: null) => QueryBuilder<T>
  order: (column: string, options: { ascending: boolean }) => QueryBuilder<T>
  limit: (count: number) => Promise<QueryResponse<T>>
}

type AuthorizationClient = {
  rpc: (
    functionName: 'authorize_operation',
    params: {
      p_operation_key: OperationKey
      p_target_type: string
      p_target_id: string
      p_reason: string
      p_correlation_id: string
    },
  ) => Promise<{ data: boolean | null; error: SupabaseError | null }>
  from: (table: string) => QueryBuilder<unknown>
}

const authorizationClient = supabase as unknown as AuthorizationClient

const OPERATIONS: Operation[] = [
  {
    key: 'criar_configurar_ciclo',
    label: 'Criar ou configurar ciclo',
    description: 'Abrir ou ajustar um ciclo mensal em preparação.',
    expectedForTestAccount: 'denied',
  },
  {
    key: 'importar',
    label: 'Importar dados',
    description: 'Enviar dados para a área de preparação.',
    expectedForTestAccount: 'denied',
  },
  {
    key: 'homologar',
    label: 'Homologar pendências',
    description: 'Revisar e liberar pendências de qualidade.',
    expectedForTestAccount: 'denied',
  },
  {
    key: 'editar_catalogo',
    label: 'Editar catálogo',
    description: 'Alterar produtos, responsáveis e territórios.',
    expectedForTestAccount: 'allowed',
  },
  {
    key: 'fechar_snapshot',
    label: 'Fechar snapshot',
    description: 'Congelar a versão de dados do ciclo.',
    expectedForTestAccount: 'allowed',
  },
  {
    key: 'exportar',
    label: 'Exportar diagnóstico',
    description: 'Exportar diagnóstico e evidências do ciclo.',
    expectedForTestAccount: 'denied',
  },
]

const ROLE_LABELS: Record<string, string> = {
  administrador: 'Administrador',
  operador: 'Operador',
  revisor: 'Revisor',
  gestor_dados: 'Gestor de dados',
  auditor: 'Auditor',
  consulta: 'Consulta',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function PermissionTest() {
  const navigate = useNavigate()
  const { user, session, loading, signOut } = useAuth()
  const [role, setRole] = useState('Carregando…')
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [runningOperation, setRunningOperation] = useState<OperationKey | null>(null)
  const [results, setResults] = useState<Partial<Record<OperationKey, boolean>>>({})
  const [errorMessage, setErrorMessage] = useState('')
  const [auditLoading, setAuditLoading] = useState(false)

  const userEmail = user?.email || session?.user?.email || 'conta de teste'

  const roleDescription = useMemo(() => {
    if (role === 'Carregando…') return 'Consultando o papel desta conta…'
    if (role === 'Não identificado') return 'Papel não identificado'
    return `Papel atual: ${role}`
  }, [role])

  useEffect(() => {
    if (!loading && !user && !session) {
      navigate('/', { replace: true })
      return
    }

    if (user) {
      void loadRole(user.id)
      void loadAudit(user.id)
    }
  }, [loading, navigate, session, user])

  async function loadRole(userId: string) {
    const response = await authorizationClient
      .from('profile_role_assignments')
      .select('role_key')
      .eq('profile_id', userId)
      .is('revoked_at', null)
      .limit(1)

    const assignments = (response.data ?? []) as RoleAssignment[]
    if (!response.error && assignments[0]) {
      setRole(ROLE_LABELS[assignments[0].role_key] || assignments[0].role_key)
    } else if (response.error) {
      setRole('Não identificado')
    }
  }

  async function loadAudit(userId: string) {
    setAuditLoading(true)
    const response = await authorizationClient
      .from('authorization_audit_log')
      .select('event_id, operation_key, decision, reason, correlation_id, created_at, target_type')
      .eq('actor_id', userId)
      .eq('target_type', 'human_test')
      .order('created_at', { ascending: false })
      .limit(8)

    if (response.error) {
      setErrorMessage(`Não foi possível carregar o histórico: ${response.error.message}`)
    } else {
      setAuditEvents((response.data ?? []) as AuditEvent[])
    }
    setAuditLoading(false)
  }

  async function testOperation(operation: Operation) {
    if (!user || runningOperation) return

    setErrorMessage('')
    setRunningOperation(operation.key)
    const correlationId = crypto.randomUUID()
    const response = await authorizationClient.rpc('authorize_operation', {
      p_operation_key: operation.key,
      p_target_type: 'human_test',
      p_target_id: `t11-${operation.key}`,
      p_reason: 'Teste manual da matriz de permissões T1.1',
      p_correlation_id: correlationId,
    })

    if (response.error || response.data === null) {
      setErrorMessage(response.error?.message || 'Não foi possível realizar o teste.')
    } else {
      setResults((current) => ({ ...current, [operation.key]: response.data as boolean }))
      await loadAudit(user.id)
    }
    setRunningOperation(null)
  }

  async function handleSignOut() {
    await signOut()
    navigate('/', { replace: true })
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF6EF]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-[#D99A2B] border-t-transparent rounded-full animate-spin" />
          <p className="font-sans text-sm text-[#7A6A5A]">Carregando ambiente...</p>
        </div>
      </div>
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
              Teste de permissões
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-[#E5D9C8] text-xs font-semibold text-[#7A6A5A] hover:text-[#2C1E12] hover:border-[#D99A2B]/60 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Voltar</span>
            </button>
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
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#3E2A1E] to-[#5C3F2D] text-[#FAF6EF] p-6 sm:p-10 shadow-lg border border-[#3E2A1E]">
          <div className="relative z-10 space-y-3 max-w-3xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF6EF]/10 border border-[#D99A2B]/40 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-[#D99A2B]" />
              <span>Teste seguro — não altera dados do sistema</span>
            </div>
            <h1 className="font-serif text-2xl sm:text-4xl font-bold tracking-tight">
              Teste de permissões
            </h1>
            <p className="text-sm sm:text-base text-[#FAF6EF]/85 leading-relaxed">
              Clique em uma operação para conferir se esta conta pode executá-la. O resultado é
              consultado no banco e a tentativa fica registrada no histórico.
            </p>
          </div>
          <Eye className="absolute right-8 top-1/2 -translate-y-1/2 w-40 h-40 text-[#FAF6EF] opacity-10" />
        </section>

        <section className="bg-white rounded-2xl border border-[#E5D9C8] p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wider font-semibold text-[#7A6A5A]">
                Conta em uso
              </p>
              <p className="text-base font-semibold text-[#2C1E12] mt-1">{userEmail}</p>
              <p className="text-sm text-[#7A6A5A] mt-1">{roleDescription}</p>
            </div>
            <div className="rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] px-4 py-3 text-sm text-[#7A6A5A] max-w-md">
              <strong className="text-[#2C1E12]">Como testar:</strong> para a conta sintética atual,
              “Editar catálogo” e “Fechar snapshot” devem mostrar Permitido. As outras opções devem
              mostrar Negado.
            </div>
          </div>
        </section>

        {errorMessage && (
          <div
            className="rounded-xl border border-[#C44133]/30 bg-[#FDE8E6] px-4 py-3 text-sm text-[#8F2E25]"
            role="alert"
          >
            {errorMessage}
          </div>
        )}

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {OPERATIONS.map((operation) => {
            const result = results[operation.key]
            const isRunning = runningOperation === operation.key
            const resultLabel =
              result === undefined ? 'Ainda não testado' : result ? 'Permitido' : 'Negado'
            const resultClass =
              result === undefined
                ? 'text-[#7A6A5A] bg-[#FAF6EF]'
                : result
                  ? 'text-[#2E7D32] bg-[#E9F5EA]'
                  : 'text-[#8F2E25] bg-[#FDE8E6]'

            return (
              <article
                key={operation.key}
                className="bg-white rounded-2xl border border-[#E5D9C8] p-5 shadow-sm flex flex-col gap-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-semibold text-[#2C1E12]">{operation.label}</h2>
                    <p className="text-sm text-[#7A6A5A] mt-1 leading-relaxed">
                      {operation.description}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${resultClass}`}
                  >
                    {resultLabel}
                  </span>
                </div>
                <button
                  onClick={() => testOperation(operation)}
                  disabled={Boolean(runningOperation)}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#D99A2B] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#BF841F] disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
                >
                  {isRunning ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="w-4 h-4" />
                  )}
                  {isRunning ? 'Verificando…' : 'Testar esta operação'}
                </button>
              </article>
            )
          })}
        </section>

        <section className="bg-white rounded-2xl border border-[#E5D9C8] p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3 pb-4 border-b border-[#E5D9C8]">
            <div>
              <h2 className="font-serif text-xl font-bold text-[#2C1E12] flex items-center gap-2">
                <Clock3 className="w-5 h-5 text-[#D99A2B]" />
                Histórico dos seus testes
              </h2>
              <p className="text-sm text-[#7A6A5A] mt-1">
                Mostramos somente os testes feitos por esta conta.
              </p>
            </div>
            <button
              onClick={() => void loadAudit(user.id)}
              disabled={auditLoading}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#7A6A5A] hover:text-[#2C1E12] disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${auditLoading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>

          {auditEvents.length === 0 ? (
            <div className="py-8 text-center text-sm text-[#7A6A5A]">
              Nenhum teste realizado ainda.
            </div>
          ) : (
            <div className="divide-y divide-[#E5D9C8]">
              {auditEvents.map((event) => {
                const operation = OPERATIONS.find((item) => item.key === event.operation_key)
                const allowed = event.decision === 'allowed'
                return (
                  <div
                    key={event.event_id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                  >
                    <div className="flex items-center gap-3">
                      {allowed ? (
                        <CheckCircle2 className="w-5 h-5 text-[#2E7D32]" />
                      ) : (
                        <XCircle className="w-5 h-5 text-[#C44133]" />
                      )}
                      <div>
                        <p className="text-sm font-semibold text-[#2C1E12]">
                          {operation?.label || event.operation_key}
                        </p>
                        <p className="text-xs text-[#7A6A5A]">{formatDate(event.created_at)}</p>
                      </div>
                    </div>
                    <span
                      className={`self-start sm:self-auto rounded-full px-2.5 py-1 text-xs font-semibold ${allowed ? 'text-[#2E7D32] bg-[#E9F5EA]' : 'text-[#8F2E25] bg-[#FDE8E6]'}`}
                    >
                      {allowed ? 'Permitido e registrado' : 'Negado e registrado'}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      </main>

      <footer className="border-t border-[#E5D9C8] py-4 bg-white text-center text-xs text-[#7A6A5A]">
        Panutrir Alimentos © {new Date().getFullYear()} — Tela de teste da T1.1
      </footer>
    </div>
  )
}

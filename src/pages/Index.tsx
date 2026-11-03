import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  KeyRound,
  X,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { PanutrirLogo } from '@/components/PanutrirLogo'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export default function Index() {
  const navigate = useNavigate()
  const { signIn, resetPassword, user, session, loading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [emailTouched, setEmailTouched] = useState(false)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')

  // Modal "Esqueceu sua senha?"
  const [resetOpen, setResetOpen] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetSending, setResetSending] = useState(false)
  const [resetDone, setResetDone] = useState(false)
  const [resetError, setResetError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && (user || session)) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, session, loading, navigate])

  // Validação de e-mail em tempo real
  const validateEmail = (value: string) => {
    if (!value.trim()) return 'Digite seu e-mail'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'E-mail inválido'
    return ''
  }

  // Validação de senha em tempo real
  const validatePassword = (value: string) => {
    if (!value) return 'Digite sua senha'
    if (value.length < 8) return 'A senha deve ter pelo menos 8 caracteres'
    return ''
  }

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
    if (emailTouched) setEmailError(validateEmail(e.target.value))
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value)
    if (passwordTouched) setPasswordError(validatePassword(e.target.value))
  }

  const handleEmailBlur = () => {
    setEmailTouched(true)
    setEmailError(validateEmail(email))
  }

  const handlePasswordBlur = () => {
    setPasswordTouched(true)
    setPasswordError(validatePassword(password))
  }

  const handleFillDemo = () => {
    setEmail('paulo.ferreira@panutrir.com.br')
    setPassword('V8kR3mQ2wLpX7nZt9sJd')
    setEmailTouched(true)
    setPasswordTouched(true)
    setEmailError('')
    setPasswordError('')
    setFormError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const eErr = validateEmail(email)
    const pErr = validatePassword(password)
    setEmailError(eErr)
    setPasswordError(pErr)
    setEmailTouched(true)
    setPasswordTouched(true)
    if (eErr || pErr) return

    setSubmitting(true)
    setFormError(null)
    const { error } = await signIn(email.trim(), password)
    if (error) {
      setFormError(
        error.message === 'Invalid login credentials'
          ? 'E-mail ou senha incorretos. Verifique e tente novamente.'
          : error.message,
      )
    }
    setSubmitting(false)
  }

  const handleResetPassword = async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(resetEmail)) {
      setResetError('Digite um e-mail válido')
      return
    }
    setResetSending(true)
    setResetError(null)
    const { error } = await resetPassword(resetEmail.trim())
    if (error) setResetError(error.message)
    else setResetDone(true)
    setResetSending(false)
  }

  return (
    <div className="min-h-screen flex bg-[#FAF6EF] text-[#2C1E12] font-sans">
      {/* Painel Esquerdo - Identidade */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden">
        <img
          src="https://img.usecurling.com/p/1600/1200?q=artisan+bread"
          alt="Pães artesanais Panutrir"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-[#3E2A1E]/95 via-[#3E2A1E]/85 to-[#5C3F2D]/70" />
        <div className="relative z-10 flex flex-col justify-between p-10 xl:p-14 w-full">
          <PanutrirLogo variant="light" size="lg" showSlogan={true} />

          <div className="space-y-6 max-w-lg">
            <span className="inline-block px-3 py-1 rounded-full bg-[#FAF6EF]/10 border border-[#D99A2B]/40 text-[#FAF6EF] text-xs font-medium tracking-wider uppercase">
              Painel Corporativo
            </span>
            <h1 className="font-serif text-4xl xl:text-5xl font-bold text-[#FAF6EF] leading-tight tracking-tight">
              Sistema de Controle de Metas
            </h1>
            <p className="font-sans text-[#FAF6EF]/85 text-base xl:text-lg leading-relaxed">
              Ferramenta interna da Panutrir para gestão de desempenho, alinhamento estratégico de
              produção e acompanhamento de objetivos operacionais.
            </p>
            <div className="flex flex-col gap-3 pt-2">
              <div className="flex items-center gap-3 text-[#FAF6EF]/90">
                <span className="w-2 h-2 rounded-full bg-[#D99A2B]" />
                <span className="text-sm">Metas de Produção</span>
              </div>
              <div className="flex items-center gap-3 text-[#FAF6EF]/90">
                <span className="w-2 h-2 rounded-full bg-[#D99A2B]" />
                <span className="text-sm">Controle de Qualidade</span>
              </div>
            </div>
          </div>

          <p className="text-[#FAF6EF]/60 text-xs">
            Panutrir Alimentos © {new Date().getFullYear()} · Sapopema • PR
          </p>
        </div>
      </div>

      {/* Painel Direito - Login */}
      <div className="w-full lg:w-[45%] flex flex-col">
        <div className="w-full max-w-[420px] flex items-center justify-end">
          <button
            type="button"
            onClick={handleFillDemo}
            className="text-xs text-[#7A6A5A] hover:text-[#D99A2B] font-medium flex items-center gap-1.5 py-1 px-2.5 rounded-full hover:bg-black/5 transition-colors border border-transparent hover:border-[#E5D9C8]"
            title="Preencher com usuário de teste criado na migração"
          >
            <CheckCircle className="w-3.5 h-3.5 text-[#D99A2B]" />
            <span>Preencher conta de teste</span>
          </button>
        </div>

        {/* Container Centralizado de 420px */}
        <div className="w-full max-w-[420px] my-auto space-y-7 animate-in fade-in slide-in-from-bottom-5 duration-500">
          {/* Logo exibido no mobile acima do título */}
          <div className="flex justify-center md:hidden mb-4">
            <PanutrirLogo variant="dark" size="md" showSlogan={true} />
          </div>

          <div className="space-y-2">
            <h2 className="font-serif text-3xl font-bold tracking-tight">Bem-vindo de volta</h2>
            <p className="text-sm text-[#7A6A5A]">Acesse sua conta para continuar</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="text-sm font-semibold text-[#2C1E12] flex items-center gap-2"
              >
                <Mail className="w-4 h-4 text-[#D99A2B]" />
                E-mail
              </label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com.br"
                value={email}
                onChange={handleEmailChange}
                onBlur={handleEmailBlur}
                className={`h-11 bg-white border-[#E5D9C8] focus-visible:ring-[#D99A2B]/40 focus-visible:border-[#D99A2B] ${
                  emailError ? 'border-[#C44133]' : ''
                }`}
                autoComplete="email"
              />
              {emailError && (
                <p className="text-xs text-[#C44133] flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {emailError}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-sm font-semibold text-[#2C1E12] flex items-center gap-2"
                >
                  <Lock className="w-4 h-4 text-[#D99A2B]" />
                  Senha
                </label>
                <button
                  type="button"
                  onClick={() => setResetOpen(true)}
                  className="text-xs text-[#7A6A5A] hover:text-[#D99A2B] font-medium"
                >
                  Esqueceu sua senha?
                </button>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Digite sua senha"
                  value={password}
                  onChange={handlePasswordChange}
                  onBlur={handlePasswordBlur}
                  className={`h-11 pr-10 bg-white border-[#E5D9C8] focus-visible:ring-[#D99A2B]/40 focus-visible:border-[#D99A2B] ${
                    passwordError ? 'border-[#C44133]' : ''
                  }`}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#7A6A5A] hover:text-[#2C1E12]"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {passwordError && (
                <p className="text-xs text-[#C44133] flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {passwordError}
                </p>
              )}
            </div>

            {formError && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/30 text-[#C44133] text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-[#D99A2B] hover:bg-[#C4881F] text-white font-semibold text-base shadow-md hover:shadow-lg transition-all"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                <>
                  Entrar
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Acesso de teste interno */}
          <div className="pt-2 border-t border-[#E5D9C8]">
            <div className="flex items-center justify-between gap-2 rounded-xl bg-[#FAF6EF] border border-[#E5D9C8] px-4 py-3">
              <div className="min-w-0">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#7A6A5A] flex items-center gap-1">
                  <KeyRound className="w-3 h-3 text-[#D99A2B]" />
                  Acesso de teste interno
                </p>
                <p className="text-xs text-[#7A6A5A] font-mono truncate mt-0.5">
                  paulo.ferreira@panutrir.com.br • V8kR3mQ2wLpX7nZt9sJd
                </p>
              </div>
              <button
                type="button"
                onClick={handleFillDemo}
                className="shrink-0 text-xs font-semibold text-[#D99A2B] hover:text-[#C4881F] px-3 py-1.5 rounded-lg hover:bg-[#D99A2B]/10 transition-colors"
              >
                Usar credenciais
              </button>
            </div>
          </div>
        </div>

        <p className="w-full max-w-[420px] pb-6 text-center text-[11px] text-[#7A6A5A]/70">
          Ambiente interno restrito — acesso autorizado somente a colaboradores da Panutrir.
        </p>
      </div>

      {/* Modal Esqueceu sua senha */}
      <Dialog open={resetOpen} onOpenChange={setResetOpen}>
        <DialogContent className="sm:max-w-md bg-white">
          <DialogHeader>
            <DialogTitle className="font-serif text-xl flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-[#D99A2B]" />
              Recuperar senha
            </DialogTitle>
            <DialogDescription>
              Informe seu e-mail corporativo e enviaremos um link para redefinir sua senha.
            </DialogDescription>
          </DialogHeader>
          {resetDone ? (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-[#E8F5E9] border border-[#2E7D32]/30 text-[#2E7D32] text-sm">
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>
                E-mail de recuperação enviado para <strong>{resetEmail}</strong>. Verifique sua
                caixa de entrada.
              </span>
            </div>
          ) : (
            <div className="space-y-4">
              <Input
                type="email"
                placeholder="seu@email.com.br"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                className="h-11 bg-white border-[#E5D9C8]"
              />
              {resetError && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/30 text-[#C44133] text-sm">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{resetError}</span>
                </div>
              )}
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setResetOpen(false)}>
              <X className="w-4 h-4" /> Fechar
            </Button>
            {!resetDone && (
              <Button
                onClick={handleResetPassword}
                disabled={resetSending}
                className="bg-[#D99A2B] hover:bg-[#C4881F] text-white"
              >
                {resetSending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Enviando...
                  </>
                ) : (
                  'Enviar link'
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertTriangle,
  Loader2,
  Sparkles,
  CheckCircle,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { PanutrirLogo } from '@/components/PanutrirLogo'
import { ForgotPasswordModal } from '@/components/ForgotPasswordModal'

export default function Index() {
  const navigate = useNavigate()
  const { user, session, loading: authLoading, signIn } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Estados de validação
  const [emailTouched, setEmailTouched] = useState(false)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Modal "Esqueceu sua senha?"
  const [isForgotModalOpen, setIsForgotModalOpen] = useState(false)

  // Imagem artesanal de alta qualidade de pães e trigo da CDN autorizada
  const breadBgImage =
    'https://img.usecurling.com/p/1200/1600?q=artisan+bread+bakery+wheat&color=warm'

  // Redirecionamento se já autenticado
  useEffect(() => {
    if (!authLoading && (user || session)) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, session, authLoading, navigate])

  // Validação de e-mail em tempo real
  const validateEmail = (value: string): string => {
    const trimmed = value.trim()
    if (!trimmed) {
      return 'Informe seu e-mail'
    }
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!regex.test(trimmed)) {
      return 'Informe um e-mail válido'
    }
    return ''
  }

  // Validação de senha em tempo real
  const validatePassword = (value: string): string => {
    if (!value) {
      return 'Digite sua senha'
    }
    if (value.length < 8) {
      return 'A senha deve ter pelo menos 8 caracteres'
    }
    return ''
  }

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setEmail(val)
    if (formError) setFormError(null)
    if (emailTouched) {
      setEmailError(validateEmail(val))
    }
  }

  const handleEmailBlur = () => {
    setEmailTouched(true)
    setEmailError(validateEmail(email))
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setPassword(val)
    if (formError) setFormError(null)
    if (passwordTouched) {
      setPasswordError(validatePassword(val))
    }
  }

  const handlePasswordBlur = () => {
    setPasswordTouched(true)
    setPasswordError(validatePassword(password))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailTouched(true)
    setPasswordTouched(true)

    const emailErr = validateEmail(email)
    const passErr = validatePassword(password)
    setEmailError(emailErr)
    setPasswordError(passErr)

    if (emailErr || passErr) {
      return
    }

    setIsSubmitting(true)
    setFormError(null)

    try {
      const { error } = await signIn(email.trim(), password)

      if (error) {
        console.warn('Erro de login retornado pelo Supabase:', error.message)
        const msg = error.message.toLowerCase()
        if (msg.includes('invalid login credentials') || msg.includes('invalid credentials')) {
          setFormError('E-mail ou senha incorretos')
        } else if (msg.includes('email not confirmed')) {
          setFormError('E-mail ainda não confirmado. Verifique sua caixa de entrada.')
        } else if (msg.includes('user not found')) {
          setFormError('Usuário não encontrado')
        } else if (msg.includes('too many requests') || msg.includes('rate limit')) {
          setFormError('Muitas tentativas sem sucesso. Aguarde alguns instantes.')
        } else {
          setFormError('Falha ao autenticar. Verifique suas credenciais.')
        }
      } else {
        // Redireciona para /dashboard
        navigate('/dashboard')
      }
    } catch (err) {
      console.error(err)
      setFormError('Não foi possível conectar ao servidor. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Preenche dados de demonstração da Panutrir (para facilitar a avaliação)
  const handleFillDemo = () => {
    setEmail('paulo.ferreira@panutrir.com.br')
    setPassword('Skip@Pass')
    setEmailTouched(true)
    setPasswordTouched(true)
    setEmailError('')
    setPasswordError('')
    setFormError(null)
  }

  return (
    <div className="relative w-full min-h-screen flex flex-col lg:flex-row bg-[#FAF6EF] overflow-hidden animate-fade-in font-sans">
      {/* ============================================================== */}
      {/* 1. PAINEL DE MARCA À ESQUERDA (Desktop 50%, Tablet 40%, Oculto em Mobile) */}
      {/* ============================================================== */}
      <section
        aria-label="Identidade Visual Panutrir"
        className="hidden md:flex md:w-[40%] lg:w-1/2 relative min-h-screen flex-col justify-between p-8 lg:p-14 overflow-hidden select-none"
      >
        {/* Imagem de Fundo com Fallback Texturizado */}
        <div
          className="absolute inset-0 bg-cover bg-center transition-transform duration-1000 scale-105"
          style={{
            backgroundImage: `url(${breadBgImage})`,
            backgroundColor: '#3E2A1E',
          }}
        />

        {/* Gradiente Duplo Panutrir: Marrom Quente Profundo (inferior-esquerdo) a Âmbar (superior-direito) */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'linear-gradient(135deg, rgba(62, 42, 30, 0.92) 0%, rgba(62, 42, 30, 0.82) 45%, rgba(217, 154, 43, 0.42) 100%)',
          }}
        />

        {/* Textura sutil pontilhada para acabamento nobre */}
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(rgba(250, 246, 239, 0.4) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />

        {/* Topo do Painel Esquerdo: Logotipo da Panutrir */}
        <header className="relative z-10 animate-fade-in-down">
          <PanutrirLogo variant="light" size="lg" showSlogan={true} />
        </header>

        {/* Centro/Base do Painel Esquerdo: Título e Mensagem Institucional */}
        <div className="relative z-10 my-auto py-10 max-w-lg space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FAF6EF]/10 border border-[#D99A2B]/40 text-[#FAF6EF] text-xs font-medium tracking-wider uppercase backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#D99A2B]" />
            <span>Painel Corporativo</span>
          </div>

          <h1 className="font-serif text-3xl lg:text-4xl xl:text-5xl font-bold text-[#FAF6EF] leading-[1.15] tracking-tight drop-shadow-sm">
            Sistema de Controle de Metas
          </h1>

          {/* Linha Divisória Fina Dourada */}
          <div className="w-20 h-1 bg-gradient-to-r from-[#D99A2B] to-[#FAF6EF]/20 rounded-full" />

          <p className="font-sans text-base lg:text-lg text-[#FAF6EF]/85 leading-relaxed font-light">
            Ferramenta interna da Panutrir para gestão de desempenho, alinhamento estratégico de
            produção e acompanhamento de objetivos operacionais.
          </p>

          {/* Badges de Destaque da Marca Panutrir */}
          <div className="pt-4 grid grid-cols-2 gap-3 text-xs text-[#FAF6EF]/90 font-medium">
            <div className="flex items-center gap-2 bg-[#3E2A1E]/40 border border-[#FAF6EF]/10 rounded-lg p-2.5 backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-[#D99A2B]" />
              <span>Metas de Produção</span>
            </div>
            <div className="flex items-center gap-2 bg-[#3E2A1E]/40 border border-[#FAF6EF]/10 rounded-lg p-2.5 backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-[#D99A2B]" />
              <span>Controle de Qualidade</span>
            </div>
          </div>
        </div>

        {/* Rodapé do Painel Esquerdo */}
        <footer className="relative z-10 pt-4 border-t border-[#FAF6EF]/15 flex items-center justify-between text-xs text-[#FAF6EF]/60">
          <span>Panutrir Alimentos © {new Date().getFullYear()}</span>
          <span>Sapopema • PR</span>
        </footer>
      </section>

      {/* ============================================================== */}
      {/* 2. PAINEL DO FORMULÁRIO À DIREITA (Fundo Creme #FAF6EF) */}
      {/* ============================================================== */}
      <section
        aria-label="Acesso ao Sistema"
        className="w-full md:w-[60%] lg:w-1/2 min-h-screen flex flex-col justify-between items-center py-8 px-6 sm:px-12 lg:px-16 bg-[#FAF6EF]"
      >
        {/* Barra superior de auxílio / demo pill */}
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

          {/* Cabeçalho do Formulário */}
          <div className="space-y-2 text-left">
            <h2 className="font-serif text-[28px] sm:text-[32px] font-bold text-[#2C1E12] leading-tight tracking-[0.5px]">
              Bem-vindo de volta
            </h2>
            <p className="font-sans text-sm sm:text-[15px] text-[#7A6A5A]">
              Acesse sua conta para continuar
            </p>
          </div>

          {/* Formulário Principal */}
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Campo E-mail */}
            <div className="space-y-1.5">
              <label htmlFor="email-input" className="block text-sm font-medium text-[#2C1E12]">
                E-mail
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7A6A5A]">
                  <Mail className="w-[18px] h-[18px]" />
                </div>
                <input
                  id="email-input"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={handleEmailChange}
                  onBlur={handleEmailBlur}
                  placeholder="seu@email.com.br"
                  className={`w-full h-[50px] pl-11 pr-4 rounded-lg bg-white border text-[15px] text-[#2C1E12] placeholder-[#7A6A5A]/60 transition-all duration-200 outline-none ${
                    emailError && emailTouched
                      ? 'border-[#C44133] focus:border-[#C44133] focus:ring-4 focus:ring-[#C44133]/15'
                      : 'border-[#E5D9C8] focus:border-[#D99A2B] focus:ring-4 focus:ring-[#D99A2B]/15'
                  }`}
                  aria-invalid={Boolean(emailError && emailTouched)}
                  aria-describedby={emailError ? 'email-error-msg' : undefined}
                />
              </div>
              {emailError && emailTouched && (
                <p
                  id="email-error-msg"
                  className="text-xs text-[#C44133] flex items-center gap-1 mt-1 animate-slide-down"
                >
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>{emailError}</span>
                </p>
              )}
            </div>

            {/* Campo Senha */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password-input"
                  className="block text-sm font-medium text-[#2C1E12]"
                >
                  Senha
                </label>
                <button
                  type="button"
                  onClick={() => setIsForgotModalOpen(true)}
                  className="text-xs font-semibold text-[#D99A2B] hover:text-[#BF841F] transition-colors focus:outline-none focus:underline"
                >
                  Esqueceu sua senha?
                </button>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7A6A5A]">
                  <Lock className="w-[18px] h-[18px]" />
                </div>
                <input
                  id="password-input"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={handlePasswordChange}
                  onBlur={handlePasswordBlur}
                  placeholder="Digite sua senha"
                  className={`w-full h-[50px] pl-11 pr-11 rounded-lg bg-white border text-[15px] text-[#2C1E12] placeholder-[#7A6A5A]/60 transition-all duration-200 outline-none ${
                    passwordError && passwordTouched
                      ? 'border-[#C44133] focus:border-[#C44133] focus:ring-4 focus:ring-[#C44133]/15'
                      : 'border-[#E5D9C8] focus:border-[#D99A2B] focus:ring-4 focus:ring-[#D99A2B]/15'
                  }`}
                  aria-invalid={Boolean(passwordError && passwordTouched)}
                  aria-describedby={passwordError ? 'password-error-msg' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[#7A6A5A] hover:text-[#2C1E12] transition-colors focus:outline-none"
                  aria-label={showPassword ? 'Ocultar senha' : 'Exibir senha'}
                >
                  {showPassword ? (
                    <EyeOff className="w-[18px] h-[18px]" />
                  ) : (
                    <Eye className="w-[18px] h-[18px]" />
                  )}
                </button>
              </div>
              {passwordError && passwordTouched && (
                <p
                  id="password-error-msg"
                  className="text-xs text-[#C44133] flex items-center gap-1 mt-1 animate-slide-down"
                >
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>{passwordError}</span>
                </p>
              )}
            </div>

            {/* Botão Entrar */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full h-[50px] rounded-lg bg-[#D99A2B] hover:bg-[#BF841F] text-white font-sans font-semibold text-base transition-all duration-200 flex items-center justify-center gap-2 shadow-[0_2px_8px_rgba(217,154,43,0.3)] hover:shadow-[0_4px_14px_rgba(191,132,31,0.4)] hover:-translate-y-[1px] active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none border border-[#BF841F]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                    <span>Entrando...</span>
                  </>
                ) : (
                  <span>Entrar</span>
                )}
              </button>
            </div>

            {/* Área de Erro Condicional com animação slide-down */}
            {formError && (
              <div
                role="alert"
                className="flex items-start gap-3 p-3.5 rounded-lg bg-[#FDE8E6] border border-[#C44133]/25 text-[#C44133] text-sm animate-in fade-in slide-in-from-top-2 duration-200"
              >
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-[#C44133]" />
                <span className="leading-snug">{formError}</span>
              </div>
            )}
          </form>

          {/* Dica da conta de teste pré-configurada */}
          <div className="p-3.5 rounded-lg bg-white/70 border border-[#E5D9C8]/80 text-xs text-[#7A6A5A] space-y-1">
            <div className="flex items-center justify-between text-[#2C1E12] font-semibold">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D99A2B]" />
                Acesso de teste interno:
              </span>
              <button
                type="button"
                onClick={handleFillDemo}
                className="text-[11px] text-[#D99A2B] hover:underline"
              >
                Usar credenciais
              </button>
            </div>
            <p className="font-mono text-[11px] text-[#7A6A5A]">
              paulo.ferreira@panutrir.com.br • Skip@Pass
            </p>
          </div>
        </div>

        {/* Rodapé Discreto Centralizado */}
        <footer className="w-full max-w-[420px] pt-6 pb-2 text-center">
          <p className="font-sans text-xs text-[#7A6A5A] leading-relaxed">
            Ambiente interno restrito — acesso autorizado somente a colaboradores da Panutrir.
          </p>
        </footer>
      </section>

      {/* Modal Esqueceu sua senha */}
      <ForgotPasswordModal
        isOpen={isForgotModalOpen}
        onClose={() => setIsForgotModalOpen(false)}
        defaultEmail={email}
      />
    </div>
  )
}

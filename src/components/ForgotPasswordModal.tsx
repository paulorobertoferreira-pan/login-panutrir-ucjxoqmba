import React, { useState } from 'react'
import { Mail, ArrowLeft, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { toast } from '@/hooks/use-toast'

interface ForgotPasswordModalProps {
  isOpen: boolean
  onClose: () => void
  defaultEmail?: string
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  isOpen,
  onClose,
  defaultEmail = '',
}) => {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState(defaultEmail)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!email.trim() || !emailRegex.test(email.trim())) {
      setError('Informe um e-mail corporativo válido')
      return
    }

    setLoading(true)
    try {
      const { error: resetErr } = await resetPassword(email.trim())
      if (resetErr) {
        setError(
          resetErr.message.includes('rate')
            ? 'Muitas tentativas em pouco tempo. Aguarde alguns minutos.'
            : 'Não foi possível enviar o link de redefinição. Tente novamente.',
        )
      } else {
        setSuccess(true)
        toast({
          title: 'Link de redefinição enviado',
          description: `Enviamos as instruções para ${email.trim()}`,
          className: 'bg-[#2E7D32] text-white border-none shadow-lg',
        })
        setTimeout(() => {
          onClose()
          setSuccess(false)
        }, 2200)
      }
    } catch (err) {
      console.error(err)
      setError('Ocorreu um erro inesperado ao conectar com o servidor.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/55 backdrop-blur-[2px] animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="forgot-password-title"
    >
      <div
        className="relative w-full max-w-md bg-[#FAF6EF] rounded-2xl shadow-2xl border border-[#E5D9C8] p-6 sm:p-8 animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabeçalho */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-full bg-[#D99A2B]/15 text-[#D99A2B] flex items-center justify-center shrink-0">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h3
              id="forgot-password-title"
              className="font-serif text-xl sm:text-2xl font-bold text-[#2C1E12]"
            >
              Redefinir senha
            </h3>
            <p className="font-sans text-xs sm:text-sm text-[#7A6A5A]">
              Instruções de acesso ao sistema interno
            </p>
          </div>
        </div>

        {success ? (
          <div className="py-6 text-center space-y-3 animate-fade-in">
            <div className="w-12 h-12 rounded-full bg-[#2E7D32]/15 text-[#2E7D32] mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h4 className="font-serif font-bold text-lg text-[#2C1E12]">
              Verifique sua caixa de entrada
            </h4>
            <p className="font-sans text-sm text-[#7A6A5A] leading-relaxed">
              Enviamos um link seguro de recuperação para{' '}
              <strong className="text-[#2C1E12] font-semibold">{email}</strong>.
            </p>
            <div className="pt-2">
              <button
                type="button"
                onClick={onClose}
                className="w-full py-2.5 px-4 rounded-lg bg-[#D99A2B] hover:bg-[#BF841F] text-white font-medium text-sm transition-colors"
              >
                Concluir
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <p className="font-sans text-sm text-[#7A6A5A] leading-relaxed">
              Informe o e-mail cadastrado na Panutrir. Enviaremos um link seguro para você cadastrar
              uma nova senha.
            </p>

            <div className="space-y-1.5">
              <label htmlFor="reset-email" className="block text-sm font-medium text-[#2C1E12]">
                E-mail corporativo
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#7A6A5A]">
                  <Mail className="w-[18px] h-[18px]" />
                </div>
                <input
                  id="reset-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@panutrir.com.br"
                  className="w-full pl-11 pr-4 py-2.5 text-sm rounded-lg bg-white border border-[#E5D9C8] text-[#2C1E12] placeholder-[#7A6A5A]/60 focus:outline-none focus:border-[#D99A2B] focus:ring-4 focus:ring-[#D99A2B]/15 transition-all"
                  autoFocus
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/20 text-[#C44133] text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="py-2.5 px-4 rounded-lg border border-[#E5D9C8] hover:bg-black/5 text-[#7A6A5A] hover:text-[#2C1E12] text-sm font-medium transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg bg-[#D99A2B] hover:bg-[#BF841F] active:translate-y-[1px] text-white text-sm font-semibold shadow-sm transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Enviando...</span>
                  </>
                ) : (
                  <span>Enviar link</span>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

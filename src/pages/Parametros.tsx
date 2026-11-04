import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, Save, RefreshCw, CheckCircle2, AlertTriangle, Pencil } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

/* F2-T2.1 / SPEC-2-002 — Tela de parâmetros versionados (CA-2-06).

   Regras implementadas:
   · a tela lista os parâmetros da versão vigente (oficial) do ciclo;
   · editar um valor NÃO altera a versão existente: cria versão nova (rascunho)
     pela RPC criar_versao_parametros, com autor e motivo obrigatórios;
   · valor PENDENTE explícito: o campo aceita "PENDENTE" como valor (texto),
     gravado em valor_texto com pendente_de preenchido pelo motivo informado;
   · UPDATE direto na versão é recusado pelo trigger da T3.1 (imutabilidade) —
     a tela nem tenta: sempre cria versão.

   A RPC exige autor e motivo não vazios (check_violation) e clona todos os
   parâmetros, sortimento e substituição da versão de origem.
 */

interface ParamValor {
  parametro_codigo: string
  descricao: string
  valor_numero: number | null
  valor_texto: string | null
  unidade: string | null
  pendente_de: string | null
}

interface Versao {
  versao_id: string
  versao_codigo: string
  status: string
  autor: string
  motivo: string
  criado_em: string
}

export default function Parametros() {
  const navigate = useNavigate()
  const { user, session, loading } = useAuth()
  const [versao, setVersao] = useState<Versao | null>(null)
  const [valores, setValores] = useState<ParamValor[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  // edição
  const [editOpen, setEditOpen] = useState(false)
  const [editCodigo, setEditCodigo] = useState<string>('')
  const [editDescricao, setEditDescricao] = useState<string>('')
  const [editValor, setEditValor] = useState<string>('')
  const [editPendente, setEditPendente] = useState(false)
  const [editMotivo, setEditMotivo] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erroForm, setErroForm] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user && !session) navigate('/', { replace: true })
  }, [user, session, loading, navigate])

  const carregar = async () => {
    setCarregando(true)
    setErro(null)
    // versão oficial do ciclo Out/26 (a vigente); depois a lista de valores
    const { data: v, error: ev } = await supabase
      .from('parametros_versao')
      .select('versao_id, versao_codigo, status, autor, motivo, criado_em')
      .eq('status', 'oficial')
      .order('criado_em', { ascending: false })
      .limit(1)
    if (ev) { setErro(ev.message); setCarregando(false); return }
    const versaoOficial = (v ?? [])[0] as Versao | undefined
    setVersao(versaoOficial ?? null)
    if (!versaoOficial) { setValores([]); setCarregando(false); return }
    const { data: vals, error: evl } = await supabase
      .from('parametros_valor')
      .select('parametro_codigo, descricao, valor_numero, valor_texto, unidade, pendente_de')
      .eq('versao_id', versaoOficial.versao_id)
      .order('parametro_codigo')
    if (evl) setErro(evl.message)
    else setValores((vals ?? []) as ParamValor[])
    setCarregando(false)
  }

  useEffect(() => {
    if (user && session) carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, session])

  const abrirEdicao = (p: ParamValor) => {
    setEditCodigo(p.parametro_codigo)
    setEditDescricao(p.descricao)
    setEditPendente(p.pendente_de != null)
    setEditValor(
      p.pendente_de != null
        ? 'PENDENTE'
        : p.valor_numero != null
          ? String(p.valor_numero)
          : (p.valor_texto ?? ''),
    )
    setEditMotivo('')
    setErroForm(null)
    setEditOpen(true)
  }

  const salvar = async () => {
    setErroForm(null)
    if (!versao) return
    if (!editMotivo.trim()) { setErroForm('Informe o motivo da alteração'); return }
    if (!editValor.trim()) { setErroForm('Informe o valor (ou marque PENDENTE)'); return }
    setSalvando(true)
    const alteracao: Record<string, string | number> = editPendente
      ? { [editCodigo]: 'PENDENTE' }
      : isNaN(Number(editValor))
        ? { [editCodigo]: editValor.trim() }
        : { [editCodigo]: Number(editValor) }
    const { data, error } = await supabase.rpc('criar_versao_parametros', {
      p_versao_origem: versao.versao_id,
      p_novo_codigo: `${versao.versao_codigo}-r${Date.now().toString(36)}`,
      p_autor: user?.email ?? 'operador',
      p_motivo: editMotivo.trim(),
      p_alteracoes: alteracao,
    })
    setSalvando(false)
    if (error) { setErroForm(error.message); return }
    setEditOpen(false)
    setAviso(`Versão nova criada (${String(data).slice(0, 8)}…) com ${editCodigo} = ${editPendente ? 'PENDENTE' : editValor}. A versão anterior segue intacta.`)
    await carregar()
  }

  const fmtValor = (p: ParamValor) =>
    p.pendente_de != null
      ? 'PENDENTE'
      : p.valor_numero != null
        ? p.valor_numero.toLocaleString('pt-BR', { maximumFractionDigits: 6 })
        : (p.valor_texto ?? '—')

  return (
    <div className="min-h-screen bg-[#FAF6EF] text-[#2C1E12] flex flex-col font-sans">
      <header className="border-b border-[#E5D9C8] bg-white sticky top-0 z-20 shadow-xs">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#7A6A5A] hover:text-[#2C1E12]"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Voltar
            </button>
            <span className="text-[#E5D9C8]">|</span>
            <span className="font-sans text-xs tracking-wider uppercase font-semibold text-[#7A6A5A]">
              Parâmetros versionados
            </span>
          </div>
          <button
            onClick={carregar}
            className="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-[#E5D9C8] text-xs font-semibold text-[#7A6A5A] hover:text-[#2C1E12]"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Atualizar
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6 animate-fade-in">
        <div className="space-y-1">
          <h2 className="font-serif text-xl sm:text-2xl font-bold text-[#2C1E12]">
            Parâmetros da versão oficial
          </h2>
          {versao && (
            <p className="font-sans text-sm text-[#7A6A5A]">
              {versao.versao_codigo} · status <strong>{versao.status}</strong> · autor {versao.autor} · motivo: {versao.motivo}
            </p>
          )}
        </div>

        {aviso && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-[#E8F5E9] border border-[#2E7D32]/30 text-[#2E7D32] text-sm">
            <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{aviso}</span>
          </div>
        )}
        {erro && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/30 text-[#C44133] text-sm">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{erro}</span>
          </div>
        )}

        {carregando ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-[#D99A2B] animate-spin" />
          </div>
        ) : (
          <div className="rounded-xl border border-[#E5D9C8] bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E5D9C8] bg-[#FAF6EF]">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-[#7A6A5A]">Código</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-[#7A6A5A]">Descrição</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-[#7A6A5A]">Valor</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-[#7A6A5A]">Unidade</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {valores.map((p) => (
                  <tr key={p.parametro_codigo} className="border-b border-[#E5D9C8]/60 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs font-semibold">{p.parametro_codigo}</td>
                    <td className="px-4 py-2.5 text-xs text-[#7A6A5A]">{p.descricao}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-xs">
                      {p.pendente_de != null ? (
                        <Badge className="bg-[#D99A2B]/15 text-[#D99A2B] border border-[#D99A2B]/30 gap-1">
                          <AlertTriangle className="w-3 h-3" /> PENDENTE
                        </Badge>
                      ) : (
                        fmtValor(p)
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-[#7A6A5A]">{p.unidade ?? '—'}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={() => abrirEdicao(p)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-[#D99A2B] hover:text-[#C4881F]"
                      >
                        <Pencil className="w-3 h-3" /> Editar
                      </button>
                    </td>
                  </tr>
                ))}
                {valores.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-xs text-[#7A6A5A]">Nenhuma versão oficial encontrada.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs text-[#7A6A5A]">
          Toda alteração cria uma <strong>versão nova</strong> (rascunho) com autor e motivo — a versão oficial nunca é editada
          (trigger de imutabilidade da T3.1). Valor sem resposta do cliente fica gravado como <strong>PENDENTE</strong>.
        </p>
      </main>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md bg-white">
          <DialogHeader>
            <DialogTitle className="font-serif text-xl">
              Editar {editCodigo}
            </DialogTitle>
            <DialogDescription>
              {editDescricao} — a alteração cria uma versão nova; a atual segue intacta.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="valor" className="text-sm font-semibold">Novo valor</Label>
              <Input
                id="valor"
                value={editValor}
                onChange={(e) => setEditValor(e.target.value)}
                disabled={editPendente}
                className="h-11 bg-white border-[#E5D9C8] font-mono"
                placeholder="valor do parâmetro"
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={editPendente}
                onChange={(e) => { setEditPendente(e.target.checked); if (e.target.checked) setEditValor('PENDENTE') }}
                className="w-4 h-4 accent-[#D99A2B]"
              />
              Marcar como <strong>PENDENTE</strong> (sem resposta do cliente ainda)
            </label>
            <div className="space-y-2">
              <Label htmlFor="motivo" className="text-sm font-semibold">Motivo (obrigatório)</Label>
              <Input
                id="motivo"
                value={editMotivo}
                onChange={(e) => setEditMotivo(e.target.value)}
                className="h-11 bg-white border-[#E5D9C8]"
                placeholder="ex.: decisão do cliente Q-20 / ajuste aprovado"
              />
            </div>
            {erroForm && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/30 text-[#C44133] text-sm">
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{erroForm}</span>
              </div>
            )}
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setEditOpen(false)}>Cancelar</Button>
            <Button onClick={salvar} disabled={salvando} className="bg-[#D99A2B] hover:bg-[#C4881F] text-white">
              {salvando ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Criando versão…</>
              ) : (
                <><Save className="w-4 h-4" /> Criar versão nova</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
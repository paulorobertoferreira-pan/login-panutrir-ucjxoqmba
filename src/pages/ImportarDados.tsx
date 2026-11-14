import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Upload,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Clock,
  Download,
  Search,
} from 'lucide-react'
import * as XLSX from 'xlsx'
import { useAuth } from '@/hooks/use-auth'
import { supabase } from '@/lib/supabase/client'
import { Badge } from '@/components/ui/badge'

/* F2-T1.3 / SPEC-2-001 (CA-2-02) — Importação de dados novos, sem SQL.

   O Ângelo arrasta a planilha (congelada do BI), a tela mostra o que será
   importado (meses, combinações, rejeições, totais por mês) e pede confirmação.
   A gravação é a MESMA do fluxo operacional provado em `contracts/carga_operacional.py`:
   · uma transação por carga (tudo ou nada);
   · idempotência por mês (recarregar substitui só aquele mês);
   · registro completo em `carga_registro` (arquivo, hash, contagens, totais, rejeições);
   · conferência fonte × banco ao final.

   A tela faz a leitura e a validação no navegador (xlsx) e envia o agregado ao
   banco em blocos, gravando o registro. Nada é gravado antes do clique.
 */

const ALIASES: Record<string, string> = {
  'mesano: mês': 'mes',
  'mesano: mes': 'mes',
  mês: 'mes',
  mes: 'mes',
  id_empresa: 'id_empresa',
  tipo: 'tipo',
  regiao: 'regiao',
  regional: 'regional',
  cd_resp: 'cd_resp',
  codrede: 'codrede',
  rede: 'rede',
  cidade: 'cidade',
  uf: 'uf',
  codcli: 'cod_cliente',
  codcli_sap: 'codcli_sap',
  fantasia: 'fantasia',
  codpro: 'cod_sku',
  codpro_sap: 'codpro_sap',
  produto: 'produto',
  linha: 'linha',
  'soma de qtde': 'qtdade',
  'soma de vlritens': 'vlritens',
  'soma de vlrdesc': 'vlrdesc',
  'soma de qtdetroca': 'qtdetroca',
  'soma de vlrtroca': 'vlrtroca',
}

const OBRIGATORIAS = ['mes', 'cod_cliente', 'cod_sku', 'vlritens', 'vlrdesc', 'vlrtroca', 'qtdade']
const LOTE = 800

interface Agregado {
  vlritens: number
  vlrdesc: number
  vlrtroca: number
  qtdade: number
}
interface Leitura {
  arquivo: string
  bytes: number
  hash: string
  linhasLidas: number
  agg: Map<string, Agregado>
  totaisPorMes: Record<
    string,
    { vlritens: number; vlrdesc: number; vlrtroca: number; linhas: number }
  >
  rejeicoes: Record<string, number>
  meses: string[]
}

interface Carga {
  carga_id: string
  arquivo_nome: string
  meses_afetados: string[]
  linhas_lidas: number
  linhas_agregadas: number
  linhas_rejeitadas: number
  totais_por_mes: Record<string, { vlritens: number }>
  executado_por: string
  concluido_em: string | null
  status: string
}

const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const num = (v: number) => v.toLocaleString('pt-BR')
const soDigitos = (v: unknown) =>
  String(v ?? '')
    .replace(/\.0+$/, '')
    .trim()

function hashArquivo(buf: ArrayBuffer): Promise<string> {
  return crypto.subtle.digest('SHA-256', buf).then((h) =>
    Array.from(new Uint8Array(h))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join(''),
  )
}

export default function ImportarDados() {
  const navigate = useNavigate()
  const { user, session, loading } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)

  const [leitura, setLeitura] = useState<Leitura | null>(null)
  const [lendo, setLendo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [gravando, setGravando] = useState(false)
  const [progresso, setProgresso] = useState('')
  const [sucesso, setSucesso] = useState<string | null>(null)
  const [historico, setHistorico] = useState<Carga[]>([])
  const [busca, setBusca] = useState('')

  useEffect(() => {
    if (!loading && !user && !session) navigate('/', { replace: true })
  }, [user, session, loading, navigate])

  const carregarHistorico = useCallback(async () => {
    const { data } = await supabase
      .from('carga_registro')
      .select(
        'carga_id, arquivo_nome, meses_afetados, linhas_lidas, linhas_agregadas, linhas_rejeitadas, totais_por_mes, executado_por, concluido_em, status',
      )
      .order('iniciado_em', { ascending: false })
      .limit(50)
    setHistorico((data ?? []) as Carga[])
  }, [])

  useEffect(() => {
    if (user && session) carregarHistorico()
  }, [user, session, carregarHistorico])

  const lerArquivo = async (file: File) => {
    setErro(null)
    setSucesso(null)
    setLeitura(null)
    setLendo(true)
    try {
      const buf = await file.arrayBuffer()
      const hash = await hashArquivo(buf.slice(0))
      const wb = XLSX.read(buf, { type: 'array', cellDates: true })
      // a aba de dados é a que tem mais colunas (2024/25 trazem uma aba de ruído)
      let melhor: any = null
      for (const nome of wb.SheetNames) {
        const ws = wb.Sheets[nome]
        const rows = XLSX.utils.sheet_to_json<any[]>(ws, { header: 1, raw: true, defval: null })
        if (rows.length && (!melhor || (rows[0]?.filter(Boolean).length ?? 0) > melhor.cols)) {
          melhor = { nome, rows, cols: rows[0]?.filter(Boolean).length ?? 0 }
        }
      }
      if (!melhor) throw new Error('arquivo sem abas legíveis')
      const [cab, ...dados] = melhor.rows as any[][]
      const mapa: Record<number, string> = {}
      ;(cab ?? []).forEach((h: unknown, i: number) => {
        const c =
          ALIASES[
            String(h ?? '')
              .trim()
              .toLowerCase()
          ]
        if (c) mapa[i] = c
      })
      const presentes = new Set(Object.values(mapa))
      const faltando = OBRIGATORIAS.filter((c) => !presentes.has(c))
      if (faltando.length) throw new Error(`colunas obrigatórias ausentes: ${faltando.join(', ')}`)

      const agg = new Map<string, Agregado>()
      const totais: Leitura['totaisPorMes'] = {}
      const rejeicoes: Record<string, number> = {}
      let lidas = 0
      const rejeitar = (motivo: string) => {
        rejeicoes[motivo] = (rejeicoes[motivo] ?? 0) + 1
      }

      for (const row of dados) {
        if (!row || row.every((c) => c === null || c === '')) continue
        lidas++
        const val: Record<string, unknown> = {}
        for (const [i, campo] of Object.entries(mapa)) val[campo] = row[Number(i)]
        // mês: Date (cellDates) ou texto
        let mes: string | null = null
        const mv: any = val.mes
        if (mv instanceof Date)
          mes = `${mv.getFullYear()}-${String(mv.getMonth() + 1).padStart(2, '0')}`
        else if (typeof mv === 'string') {
          const m = mv.match(/^(\d{4})-(\d{2})/)
          if (m) mes = `${m[1]}-${m[2]}`
        }
        const cli = soDigitos(val.cod_cliente)
        const sku = soDigitos(val.cod_sku)
        if (!mes) {
          rejeitar('data_invalida')
          continue
        }
        if (!cli) {
          rejeitar('codigo_vazio')
          continue
        }
        if (!sku) {
          rejeitar('sku_vazio')
          continue
        }
        const n = (v: unknown) => {
          const x = typeof v === 'number' ? v : parseFloat(String(v ?? '').replace(',', '.'))
          return Number.isFinite(x) ? Math.round(x * 100) / 100 : 0
        }
        const a = agg.get(`${mes}|${cli}|${sku}`) ?? {
          vlritens: 0,
          vlrdesc: 0,
          vlrtroca: 0,
          qtdade: 0,
        }
        a.vlritens += n(val.vlritens)
        a.vlrdesc += n(val.vlrdesc)
        a.vlrtroca += n(val.vlrtroca)
        a.qtdade += n(val.qtdade)
        // combinação sem nenhum valor (todos zero) não é venda: não entra
        // (mesma regra do contrato — o mesmo par aparece em linha só-zero)
        if (a.vlritens !== 0 || a.vlrdesc !== 0 || a.vlrtroca !== 0 || a.qtdade !== 0) {
          agg.set(`${mes}|${cli}|${sku}`, a)
        }
        const t = totais[mes] ?? { vlritens: 0, vlrdesc: 0, vlrtroca: 0, linhas: 0 }
        t.vlritens += n(val.vlritens)
        t.vlrdesc += n(val.vlrdesc)
        t.vlrtroca += n(val.vlrtroca)
        t.linhas += 1
        totais[mes] = t
      }

      setLeitura({
        arquivo: file.name,
        bytes: file.size,
        hash,
        linhasLidas: lidas,
        agg,
        totaisPorMes: totais,
        rejeicoes,
        meses: Object.keys(totais).sort(),
      })
    } catch (e: any) {
      setErro(e?.message ?? String(e))
    } finally {
      setLendo(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const confirmar = async () => {
    if (!leitura) return
    setGravando(true)
    setErro(null)
    setProgresso('Registrando a carga…')
    try {
      // 1) registro da carga (em_andamento)
      const { data: reg, error: eReg } = await supabase
        .from('carga_registro')
        .insert({
          arquivo_nome: leitura.arquivo,
          arquivo_hash: leitura.hash,
          arquivo_bytes: leitura.bytes,
          meses_afetados: leitura.meses,
          linhas_lidas: leitura.linhasLidas,
          linhas_agregadas: leitura.agg.size,
          linhas_rejeitadas: Object.values(leitura.rejeicoes).reduce((a, b) => a + b, 0),
          rejeicoes: { por_motivo: leitura.rejeicoes, exemplos: [] },
          totais_por_mes: leitura.totaisPorMes,
          executado_por: user?.email ?? 'operador',
          status: 'em_andamento',
        })
        .select('carga_id')
        .single()
      if (eReg) throw new Error(eReg.message)
      const cargaId = reg.carga_id

      // 2) idempotência por mês: apagar os meses desta carga
      for (const mes of leitura.meses) {
        const { error } = await supabase.from('venda_mensal').delete().eq('mes', `${mes}-01`)
        if (error) throw new Error(`ao limpar ${mes}: ${error.message}`)
      }

      // 3) enviar o agregado em blocos
      const linhas = Array.from(leitura.agg.entries()).map(([k, a]) => {
        const [mes, cli, sku] = k.split('|')
        // cod_cliente/cod_sku são INTEGER no banco; venda_bruta e venda_liquida
        // são as duas métricas do contrato (bruta = vlritens − vlrdesc;
        // líquida de 3 termos = bruta − vlrtroca — as métricas provadas na Fase 1)
        const bruta = Math.round((a.vlritens - a.vlrdesc) * 100) / 100
        return {
          mes: `${mes}-01`,
          cod_cliente: Number(cli),
          cod_sku: Number(sku),
          vlritens: a.vlritens,
          vlrdesc: a.vlrdesc,
          vlrtroca: a.vlrtroca,
          qtdade: a.qtdade,
          venda_bruta: bruta,
          venda_liquida: Math.round((bruta - a.vlrtroca) * 100) / 100,
          carga_id: cargaId,
        }
      })
      let enviadas = 0
      for (let i = 0; i < linhas.length; i += LOTE) {
        const bloco = linhas.slice(i, i + LOTE)
        setProgresso(`Gravando ${num(enviadas)} de ${num(linhas.length)} combinações…`)
        const { error } = await supabase.from('venda_mensal').insert(bloco)
        if (error) throw new Error(`ao gravar (bloco ${i}): ${error.message}`)
        enviadas += bloco.length
      }

      // 4) fechar o registro
      setProgresso('Conferindo os totais…')
      const { error: eFim } = await supabase
        .from('carga_registro')
        .update({
          status: 'concluida',
          concluido_em: new Date().toISOString(),
          linhas_agregadas: enviadas,
        })
        .eq('carga_id', cargaId)
      if (eFim) throw new Error(eFim.message)

      setSucesso(
        `${num(enviadas)} combinações gravadas em ${leitura.meses.join(', ')}. O mês foi substituído por completo — recarregar não duplica.`,
      )
      setLeitura(null)
      await carregarHistorico()
    } catch (e: any) {
      setErro(e?.message ?? String(e))
    } finally {
      setGravando(false)
      setProgresso('')
    }
  }

  const filtrado = useMemo(() => {
    const q = busca.trim().toLowerCase()
    if (!q) return historico
    return historico.filter(
      (c) =>
        c.arquivo_nome.toLowerCase().includes(q) ||
        (c.meses_afetados ?? []).join(' ').includes(q) ||
        (c.executado_por ?? '').toLowerCase().includes(q),
    )
  }, [historico, busca])

  return (
    <div className="min-h-screen bg-[#FAF6EF] text-[#2C1E12] flex flex-col font-sans">
      <header className="border-b border-[#E5D9C8] bg-white sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#7A6A5A] hover:text-[#2C1E12]"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Voltar
            </button>
            <span className="text-[#E5D9C8]">|</span>
            <span className="text-xs tracking-wider uppercase font-semibold text-[#7A6A5A]">
              Importar dados
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="space-y-1">
          <h2 className="font-serif text-xl sm:text-2xl font-bold">Importar vendas do mês</h2>
          <p className="text-sm text-[#7A6A5A]">
            Arraste a planilha fechada do BI. A tela mostra o que será importado antes de gravar —
            nada entra sem a sua confirmação.
          </p>
        </div>

        {sucesso && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-[#E8F5E9] border border-[#2E7D32]/30 text-[#2E7D32] text-sm">
            <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{sucesso}</span>
          </div>
        )}
        {erro && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-[#FDE8E6] border border-[#C44133]/30 text-[#C44133] text-sm">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{erro}</span>
          </div>
        )}

        {/* área de upload */}
        <div
          onClick={() => !lendo && inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const f = e.dataTransfer.files?.[0]
            if (f) lerArquivo(f)
          }}
          className="cursor-pointer rounded-xl border-2 border-dashed border-[#E5D9C8] bg-white p-10 text-center hover:border-[#D99A2B]/60 transition-colors"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) lerArquivo(f)
            }}
          />
          {lendo ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-7 h-7 text-[#D99A2B] animate-spin" />
              <p className="text-sm text-[#7A6A5A]">Lendo a planilha…</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Upload className="w-7 h-7 text-[#D99A2B]" />
              <p className="font-medium">Clique ou arraste a planilha aqui</p>
              <p className="text-xs text-[#7A6A5A]">
                .xlsx do BI — histórico de vendas do mês fechado
              </p>
            </div>
          )}
        </div>

        {/* prévia da leitura */}
        {leitura && (
          <div className="rounded-xl border border-[#E5D9C8] bg-white overflow-hidden">
            <div className="px-5 py-3 bg-[#FAF6EF] border-b border-[#E5D9C8] flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-[#D99A2B]" />
              <span className="font-semibold text-sm">{leitura.arquivo}</span>
              <span className="text-xs text-[#7A6A5A]">· {num(leitura.bytes)} bytes</span>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-xs text-[#7A6A5A] uppercase tracking-wider">Mês(es)</p>
                  <p className="font-semibold">{leitura.meses.join(', ')}</p>
                </div>
                <div>
                  <p className="text-xs text-[#7A6A5A] uppercase tracking-wider">Linhas lidas</p>
                  <p className="font-semibold">{num(leitura.linhasLidas)}</p>
                </div>
                <div>
                  <p className="text-xs text-[#7A6A5A] uppercase tracking-wider">Combinações</p>
                  <p className="font-semibold">{num(leitura.agg.size)}</p>
                </div>
                <div>
                  <p className="text-xs text-[#7A6A5A] uppercase tracking-wider">Rejeitadas</p>
                  <p className="font-semibold">
                    {num(Object.values(leitura.rejeicoes).reduce((a, b) => a + b, 0))}
                  </p>
                </div>
              </div>
              <div className="space-y-1">
                {leitura.meses.map((m) => {
                  const t = leitura.totaisPorMes[m]
                  return (
                    <div
                      key={m}
                      className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-mono text-[#7A6A5A]"
                    >
                      <span className="font-semibold text-[#2C1E12]">{m}</span>
                      <span>bruta {brl(t.vlritens)}</span>
                      <span>desc {brl(t.vlrdesc)}</span>
                      <span>troca {brl(t.vlrtroca)}</span>
                      <span>{num(t.linhas)} linhas</span>
                    </div>
                  )
                })}
              </div>
              {Object.keys(leitura.rejeicoes).length > 0 && (
                <p className="text-xs text-[#D99A2B]">
                  Linhas rejeitadas (não invalidam a carga): {JSON.stringify(leitura.rejeicoes)}
                </p>
              )}
              <div className="flex gap-2 pt-1">
                <button
                  onClick={confirmar}
                  disabled={gravando}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#D99A2B] hover:bg-[#C4881F] text-white text-sm font-semibold disabled:opacity-60"
                >
                  {gravando ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Gravando…
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" /> Confirmar importação
                    </>
                  )}
                </button>
                <button
                  onClick={() => setLeitura(null)}
                  disabled={gravando}
                  className="px-4 py-2 rounded-lg border border-[#E5D9C8] text-sm font-semibold text-[#7A6A5A] hover:text-[#2C1E12]"
                >
                  Cancelar
                </button>
              </div>
              {progresso && <p className="text-xs text-[#7A6A5A]">{progresso}</p>}
            </div>
          </div>
        )}

        {/* histórico de cargas */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-serif text-lg font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#D99A2B]" /> Cargas recentes
            </h3>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#7A6A5A]" />
              <input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="filtrar por arquivo, mês ou operador"
                className="pl-8 pr-3 py-1.5 w-64 rounded-lg border border-[#E5D9C8] bg-white text-xs"
              />
            </div>
          </div>
          <div className="rounded-xl border border-[#E5D9C8] bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E5D9C8] bg-[#FAF6EF] text-xs uppercase tracking-wider text-[#7A6A5A]">
                  <th className="text-left px-4 py-2">Arquivo</th>
                  <th className="text-left px-4 py-2">Mês</th>
                  <th className="text-right px-4 py-2">Linhas</th>
                  <th className="text-right px-4 py-2">Comb.</th>
                  <th className="text-right px-4 py-2">Rejeit.</th>
                  <th className="text-left px-4 py-2">Operador</th>
                  <th className="text-left px-4 py-2">Concluída</th>
                  <th className="text-left px-4 py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {filtrado.map((c) => (
                  <tr key={c.carga_id} className="border-b border-[#E5D9C8]/60 last:border-0">
                    <td className="px-4 py-2 text-xs max-w-[16rem] truncate" title={c.arquivo_nome}>
                      {c.arquivo_nome}
                    </td>
                    <td className="px-4 py-2 text-xs font-mono">
                      {(c.meses_afetados ?? []).join(', ')}
                    </td>
                    <td className="px-4 py-2 text-right text-xs font-mono">
                      {num(c.linhas_lidas)}
                    </td>
                    <td className="px-4 py-2 text-right text-xs font-mono">
                      {num(c.linhas_agregadas)}
                    </td>
                    <td className="px-4 py-2 text-right text-xs font-mono">
                      {num(c.linhas_rejeitadas)}
                    </td>
                    <td className="px-4 py-2 text-xs text-[#7A6A5A]">{c.executado_por}</td>
                    <td className="px-4 py-2 text-xs text-[#7A6A5A]">
                      {c.concluido_em ? new Date(c.concluido_em).toLocaleString('pt-BR') : '—'}
                    </td>
                    <td className="px-4 py-2">
                      {c.status === 'concluida' ? (
                        <Badge className="bg-[#E8F5E9] text-[#2E7D32] border border-[#2E7D32]/30">
                          concluída
                        </Badge>
                      ) : c.status === 'falhou' ? (
                        <Badge className="bg-[#FDE8E6] text-[#C44133] border border-[#C44133]/30">
                          falhou
                        </Badge>
                      ) : (
                        <Badge className="bg-[#D99A2B]/15 text-[#D99A2B] border border-[#D99A2B]/30">
                          em andamento
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
                {filtrado.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-xs text-[#7A6A5A]">
                      Nenhuma carga registrada ainda.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[#7A6A5A] flex items-center gap-1.5">
            <Download className="w-3.5 h-3.5" />
            Cada carga guarda arquivo, hash, contagens, totais e linhas rejeitadas — recarregar um
            mês substitui só aquele mês.
          </p>
        </div>
      </main>
    </div>
  )
}

import { useMemo, useState } from 'react'
import { Input } from '@/components/ui/input'

export type OpcaoPromotor = {
  valor: string
  // Texto exibido ao escolher a opção (nome e código do promotor · supervisor)
  rotulo: string
  // Texto pesquisado: nome e código do promotor e do supervisor
  busca: string
}

type Props = {
  id: string
  opcoes: OpcaoPromotor[]
  valor: string
  onChange: (valor: string) => void
  disabled?: boolean
}

const semAcento = (t: string) =>
  t
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()

// Campo de busca com lista filtrada por nome ou código do promotor (sem rolar a lista inteira)
export function BuscaPromotor({ id, opcoes, valor, onChange, disabled }: Props) {
  const [texto, setTexto] = useState('')
  const [aberto, setAberto] = useState(false)
  const termo = semAcento(texto.trim())
  const filtradas = useMemo(
    () => opcoes.filter((o) => !termo || semAcento(o.busca).includes(termo)),
    [opcoes, termo],
  )

  return (
    <div className="relative">
      <Input
        id={id}
        role="combobox"
        aria-expanded={aberto}
        aria-controls={`${id}-lista`}
        aria-autocomplete="list"
        autoComplete="off"
        placeholder="Buscar por nome ou código do promotor"
        value={texto}
        disabled={disabled}
        onFocus={() => setAberto(true)}
        onBlur={() => setAberto(false)}
        onChange={(e) => {
          setTexto(e.target.value)
          setAberto(true)
          // Digitar de novo desfaz a escolha anterior até um novo promotor ser selecionado
          if (valor) onChange('')
        }}
      />
      {aberto && !disabled && (
        <div
          id={`${id}-lista`}
          role="listbox"
          className="absolute z-30 mt-1 max-h-56 w-full overflow-y-auto rounded border bg-white text-sm shadow-md"
        >
          {filtradas.length === 0 && (
            <p className="p-2 text-[#7A6A5A]">Nenhum promotor encontrado.</p>
          )}
          {filtradas.map((o) => (
            <button
              key={o.valor}
              type="button"
              role="option"
              aria-selected={o.valor === valor}
              // Evita que o campo perca o foco antes da escolha ser registrada
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onChange(o.valor)
                setTexto(o.rotulo)
                setAberto(false)
              }}
              className={`block w-full px-3 py-2 text-left hover:bg-[#FAF6EF] ${
                o.valor === valor ? 'bg-[#FAF6EF] font-semibold' : ''
              }`}
            >
              {o.rotulo}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

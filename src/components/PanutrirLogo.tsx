import React from 'react'

interface LogoProps {
  className?: string
  variant?: 'light' | 'dark' | 'amber'
  size?: 'sm' | 'md' | 'lg'
  showSlogan?: boolean
}

export const PanutrirLogo: React.FC<LogoProps> = ({
  className = '',
  variant = 'light',
  size = 'md',
  showSlogan = true,
}) => {
  const isLight = variant === 'light'
  const isDark = variant === 'dark'

  const textClass = isLight ? 'text-[#FAF6EF]' : isDark ? 'text-[#2C1E12]' : 'text-[#D99A2B]'

  const accentClass = isLight ? 'text-[#D99A2B]' : 'text-[#D99A2B]'
  const sloganClass = isLight ? 'text-[#FAF6EF]/80' : 'text-[#7A6A5A]'

  const sizeDimensions = {
    sm: { icon: 28, text: 'text-xl', sub: 'text-[10px]' },
    md: { icon: 38, text: 'text-2xl', sub: 'text-xs' },
    lg: { icon: 52, text: 'text-3xl sm:text-4xl', sub: 'text-xs sm:text-sm' },
  }[size]

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Símbolo do Trigo Dourado Artesanal */}
      <div className="relative flex items-center justify-center shrink-0">
        <svg
          width={sizeDimensions.icon}
          height={sizeDimensions.icon}
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-sm"
          aria-hidden="true"
        >
          {/* Círculo suave de fundo */}
          <circle
            cx="24"
            cy="24"
            r="23"
            fill={isLight ? 'rgba(217, 154, 43, 0.18)' : '#FAF6EF'}
            stroke="#D99A2B"
            strokeWidth="1.5"
            strokeDasharray="2 2"
          />

          {/* Ramo de Trigo / Espiga Central estilizada */}
          {/* Haste */}
          <path d="M24 38V12" stroke="#D99A2B" strokeWidth="2" strokeLinecap="round" />
          {/* Grãos esquerdos */}
          <path
            d="M24 32C20 31 18 28 18 25C21 25 24 28 24 29"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          <path
            d="M24 24C19 23 17 19 17 16C21 16 24 20 24 21"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          <path
            d="M24 16C21 15 19 12 19 9C22 9 24 13 24 14"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          {/* Grãos direitos */}
          <path
            d="M24 32C28 31 30 28 30 25C27 25 24 28 24 29"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          <path
            d="M24 24C29 23 31 19 31 16C27 16 24 20 24 21"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          <path
            d="M24 16C27 15 29 12 29 9C26 9 24 13 24 14"
            fill="#D99A2B"
            stroke="#BF841F"
            strokeWidth="0.8"
          />
          {/* Ponta superior */}
          <path d="M24 10C23 7 24 5 24 5C24 5 25 7 24 10Z" fill="#BF841F" />
        </svg>
      </div>

      {/* Tipografia da Marca */}
      <div className="flex flex-col leading-none">
        <div className="flex items-baseline tracking-wider">
          <span
            className={`font-serif font-bold ${sizeDimensions.text} ${textClass} tracking-[0.14em] uppercase`}
          >
            PANU
          </span>
          <span
            className={`font-serif font-bold ${sizeDimensions.text} ${accentClass} tracking-[0.14em] uppercase`}
          >
            TRIR
          </span>
        </div>
        {showSlogan && (
          <span
            className={`font-sans tracking-wide italic mt-1 font-medium ${sizeDimensions.sub} ${sloganClass}`}
          >
            O verdadeiro gostinho do pão
          </span>
        )}
      </div>
    </div>
  )
}

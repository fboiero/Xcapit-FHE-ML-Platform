import { forwardRef } from 'react'

/**
 * Button Component
 *
 * Variantes:
 * - primary: Acción principal (brand-600)
 * - secondary: Acción secundaria (borde)
 * - danger: Acciones destructivas (rojo)
 * - ghost: Sin fondo, solo hover
 *
 * Tamaños:
 * - sm: Pequeño (py-1.5 px-3)
 * - md: Mediano (py-2.5 px-5) - default
 * - lg: Grande (py-3 px-6)
 *
 * Props adicionales:
 * - loading: Muestra spinner
 * - disabled: Deshabilitado
 * - fullWidth: Ancho completo
 * - leftIcon / rightIcon: Iconos
 */

const variants = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-500 disabled:bg-brand-300',
  secondary:
    'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus:ring-slate-500 disabled:bg-slate-100 disabled:text-slate-400',
  danger:
    'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-300',
  ghost:
    'bg-transparent text-slate-600 hover:bg-slate-100 focus:ring-slate-500 disabled:text-slate-400',
}

const sizes = {
  sm: 'py-1.5 px-3 text-sm',
  md: 'py-2.5 px-5 text-sm',
  lg: 'py-3 px-6 text-base',
}

const Button = forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className = '',
  type = 'button',
  ...props
}, ref) => {
  const isDisabled = disabled || loading

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium rounded-xl
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:cursor-not-allowed
        ${variants[variant]}
        ${sizes[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
      {...props}
    >
      {loading ? (
        <svg
          className="animate-spin h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : leftIcon ? (
        <span className="w-4 h-4" aria-hidden="true">{leftIcon}</span>
      ) : null}

      {children}

      {rightIcon && !loading && (
        <span className="w-4 h-4" aria-hidden="true">{rightIcon}</span>
      )}
    </button>
  )
})

Button.displayName = 'Button'

export default Button

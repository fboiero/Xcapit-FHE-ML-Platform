/**
 * Card Component
 *
 * Tamaños de padding:
 * - sm: p-4
 * - md: p-6 (default)
 * - lg: p-8
 *
 * Variantes:
 * - default: Borde sutil
 * - elevated: Con sombra
 * - interactive: Hover effect
 * - bordered: Borde más visible
 */

const paddings = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

const variants = {
  default: 'bg-white border border-slate-200',
  elevated: 'bg-white shadow-lg',
  interactive: 'bg-white border border-slate-200 hover:shadow-lg hover:border-brand-200 transition-all cursor-pointer',
  bordered: 'bg-white border-2 border-slate-300',
}

export default function Card({
  children,
  size = 'md',
  variant = 'default',
  className = '',
  onClick,
  ...props
}) {
  const Component = onClick ? 'button' : 'div'

  return (
    <Component
      onClick={onClick}
      className={`
        rounded-xl
        ${paddings[size]}
        ${variants[variant]}
        ${onClick ? 'w-full text-left focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2' : ''}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
      {...props}
    >
      {children}
    </Component>
  )
}

// Sub-componentes para estructura consistente
Card.Header = function CardHeader({ children, className = '' }) {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  )
}

Card.Title = function CardTitle({ children, className = '' }) {
  return (
    <h3 className={`text-lg font-semibold text-slate-900 ${className}`}>
      {children}
    </h3>
  )
}

Card.Description = function CardDescription({ children, className = '' }) {
  return (
    <p className={`text-sm text-slate-600 mt-1 ${className}`}>
      {children}
    </p>
  )
}

Card.Body = function CardBody({ children, className = '' }) {
  return (
    <div className={className}>
      {children}
    </div>
  )
}

Card.Footer = function CardFooter({ children, className = '' }) {
  return (
    <div className={`mt-4 pt-4 border-t border-slate-100 ${className}`}>
      {children}
    </div>
  )
}

/**
 * Badge Component
 *
 * Para estados, etiquetas, contadores
 *
 * Variantes:
 * - default: Gris neutro
 * - primary: Brand color
 * - success: Verde
 * - warning: Amarillo
 * - danger: Rojo
 * - info: Azul
 *
 * Tamaños:
 * - sm: Pequeño
 * - md: Mediano (default)
 */

const variants = {
  default: 'bg-slate-100 text-slate-700',
  primary: 'bg-brand-100 text-brand-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
}

const sizes = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
}) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        font-medium rounded-full
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            variant === 'success' ? 'bg-green-500' :
            variant === 'warning' ? 'bg-amber-500' :
            variant === 'danger' ? 'bg-red-500' :
            variant === 'info' ? 'bg-blue-500' :
            variant === 'primary' ? 'bg-brand-500' :
            'bg-slate-500'
          }`}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  )
}

// Status Badge preconfigurado
export function StatusBadge({ status }) {
  const statusConfig = {
    active: { label: 'Activo', variant: 'success', dot: true },
    pending: { label: 'Pendiente', variant: 'warning', dot: true },
    completed: { label: 'Completado', variant: 'success', dot: true },
    failed: { label: 'Fallido', variant: 'danger', dot: true },
    draft: { label: 'Borrador', variant: 'default', dot: true },
    approved: { label: 'Aprobado', variant: 'success', dot: true },
    rejected: { label: 'Rechazado', variant: 'danger', dot: true },
    in_progress: { label: 'En Progreso', variant: 'info', dot: true },
  }

  const config = statusConfig[status] || { label: status, variant: 'default' }

  return (
    <Badge variant={config.variant} dot={config.dot}>
      {config.label}
    </Badge>
  )
}

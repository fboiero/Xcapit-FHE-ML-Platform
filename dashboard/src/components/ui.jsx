export function PageLoader() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f8fafc',
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid #e2e8f0',
          borderTopColor: '#4f46e5',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Cargando...</span>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  )
}

export function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: '16px',
      border: '1px solid #e2e8f0',
      padding: '24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      ...style,
    }}>
      {children}
    </div>
  )
}

export function Badge({ children, variant = 'primary', style = {} }) {
  const colors = {
    primary: { bg: '#eef2ff', color: '#4f46e5' },
    success: { bg: '#ecfdf5', color: '#059669' },
    warning: { bg: '#fffbeb', color: '#d97706' },
    danger: { bg: '#fef2f2', color: '#dc2626' },
  }
  const c = colors[variant] || colors.primary
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '4px 12px',
      borderRadius: '100px',
      background: c.bg,
      color: c.color,
      fontSize: '0.8rem',
      fontWeight: '600',
      ...style,
    }}>
      {children}
    </span>
  )
}

export function Button({ children, onClick, variant = 'primary', disabled = false, style = {} }) {
  const baseStyle = {
    padding: '12px 24px',
    borderRadius: '10px',
    border: 'none',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    transition: 'all 0.2s',
  }
  const variants = {
    primary: {
      background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
      color: '#fff',
    },
    outline: {
      background: 'transparent',
      color: '#4f46e5',
      border: '1px solid #e2e8f0',
    },
    danger: {
      background: '#fef2f2',
      color: '#dc2626',
    },
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{ ...baseStyle, ...variants[variant], ...style }}
    >
      {children}
    </button>
  )
}

/**
 * Reusable API error display component.
 */
export default function ApiError({ error, onRetry }) {
  if (!error) return null

  return (
    <div style={{
      padding: '16px 20px',
      background: '#fef2f2',
      border: '1px solid #fecaca',
      borderRadius: '12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '1.2rem' }}>&#9888;</span>
        <span style={{ color: '#991b1b', fontSize: '0.9rem' }}>{error}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '6px 16px',
            background: '#dc2626',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '0.85rem',
            fontWeight: '600',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Reintentar
        </button>
      )}
    </div>
  )
}

import { useNavigate } from 'react-router-dom'

export default function NotFound() {
  const navigate = useNavigate()

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f8fafc',
      padding: '24px',
    }}>
      <div style={{ textAlign: 'center', maxWidth: '400px' }}>
        <div style={{ fontSize: '5rem', fontWeight: '800', color: '#e2e8f0', lineHeight: 1 }}>404</div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1e293b', margin: '16px 0 8px' }}>
          Pagina no encontrada
        </h1>
        <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '0.95rem' }}>
          La pagina que buscas no existe o fue movida.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button
            onClick={() => navigate('/dashboard')}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              fontSize: '0.95rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Ir al Dashboard
          </button>
          <button
            onClick={() => navigate(-1)}
            style={{
              padding: '12px 24px',
              background: '#fff',
              color: '#4f46e5',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              fontSize: '0.95rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Volver
          </button>
        </div>
      </div>
    </div>
  )
}

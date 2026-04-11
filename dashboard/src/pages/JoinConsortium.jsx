import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { acceptInvitation, listConsortiums, isAuthenticated } from '../api/client'

const COLORS = {
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f9fafb',
  card: '#ffffff',
  text: '#111827',
  muted: '#6b7280',
  border: '#e5e7eb',
  borderFocus: '#6366f1',
}

const MODEL_LABELS = {
  linear_regression: 'Regresion lineal',
  logistic_regression: 'Regresion logistica',
  random_forest: 'Random Forest',
  neural_network: 'Red neuronal',
}

export default function JoinConsortium() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const inviteCode = searchParams.get('code') || ''

  const [code, setCode] = useState(inviteCode)
  const [loading, setLoading] = useState(false)
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [availableConsortiums, setAvailableConsortiums] = useState([])

  const authenticated = isAuthenticated()

  useEffect(() => {
    if (!authenticated) return
    const fetchConsortiums = async () => {
      setLoading(true)
      try {
        const data = await listConsortiums()
        const list = Array.isArray(data) ? data : data.results || []
        setAvailableConsortiums(list.filter(c => c.status === 'active' || c.status === 'pending'))
      } catch (err) {
        // non-critical
      } finally {
        setLoading(false)
      }
    }
    fetchConsortiums()
  }, [authenticated])

  // Auto-join if code is in URL
  useEffect(() => {
    if (inviteCode && authenticated) {
      handleJoin(inviteCode)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleJoin = async (invCode) => {
    if (!invCode.trim()) {
      setError('Ingresa un codigo de invitacion valido.')
      return
    }
    setJoining(true)
    setError('')
    setSuccess('')

    try {
      const result = await acceptInvitation(invCode.trim())
      setSuccess(`Te has unido al consorcio "${result.consortium_name || result.name || 'exitosamente'}"`)
      setTimeout(() => {
        if (result.consortium_id || result.id) {
          navigate(`/consortiums/${result.consortium_id || result.id}`)
        } else {
          navigate('/dashboard')
        }
      }, 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setJoining(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: COLORS.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 16,
    }}>
      <div style={{ width: '100%', maxWidth: 560 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 32 }}>
          <div style={{
            width: 40, height: 40, background: COLORS.primary, borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8,
          }}>
            <svg width="24" height="24" fill="none" stroke="#fff" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <span style={{ fontSize: 24, fontWeight: 600, color: COLORS.text }}>Xcapit</span>
          <span style={{ fontSize: 24, fontWeight: 300, color: COLORS.primary, marginLeft: 4 }}>Privacy</span>
        </div>

        {/* Main card - Join by code */}
        <div style={{
          background: COLORS.card, borderRadius: 16, boxShadow: '0 20px 60px rgba(0,0,0,0.08)',
          padding: 32, marginBottom: 24,
        }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, margin: '0 0 8px', textAlign: 'center' }}>
            Unirse a un consorcio
          </h1>
          <p style={{ color: COLORS.muted, textAlign: 'center', margin: '0 0 24px', fontSize: 15 }}>
            Ingresa tu codigo de invitacion para unirte a un consorcio de aprendizaje federado.
          </p>

          {!authenticated && (
            <div style={{
              background: COLORS.warningLight, borderRadius: 10, padding: '12px 16px', marginBottom: 20,
              border: `1px solid #fde68a`,
            }}>
              <p style={{ margin: 0, fontSize: 14, color: '#92400e' }}>
                Debes{' '}
                <Link to="/login" style={{ color: COLORS.primary, fontWeight: 600 }}>iniciar sesion</Link>
                {' '}o{' '}
                <Link to="/register" style={{ color: COLORS.primary, fontWeight: 600 }}>registrarte</Link>
                {' '}antes de unirte a un consorcio.
              </p>
            </div>
          )}

          {error && (
            <div style={{
              background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
              padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
            }}>
              {error}
            </div>
          )}

          {success && (
            <div style={{
              background: COLORS.successLight, border: '1px solid #bbf7d0', color: COLORS.success,
              padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
            }}>
              {success}
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleJoin(code); }}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
                Codigo de invitacion
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Ej: INV-abc123def456"
                disabled={!authenticated}
                style={{
                  width: '100%', padding: '12px 16px', border: `1px solid ${COLORS.border}`,
                  borderRadius: 10, fontSize: 15, color: COLORS.text, outline: 'none',
                  boxSizing: 'border-box', transition: 'border-color 0.2s',
                  fontFamily: 'monospace', letterSpacing: 0.5,
                  background: authenticated ? COLORS.card : '#f3f4f6',
                }}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>

            <button
              type="submit"
              disabled={joining || !authenticated || !code.trim()}
              style={{
                width: '100%', padding: '14px 0', borderRadius: 10, border: 'none',
                background: (joining || !authenticated || !code.trim()) ? '#a5b4fc' : COLORS.primary,
                color: '#fff', fontSize: 16, fontWeight: 600,
                cursor: (joining || !authenticated || !code.trim()) ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseOver={(e) => { if (!joining && authenticated && code.trim()) e.target.style.background = COLORS.primaryHover }}
              onMouseOut={(e) => { if (!joining && authenticated && code.trim()) e.target.style.background = COLORS.primary }}
            >
              {joining ? 'Uniendose...' : 'Unirse al consorcio'}
            </button>
          </form>
        </div>

        {/* Available consortiums (if authenticated) */}
        {authenticated && availableConsortiums.length > 0 && (
          <div style={{
            background: COLORS.card, borderRadius: 16, boxShadow: '0 20px 60px rgba(0,0,0,0.08)',
            padding: 32,
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
              Consorcios disponibles
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {availableConsortiums.map((c) => (
                <div key={c.id || c.name} style={{
                  border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 16,
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  transition: 'border-color 0.2s',
                }}
                  onMouseOver={(e) => e.currentTarget.style.borderColor = COLORS.primary}
                  onMouseOut={(e) => e.currentTarget.style.borderColor = COLORS.border}
                >
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, marginBottom: 4 }}>
                      {c.name}
                    </div>
                    <div style={{ display: 'flex', gap: 16, fontSize: 13, color: COLORS.muted }}>
                      <span>{MODEL_LABELS[c.model_type] || c.model_type || 'Sin modelo'}</span>
                      <span>{c.member_count || c.members_count || 0} miembros</span>
                    </div>
                  </div>
                  <Link to={`/consortiums/${c.id}`} style={{
                    padding: '8px 16px', borderRadius: 8, background: COLORS.primaryLight,
                    color: COLORS.primary, textDecoration: 'none', fontSize: 14, fontWeight: 500,
                  }}>
                    Ver
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer links */}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <p style={{ fontSize: 14, color: COLORS.muted }}>
            Quieres crear tu propio consorcio?{' '}
            <Link to={authenticated ? '/consortiums/new' : '/register'} style={{
              color: COLORS.primary, fontWeight: 500, textDecoration: 'none',
            }}>
              {authenticated ? 'Crear consorcio' : 'Registrate primero'}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

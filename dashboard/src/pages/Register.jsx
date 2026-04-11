import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerCompany } from '../api/client'
import { startTrial } from '../api/trial'

const COLORS = {
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f9fafb',
  card: '#ffffff',
  text: '#111827',
  muted: '#6b7280',
  border: '#e5e7eb',
  borderFocus: '#6366f1',
}

const INDUSTRIES = [
  { value: '', label: 'Selecciona una industria' },
  { value: 'finanzas', label: 'Finanzas y Banca' },
  { value: 'salud', label: 'Salud y Farmaceutica' },
  { value: 'retail', label: 'Retail y Comercio' },
  { value: 'seguros', label: 'Seguros' },
  { value: 'tecnologia', label: 'Tecnologia' },
  { value: 'manufactura', label: 'Manufactura' },
  { value: 'gobierno', label: 'Gobierno y Sector Publico' },
  { value: 'educacion', label: 'Educacion' },
  { value: 'energia', label: 'Energia y Utilities' },
  { value: 'otra', label: 'Otra' },
]

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [industry, setIndustry] = useState('')
  const [loading, setLoading] = useState(false)
  const [trialStarting, setTrialStarting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await registerCompany(name, email)
      setSuccess(result)

      // Auto-start the 14-day trial
      setTrialStarting(true)
      try {
        await startTrial()
      } catch (_trialErr) {
        // Trial start might fail if already active, we still proceed
      }
      setTrialStarting(false)

      // Redirect to trial dashboard after showing API key
      setTimeout(() => navigate('/trial'), 4000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div style={{
        minHeight: '100vh',
        background: COLORS.bg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}>
        <div style={{
          background: COLORS.card,
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
          padding: 40,
          width: '100%',
          maxWidth: 440,
          textAlign: 'center',
        }}>
          {/* Success icon */}
          <div style={{
            width: 64,
            height: 64,
            background: COLORS.successLight,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}>
            <svg width="32" height="32" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h2 style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Registro exitoso
          </h2>
          <p style={{ color: COLORS.muted, margin: '0 0 24px', fontSize: 15 }}>
            Tu cuenta ha sido creada y tu periodo de prueba de 14 dias comienza ahora.
          </p>

          {/* Trial badge */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 16px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: 24,
            color: '#fff',
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 24,
          }}>
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            14 dias de prueba gratuita activados
          </div>

          {/* API Key */}
          <div style={{
            background: '#f1f5f9',
            borderRadius: 12,
            padding: 16,
            marginBottom: 24,
          }}>
            <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 6px' }}>
              Tu API Key (guardala en un lugar seguro)
            </p>
            <code style={{
              fontSize: 13,
              fontFamily: 'monospace',
              color: COLORS.text,
              wordBreak: 'break-all',
              lineHeight: 1.5,
            }}>
              {success.api_key}
            </code>
          </div>

          {trialStarting ? (
            <p style={{ fontSize: 14, color: COLORS.primary }}>
              Activando periodo de prueba...
            </p>
          ) : (
            <p style={{ fontSize: 14, color: COLORS.muted }}>
              Redirigiendo al panel de prueba en unos segundos...
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: COLORS.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16,
    }}>
      <div style={{
        background: COLORS.card,
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
        padding: 40,
        width: '100%',
        maxWidth: 440,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 32 }}>
          <div style={{
            width: 40,
            height: 40,
            background: COLORS.primary,
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 8,
          }}>
            <svg width="24" height="24" fill="none" stroke="#fff" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <span style={{ fontSize: 24, fontWeight: 600, color: COLORS.text }}>Xcapit</span>
          <span style={{ fontSize: 24, fontWeight: 300, color: COLORS.primary, marginLeft: 4 }}>Privacy</span>
        </div>

        <h1 style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, textAlign: 'center', margin: '0 0 8px' }}>
          Crear cuenta
        </h1>
        <p style={{ color: COLORS.muted, textAlign: 'center', margin: '0 0 8px', fontSize: 15 }}>
          Registra tu empresa y comienza tu periodo de prueba gratuito.
        </p>

        {/* Trial banner */}
        <div style={{
          background: COLORS.primaryLight,
          border: `1px solid ${COLORS.primary}33`,
          borderRadius: 10,
          padding: '10px 16px',
          marginBottom: 24,
          textAlign: 'center',
        }}>
          <p style={{ margin: 0, fontSize: 14, color: COLORS.primary, fontWeight: 600 }}>
            Incluye 14 dias de prueba gratuita con todas las funciones
          </p>
        </div>

        {error && (
          <div style={{
            background: COLORS.dangerLight,
            border: `1px solid #fecaca`,
            color: COLORS.danger,
            padding: '12px 16px',
            borderRadius: 10,
            marginBottom: 20,
            fontSize: 14,
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Company Name */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
              Nombre de la empresa
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: Mi Empresa S.A."
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                border: `1px solid ${COLORS.border}`,
                borderRadius: 10,
                fontSize: 15,
                color: COLORS.text,
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            />
          </div>

          {/* Email */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
              Email corporativo
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="contacto@miempresa.com"
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                border: `1px solid ${COLORS.border}`,
                borderRadius: 10,
                fontSize: 15,
                color: COLORS.text,
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            />
          </div>

          {/* Industry */}
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
              Industria
            </label>
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: `1px solid ${COLORS.border}`,
                borderRadius: 10,
                fontSize: 15,
                color: industry ? COLORS.text : COLORS.muted,
                outline: 'none',
                boxSizing: 'border-box',
                background: COLORS.card,
                cursor: 'pointer',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            >
              {INDUSTRIES.map((ind) => (
                <option key={ind.value} value={ind.value}>
                  {ind.label}
                </option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px 0',
              background: loading ? '#a5b4fc' : COLORS.primary,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s',
              marginBottom: 8,
            }}
            onMouseOver={(e) => { if (!loading) e.target.style.background = COLORS.primaryHover }}
            onMouseOut={(e) => { if (!loading) e.target.style.background = COLORS.primary }}
          >
            {loading ? 'Registrando...' : 'Crear cuenta e iniciar prueba gratuita'}
          </button>

          <p style={{ textAlign: 'center', fontSize: 12, color: COLORS.muted, margin: '4px 0 0' }}>
            Al registrarte, aceptas los terminos de servicio y la politica de privacidad.
          </p>
        </form>

        <p style={{ textAlign: 'center', color: COLORS.muted, marginTop: 24, fontSize: 15 }}>
          Ya tienes cuenta?{' '}
          <Link to="/login" style={{ color: COLORS.primary, fontWeight: 500, textDecoration: 'none' }}>
            Iniciar sesion
          </Link>
        </p>

        {/* Sandbox demo link */}
        <div style={{
          marginTop: 28,
          paddingTop: 24,
          borderTop: `1px solid ${COLORS.border}`,
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 14, color: COLORS.muted, marginBottom: 12 }}>
            Quieres ver primero como funciona?
          </p>
          <Link
            to="/sandbox-demo"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 20px',
              border: `2px solid ${COLORS.primary}33`,
              borderRadius: 10,
              color: COLORS.primary,
              fontWeight: 500,
              textDecoration: 'none',
              fontSize: 14,
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = COLORS.primaryLight}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Probar Sandbox Demo
          </Link>
        </div>
      </div>
    </div>
  )
}

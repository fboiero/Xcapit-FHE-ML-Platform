import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createConsortium } from '../api/client'

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

const MODEL_TYPES = [
  { value: '', label: 'Selecciona un tipo de modelo' },
  { value: 'linear_regression', label: 'Regresion lineal', desc: 'Ideal para predicciones numericas simples' },
  { value: 'logistic_regression', label: 'Regresion logistica', desc: 'Clasificacion binaria con probabilidades' },
  { value: 'random_forest', label: 'Random Forest', desc: 'Modelo de ensamble para clasificacion y regresion' },
  { value: 'neural_network', label: 'Red neuronal', desc: 'Deep learning para patrones complejos' },
]

const ENCRYPTION_OPTIONS = [
  { value: 'ckks', label: 'CKKS', desc: 'Encriptacion homomorfica para operaciones con decimales' },
  { value: 'bfv', label: 'BFV', desc: 'Encriptacion homomorfica para operaciones con enteros' },
]

const inputStyle = {
  width: '100%',
  padding: '12px 16px',
  border: `1px solid ${COLORS.border}`,
  borderRadius: 10,
  fontSize: 15,
  color: COLORS.text,
  outline: 'none',
  boxSizing: 'border-box',
  transition: 'border-color 0.2s',
  background: COLORS.card,
}

const labelStyle = {
  display: 'block',
  fontSize: 14,
  fontWeight: 500,
  color: '#374151',
  marginBottom: 6,
}

export default function ConsortiumCreate() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [modelType, setModelType] = useState('')
  const [encryptionScheme, setEncryptionScheme] = useState('ckks')
  const [polyDegree, setPolyDegree] = useState(8192)
  const [minMembers, setMinMembers] = useState(2)
  const [isPrivate, setIsPrivate] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState(1)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !modelType) {
      setError('El nombre y tipo de modelo son obligatorios.')
      return
    }
    setLoading(true)
    setError('')

    try {
      const mlConfig = {
        encryption_scheme: encryptionScheme,
        poly_modulus_degree: polyDegree,
        min_members: minMembers,
        is_private: isPrivate,
      }
      const result = await createConsortium(name, description, modelType, mlConfig)
      navigate(`/consortiums/${result.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const canProceed = step === 1 ? (name.trim() && modelType) : true

  return (
    <div style={{ padding: 32, maxWidth: 720, margin: '0 auto' }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
        <Link to="/dashboard" style={{ color: COLORS.muted, textDecoration: 'none', fontSize: 14 }}>Dashboard</Link>
        <span style={{ color: COLORS.muted, fontSize: 14 }}>/</span>
        <span style={{ color: COLORS.text, fontSize: 14, fontWeight: 500 }}>Crear consorcio</span>
      </div>

      <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
        Crear nuevo consorcio
      </h1>
      <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 32px' }}>
        Configura un consorcio de aprendizaje federado con privacidad.
      </p>

      {/* Progress steps */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 32 }}>
        {[{ n: 1, label: 'Informacion basica' }, { n: 2, label: 'Configuracion avanzada' }].map((s, idx) => (
          <div key={s.n} style={{ display: 'flex', alignItems: 'center', flex: idx === 0 ? 1 : 0 }}>
            <button
              onClick={() => setStep(s.n)}
              style={{
                width: 32, height: 32, borderRadius: '50%', border: 'none', cursor: 'pointer',
                background: step >= s.n ? COLORS.primary : COLORS.border,
                color: step >= s.n ? '#fff' : COLORS.muted,
                fontWeight: 600, fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              {s.n}
            </button>
            <span style={{
              fontSize: 14, fontWeight: step === s.n ? 600 : 400,
              color: step === s.n ? COLORS.text : COLORS.muted, marginLeft: 8,
            }}>
              {s.label}
            </span>
            {idx === 0 && (
              <div style={{
                flex: 1, height: 2, background: step >= 2 ? COLORS.primary : COLORS.border,
                margin: '0 16px',
              }} />
            )}
          </div>
        ))}
      </div>

      {error && (
        <div style={{
          background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28,
        }}>
          {step === 1 && (
            <>
              {/* Name */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Nombre del consorcio *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej: Consorcio Salud Latam"
                  required
                  style={inputStyle}
                  onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                  onBlur={(e) => e.target.style.borderColor = COLORS.border}
                />
              </div>

              {/* Description */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Descripcion</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe el proposito del consorcio y los datos que se compartiran..."
                  rows={4}
                  style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit' }}
                  onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                  onBlur={(e) => e.target.style.borderColor = COLORS.border}
                />
              </div>

              {/* Model type */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Tipo de modelo *</label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  required
                  style={{ ...inputStyle, cursor: 'pointer', color: modelType ? COLORS.text : COLORS.muted }}
                  onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                  onBlur={(e) => e.target.style.borderColor = COLORS.border}
                >
                  {MODEL_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
                {modelType && (
                  <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>
                    {MODEL_TYPES.find(t => t.value === modelType)?.desc}
                  </p>
                )}
              </div>

              {/* Privacy toggle */}
              <div style={{ marginBottom: 8 }}>
                <label style={{ ...labelStyle, marginBottom: 12 }}>Visibilidad</label>
                <div style={{ display: 'flex', gap: 12 }}>
                  {[{ val: true, label: 'Privado', desc: 'Solo por invitacion' }, { val: false, label: 'Publico', desc: 'Cualquiera puede unirse' }].map((opt) => (
                    <button
                      key={String(opt.val)}
                      type="button"
                      onClick={() => setIsPrivate(opt.val)}
                      style={{
                        flex: 1, padding: '14px 16px', borderRadius: 10, cursor: 'pointer',
                        border: `2px solid ${isPrivate === opt.val ? COLORS.primary : COLORS.border}`,
                        background: isPrivate === opt.val ? COLORS.primaryLight : COLORS.card,
                        textAlign: 'left', transition: 'border-color 0.2s',
                      }}
                    >
                      <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{opt.label}</div>
                      <div style={{ fontSize: 13, color: COLORS.muted, marginTop: 2 }}>{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              {/* Encryption scheme */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Esquema de encriptacion</label>
                <div style={{ display: 'flex', gap: 12 }}>
                  {ENCRYPTION_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setEncryptionScheme(opt.value)}
                      style={{
                        flex: 1, padding: '14px 16px', borderRadius: 10, cursor: 'pointer',
                        border: `2px solid ${encryptionScheme === opt.value ? COLORS.primary : COLORS.border}`,
                        background: encryptionScheme === opt.value ? COLORS.primaryLight : COLORS.card,
                        textAlign: 'left', transition: 'border-color 0.2s',
                      }}
                    >
                      <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{opt.label}</div>
                      <div style={{ fontSize: 13, color: COLORS.muted, marginTop: 2 }}>{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Polynomial degree */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Grado del polinomio (poly_modulus_degree)</label>
                <select
                  value={polyDegree}
                  onChange={(e) => setPolyDegree(Number(e.target.value))}
                  style={{ ...inputStyle, cursor: 'pointer' }}
                >
                  <option value={4096}>4096 - Rapido, menor seguridad</option>
                  <option value={8192}>8192 - Balanceado (recomendado)</option>
                  <option value={16384}>16384 - Alta seguridad, mas lento</option>
                </select>
                <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>
                  Mayor grado = mayor seguridad pero mas tiempo de computo.
                </p>
              </div>

              {/* Min members */}
              <div style={{ marginBottom: 8 }}>
                <label style={labelStyle}>Miembros minimos para entrenar</label>
                <input
                  type="number"
                  min={2}
                  max={50}
                  value={minMembers}
                  onChange={(e) => setMinMembers(Number(e.target.value))}
                  style={{ ...inputStyle, maxWidth: 120 }}
                  onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                  onBlur={(e) => e.target.style.borderColor = COLORS.border}
                />
                <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>
                  Cantidad minima de participantes antes de poder iniciar el entrenamiento.
                </p>
              </div>
            </>
          )}
        </div>

        {/* Summary card on step 2 */}
        {step === 2 && name && (
          <div style={{
            background: COLORS.primaryLight, borderRadius: 12, padding: 20, marginTop: 20,
            border: `1px solid ${COLORS.primary}33`,
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 12px' }}>
              Resumen de configuracion
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 24px', fontSize: 14 }}>
              <div><span style={{ color: COLORS.muted }}>Nombre:</span> <strong>{name}</strong></div>
              <div><span style={{ color: COLORS.muted }}>Modelo:</span> <strong>{MODEL_TYPES.find(t => t.value === modelType)?.label || '-'}</strong></div>
              <div><span style={{ color: COLORS.muted }}>Encriptacion:</span> <strong>{encryptionScheme.toUpperCase()}</strong></div>
              <div><span style={{ color: COLORS.muted }}>Poly degree:</span> <strong>{polyDegree}</strong></div>
              <div><span style={{ color: COLORS.muted }}>Visibilidad:</span> <strong>{isPrivate ? 'Privado' : 'Publico'}</strong></div>
              <div><span style={{ color: COLORS.muted }}>Min. miembros:</span> <strong>{minMembers}</strong></div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24 }}>
          {step === 2 ? (
            <button
              type="button"
              onClick={() => setStep(1)}
              style={{
                padding: '12px 24px', borderRadius: 10, border: `1px solid ${COLORS.border}`,
                background: COLORS.card, color: COLORS.text, fontSize: 15, fontWeight: 500, cursor: 'pointer',
              }}
            >
              Anterior
            </button>
          ) : (
            <div />
          )}

          {step === 1 ? (
            <button
              type="button"
              onClick={() => canProceed && setStep(2)}
              disabled={!canProceed}
              style={{
                padding: '12px 28px', borderRadius: 10, border: 'none',
                background: canProceed ? COLORS.primary : '#a5b4fc',
                color: '#fff', fontSize: 15, fontWeight: 600,
                cursor: canProceed ? 'pointer' : 'not-allowed', transition: 'background 0.2s',
              }}
              onMouseOver={(e) => { if (canProceed) e.target.style.background = COLORS.primaryHover }}
              onMouseOut={(e) => { if (canProceed) e.target.style.background = COLORS.primary }}
            >
              Siguiente
            </button>
          ) : (
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '12px 28px', borderRadius: 10, border: 'none',
                background: loading ? '#a5b4fc' : COLORS.primary,
                color: '#fff', fontSize: 15, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer', transition: 'background 0.2s',
              }}
              onMouseOver={(e) => { if (!loading) e.target.style.background = COLORS.primaryHover }}
              onMouseOut={(e) => { if (!loading) e.target.style.background = COLORS.primary }}
            >
              {loading ? 'Creando...' : 'Crear consorcio'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

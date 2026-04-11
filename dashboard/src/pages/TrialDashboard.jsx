import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  getTrialStatus,
  getTrialUsage,
  requestUpgrade,
  getPlansComparison,
  uploadTrialData,
  startTrial,
  formatBytes,
  formatLimit,
} from '../api/trial'

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
}

const PLAN_PRICES = {
  free: 'Gratis',
  starter: '$99/mes',
  professional: '$499/mes',
  enterprise: 'Contactar',
}

const PLAN_NAMES = {
  free: 'Gratuito',
  starter: 'Starter',
  professional: 'Profesional',
  enterprise: 'Enterprise',
}

// ---- Countdown Timer --------------------------------------------------------

function CountdownTimer({ endDate }) {
  const [time, setTime] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 })

  useEffect(() => {
    if (!endDate) return

    const calculate = () => {
      const now = new Date()
      const end = new Date(endDate)
      const diff = end - now

      if (diff <= 0) {
        setTime({ days: 0, hours: 0, minutes: 0, seconds: 0 })
        return
      }

      setTime({
        days: Math.floor(diff / (1000 * 60 * 60 * 24)),
        hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((diff % (1000 * 60)) / 1000),
      })
    }

    calculate()
    const interval = setInterval(calculate, 1000)
    return () => clearInterval(interval)
  }, [endDate])

  const blocks = [
    { value: time.days, label: 'Dias' },
    { value: time.hours, label: 'Horas' },
    { value: time.minutes, label: 'Minutos' },
    { value: time.seconds, label: 'Segundos' },
  ]

  const isUrgent = time.days <= 2

  return (
    <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
      {blocks.map((block) => (
        <div key={block.label} style={{
          textAlign: 'center',
          minWidth: 64,
        }}>
          <div style={{
            background: isUrgent ? COLORS.dangerLight : COLORS.primaryLight,
            borderRadius: 12,
            padding: '12px 8px',
            marginBottom: 4,
          }}>
            <span style={{
              fontSize: 28,
              fontWeight: 800,
              color: isUrgent ? COLORS.danger : COLORS.primary,
              fontVariantNumeric: 'tabular-nums',
            }}>
              {String(block.value).padStart(2, '0')}
            </span>
          </div>
          <span style={{ fontSize: 11, color: COLORS.muted, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            {block.label}
          </span>
        </div>
      ))}
    </div>
  )
}

// ---- Animated Usage Meter ---------------------------------------------------

function AnimatedUsageMeter({ label, used, limit, unit, icon }) {
  const [animatedPct, setAnimatedPct] = useState(0)
  const isUnlimited = limit === -1
  const targetPct = isUnlimited ? 0 : Math.min(100, (used / limit) * 100)
  const color = targetPct >= 90 ? COLORS.danger : targetPct >= 70 ? COLORS.warning : COLORS.success
  const bgColor = targetPct >= 90 ? COLORS.dangerLight : targetPct >= 70 ? COLORS.warningLight : COLORS.successLight

  useEffect(() => {
    let raf
    const start = performance.now()
    const duration = 800

    const animate = (now) => {
      const progress = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedPct(eased * targetPct)

      if (progress < 1) {
        raf = requestAnimationFrame(animate)
      }
    }

    raf = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf)
  }, [targetPct])

  const formatValue = (val) => {
    if (unit === 'bytes') return formatBytes(val)
    return val.toLocaleString()
  }

  const formatLimitValue = (val) => {
    if (val === -1) return 'Ilimitado'
    if (unit === 'bytes') return formatBytes(val)
    return val.toLocaleString()
  }

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {icon && (
            <div style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: bgColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {icon}
            </div>
          )}
          <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{label}</span>
        </div>
        <span style={{ fontSize: 13, color: COLORS.muted }}>
          {formatValue(used)} / {formatLimitValue(limit)}
        </span>
      </div>
      <div style={{
        background: '#e5e7eb',
        borderRadius: 10,
        height: 10,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${isUnlimited ? 0 : animatedPct}%`,
          background: `linear-gradient(90deg, ${color}, ${color}cc)`,
          height: '100%',
          borderRadius: 10,
          transition: 'none',
          position: 'relative',
        }}>
          {animatedPct > 5 && (
            <div style={{
              position: 'absolute',
              right: 0,
              top: 0,
              bottom: 0,
              width: 3,
              background: 'rgba(255,255,255,0.6)',
              borderRadius: 2,
            }} />
          )}
        </div>
      </div>
      {targetPct >= 80 && (
        <p style={{
          fontSize: 12,
          color: targetPct >= 90 ? COLORS.danger : COLORS.warning,
          margin: '4px 0 0',
          fontWeight: 500,
        }}>
          {targetPct >= 90 ? 'Limite casi alcanzado - considera hacer upgrade' : 'Acercandose al limite'}
        </p>
      )}
    </div>
  )
}

// ---- Quick Action Card ------------------------------------------------------

function QuickAction({ title, description, icon, onClick, color, disabled }) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered && !disabled ? `${color}11` : COLORS.card,
        border: `1px solid ${hovered && !disabled ? color : COLORS.border}`,
        borderRadius: 12,
        padding: 20,
        cursor: disabled ? 'not-allowed' : 'pointer',
        textAlign: 'left',
        width: '100%',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s',
        transform: hovered && !disabled ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered && !disabled ? '0 4px 12px rgba(0,0,0,0.08)' : 'none',
      }}
    >
      <div style={{
        width: 40,
        height: 40,
        borderRadius: 10,
        background: `${color}18`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 12,
      }}>
        {icon}
      </div>
      <h4 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 4px' }}>
        {title}
      </h4>
      <p style={{ fontSize: 13, color: COLORS.muted, margin: 0, lineHeight: 1.4 }}>
        {description}
      </p>
    </button>
  )
}

// ---- Upload Item ------------------------------------------------------------

function UploadItem({ file }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 0',
      borderBottom: `1px solid ${COLORS.border}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 36,
          height: 36,
          borderRadius: 8,
          background: COLORS.primaryLight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <svg width="18" height="18" fill="none" stroke={COLORS.primary} viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>
        <div>
          <p style={{ fontSize: 14, fontWeight: 500, color: COLORS.text, margin: 0 }}>
            {file.name}
          </p>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '2px 0 0' }}>
            {file.consortium} - {file.date}
          </p>
        </div>
      </div>
      <span style={{ fontSize: 13, color: COLORS.muted }}>{file.size}</span>
    </div>
  )
}

// ---- Upgrade Modal ----------------------------------------------------------

function UpgradeModal({ plans, currentTier, onUpgrade, onClose, loading }) {
  const tierOrder = ['free', 'starter', 'professional', 'enterprise']

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: 16,
    }}
    onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        background: COLORS.card,
        borderRadius: 20,
        maxWidth: 900,
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        padding: 32,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, margin: '0 0 4px' }}>
              Elegir un plan
            </h2>
            <p style={{ fontSize: 15, color: COLORS.muted, margin: 0 }}>
              Selecciona el plan que mejor se adapte a tus necesidades
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              background: COLORS.card,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="20" height="20" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
          {plans.map((plan) => {
            const isCurrent = plan.tier === currentTier
            const isDowngrade = tierOrder.indexOf(plan.tier) <= tierOrder.indexOf(currentTier)
            const isEnterprise = plan.tier === 'enterprise'
            const isPro = plan.tier === 'professional'

            return (
              <div
                key={plan.tier}
                style={{
                  border: isCurrent ? `2px solid ${COLORS.primary}` : isPro ? `2px solid ${COLORS.primary}` : `1px solid ${COLORS.border}`,
                  borderRadius: 16,
                  padding: 24,
                  background: isCurrent ? COLORS.primaryLight : COLORS.card,
                  flex: '1 1 180px',
                  minWidth: 180,
                  maxWidth: 210,
                  position: 'relative',
                }}
              >
                {isPro && !isCurrent && (
                  <div style={{
                    position: 'absolute',
                    top: -10,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: COLORS.warning,
                    color: '#fff',
                    padding: '3px 12px',
                    borderRadius: 12,
                    fontSize: 11,
                    fontWeight: 700,
                  }}>
                    Recomendado
                  </div>
                )}
                <h3 style={{ fontSize: 17, fontWeight: 700, color: COLORS.text, margin: '0 0 4px' }}>
                  {PLAN_NAMES[plan.tier] || plan.name}
                </h3>
                <p style={{ fontSize: 22, fontWeight: 800, color: COLORS.primary, margin: '0 0 12px' }}>
                  {PLAN_PRICES[plan.tier]}
                </p>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px', fontSize: 13, lineHeight: 2, color: '#374151' }}>
                  <li>{formatLimit(plan.daily_requests)} req/dia</li>
                  <li>{formatLimit(plan.max_models)} modelos</li>
                  <li>{formatLimit(plan.max_consortiums)} consorcios</li>
                  <li>{plan.max_upload_mb === -1 ? 'Ilimitado' : `${plan.max_upload_mb} MB`} datos</li>
                  <li>{formatLimit(plan.training_runs_per_day)} entrenos/dia</li>
                </ul>

                {isCurrent ? (
                  <button disabled style={{
                    width: '100%',
                    padding: '10px 0',
                    borderRadius: 8,
                    border: 'none',
                    background: '#c7d2fe',
                    color: '#4338ca',
                    fontWeight: 600,
                    fontSize: 14,
                    cursor: 'default',
                  }}>
                    Plan actual
                  </button>
                ) : !isDowngrade ? (
                  <button
                    onClick={() => onUpgrade(plan.tier)}
                    disabled={loading}
                    style={{
                      width: '100%',
                      padding: '10px 0',
                      borderRadius: 8,
                      border: 'none',
                      background: COLORS.primary,
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: 14,
                      cursor: loading ? 'not-allowed' : 'pointer',
                      opacity: loading ? 0.7 : 1,
                    }}
                  >
                    {loading ? 'Procesando...' : isEnterprise ? 'Contactar ventas' : 'Hacer upgrade'}
                  </button>
                ) : null}
              </div>
            )
          })}
        </div>

        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <Link to="/pricing" style={{ fontSize: 14, color: COLORS.primary, textDecoration: 'none', fontWeight: 500 }}>
            Ver comparacion completa de planes
          </Link>
        </div>
      </div>
    </div>
  )
}

// ---- Main Component ---------------------------------------------------------

export default function TrialDashboard() {
  const navigate = useNavigate()
  const [status, setStatus] = useState(null)
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadConsortiumId, setUploadConsortiumId] = useState('')
  const [uploadStatus, setUploadStatus] = useState(null)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const fileInputRef = useRef(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [statusData, plansData] = await Promise.all([
        getTrialStatus(),
        getPlansComparison(),
      ])
      setStatus(statusData)
      setPlans(plansData)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Auto-dismiss success messages
  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(null), 5000)
      return () => clearTimeout(t)
    }
  }, [successMsg])

  const handleStartTrial = async () => {
    try {
      setLoading(true)
      await startTrial()
      setSuccessMsg('Periodo de prueba de 14 dias activado exitosamente.')
      await fetchData()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const handleUpgrade = async (tier) => {
    if (tier === 'enterprise') {
      window.open('mailto:sales@xcapit.com?subject=Plan%20Enterprise%20-%20Xcapit%20Privacy', '_blank')
      return
    }
    try {
      setUpgrading(true)
      await requestUpgrade(tier)
      setSuccessMsg(`Upgrade a ${PLAN_NAMES[tier]} realizado exitosamente.`)
      setShowUpgradeModal(false)
      await fetchData()
    } catch (err) {
      setError(err.message)
    } finally {
      setUpgrading(false)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!uploadFile || !uploadConsortiumId) return

    try {
      setUploadStatus({ type: 'loading', message: 'Subiendo archivo...' })
      const result = await uploadTrialData(uploadConsortiumId, uploadFile)
      setUploadStatus({
        type: 'success',
        message: `Archivo "${result.file_name}" subido exitosamente (${formatBytes(result.file_size)})`,
      })
      setUploadFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      await fetchData()
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.message })
    }
  }

  // Loading state
  if (loading && !status) {
    return (
      <div style={{
        padding: 64,
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
      }}>
        <div style={{
          width: 40,
          height: 40,
          border: `4px solid ${COLORS.border}`,
          borderTopColor: COLORS.primary,
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted, fontSize: 15 }}>Cargando panel de prueba...</p>
      </div>
    )
  }

  const usage = status?.usage || {}
  const limits = status?.limits || {}
  const isTrial = status?.is_trial
  const isExpired = status?.trial_expired
  const trialEnd = status?.trial_end_date

  // Mock recent uploads for display
  const recentUploads = status?.recent_uploads || [
    { name: 'transacciones_q4_2025.csv', consortium: 'Consorcio Finanzas', date: 'Hace 2 horas', size: '12.4 MB' },
    { name: 'clientes_anonimizados.json', consortium: 'Consorcio Retail', date: 'Hace 1 dia', size: '3.2 MB' },
    { name: 'diagnosticos_encriptados.parquet', consortium: 'Consorcio Salud', date: 'Hace 3 dias', size: '28.7 MB' },
  ]

  return (
    <div style={{ maxWidth: 1140, margin: '0 auto', padding: '24px 20px' }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
      `}</style>

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 28,
        flexWrap: 'wrap',
        gap: 16,
      }}>
        <div>
          <h1 style={{ margin: '0 0 6px', fontSize: 28, fontWeight: 800, color: COLORS.text }}>
            Panel de Prueba
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14, color: COLORS.muted }}>
              Plan: <strong style={{ color: COLORS.text }}>{PLAN_NAMES[status?.tier] || status?.tier?.toUpperCase()}</strong>
            </span>
            {isTrial && (
              <span style={{
                padding: '3px 10px',
                borderRadius: 12,
                fontSize: 12,
                fontWeight: 600,
                background: isExpired ? COLORS.dangerLight : COLORS.successLight,
                color: isExpired ? COLORS.danger : COLORS.success,
              }}>
                {isExpired ? 'Prueba expirada' : `${status?.trial_days_remaining} dias restantes`}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {!isTrial && status?.tier === 'free' && !status?.trial_days_remaining && (
            <button
              onClick={handleStartTrial}
              style={{
                padding: '10px 24px',
                borderRadius: 10,
                border: 'none',
                background: COLORS.primary,
                color: '#fff',
                fontWeight: 600,
                fontSize: 15,
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseOver={(e) => e.target.style.background = COLORS.primaryHover}
              onMouseOut={(e) => e.target.style.background = COLORS.primary}
            >
              Iniciar prueba de 14 dias
            </button>
          )}
          <button
            onClick={() => setShowUpgradeModal(true)}
            style={{
              padding: '10px 24px',
              borderRadius: 10,
              border: `2px solid ${COLORS.primary}`,
              background: 'transparent',
              color: COLORS.primary,
              fontWeight: 600,
              fontSize: 15,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => e.target.style.background = COLORS.primaryLight}
            onMouseOut={(e) => e.target.style.background = 'transparent'}
          >
            Hacer upgrade
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{
          padding: '12px 16px',
          marginBottom: 16,
          borderRadius: 10,
          background: COLORS.dangerLight,
          color: COLORS.danger,
          border: '1px solid #fecaca',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          animation: 'fadeIn 0.3s ease',
        }}>
          <span style={{ fontSize: 14 }}>{error}</span>
          <button
            onClick={() => setError(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.danger, fontWeight: 700, fontSize: 16 }}
          >
            x
          </button>
        </div>
      )}

      {successMsg && (
        <div style={{
          padding: '12px 16px',
          marginBottom: 16,
          borderRadius: 10,
          background: COLORS.successLight,
          color: '#16a34a',
          border: '1px solid #bbf7d0',
          fontSize: 14,
          animation: 'fadeIn 0.3s ease',
        }}>
          {successMsg}
        </div>
      )}

      {/* Trial Countdown + Subscription Info Row */}
      <div style={{ display: 'grid', gridTemplateColumns: isTrial && !isExpired ? '1fr 1fr' : '1fr', gap: 20, marginBottom: 24 }}>
        {/* Countdown */}
        {isTrial && !isExpired && (
          <div style={{
            background: COLORS.card,
            borderRadius: 16,
            border: `1px solid ${COLORS.border}`,
            padding: 28,
            textAlign: 'center',
          }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: COLORS.muted, margin: '0 0 16px', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Tiempo restante de prueba
            </h2>
            <CountdownTimer endDate={trialEnd} />
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '16px 0 0', lineHeight: 1.5 }}>
              Al finalizar tu prueba, puedes continuar con el plan Gratuito o hacer upgrade.
            </p>
          </div>
        )}

        {/* Subscription Info */}
        <div style={{
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)',
          borderRadius: 16,
          padding: 28,
          color: '#fff',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <p style={{ fontSize: 13, margin: '0 0 4px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 500 }}>
              Tu suscripcion
            </p>
            <h2 style={{ fontSize: 28, fontWeight: 800, margin: '0 0 8px' }}>
              {PLAN_NAMES[status?.tier] || 'Gratuito'}
              {isTrial && ' (Prueba)'}
            </h2>
            <p style={{ fontSize: 14, margin: '0 0 16px', opacity: 0.85, lineHeight: 1.5 }}>
              {isTrial
                ? 'Tienes acceso completo a todas las funcionalidades durante tu periodo de prueba.'
                : status?.tier === 'free'
                  ? 'Estas en el plan gratuito. Hace upgrade para desbloquear mas funcionalidades.'
                  : `Disfrutas de todas las ventajas del plan ${PLAN_NAMES[status?.tier]}.`
              }
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={() => setShowUpgradeModal(true)}
              style={{
                padding: '10px 24px',
                borderRadius: 8,
                border: '2px solid rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.15)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 14,
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.25)'}
              onMouseOut={(e) => e.target.style.background = 'rgba(255,255,255,0.15)'}
            >
              Ver planes
            </button>
            <Link
              to="/pricing"
              style={{
                padding: '10px 24px',
                borderRadius: 8,
                background: '#fff',
                color: COLORS.primary,
                fontWeight: 600,
                fontSize: 14,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              Comparar planes
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>

      {/* Usage Meters */}
      <div style={{
        background: COLORS.card,
        borderRadius: 16,
        padding: 28,
        marginBottom: 24,
        border: `1px solid ${COLORS.border}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: COLORS.text }}>
            Uso actual
          </h2>
          <button
            onClick={fetchData}
            disabled={loading}
            style={{
              background: 'none',
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: '6px 14px',
              cursor: 'pointer',
              fontSize: 13,
              color: COLORS.muted,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.183" />
            </svg>
            Actualizar
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0 40px' }}>
          <AnimatedUsageMeter
            label="Requests hoy"
            used={usage.api_requests_today || 0}
            limit={limits.daily_requests || 100}
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            }
          />
          <AnimatedUsageMeter
            label="Entrenamientos hoy"
            used={usage.training_runs_today || 0}
            limit={limits.training_runs_per_day || 5}
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342" />
              </svg>
            }
          />
          <AnimatedUsageMeter
            label="Datos subidos"
            used={usage.data_uploaded_bytes || 0}
            limit={limits.upload_bytes || 50 * 1024 * 1024}
            unit="bytes"
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
              </svg>
            }
          />
          <AnimatedUsageMeter
            label="Sandboxes activos"
            used={usage.active_sandboxes || 0}
            limit={limits.max_sandboxes || 1}
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
              </svg>
            }
          />
          <AnimatedUsageMeter
            label="Consorcios activos"
            used={usage.active_consortiums || 0}
            limit={limits.max_consortiums || 1}
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
              </svg>
            }
          />
          <AnimatedUsageMeter
            label="Modelos"
            used={usage.active_models || 0}
            limit={limits.max_models || 2}
            icon={
              <svg width="14" height="14" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Quick Actions + Recent Uploads Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Quick Actions */}
        <div style={{
          background: COLORS.card,
          borderRadius: 16,
          padding: 28,
          border: `1px solid ${COLORS.border}`,
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 18, fontWeight: 700, color: COLORS.text }}>
            Acciones rapidas
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <QuickAction
              title="Crear consorcio"
              description="Inicia un nuevo consorcio de ML colaborativo"
              color={COLORS.primary}
              onClick={() => navigate('/consortiums/new')}
              icon={
                <svg width="20" height="20" fill="none" stroke={COLORS.primary} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772" />
                </svg>
              }
            />
            <QuickAction
              title="Subir datos"
              description="Carga datos encriptados a un consorcio"
              color={COLORS.success}
              onClick={() => navigate('/data-upload')}
              icon={
                <svg width="20" height="20" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              }
            />
            <QuickAction
              title="Entrenar modelo"
              description="Inicia un entrenamiento federado"
              color={COLORS.warning}
              onClick={() => navigate('/training')}
              icon={
                <svg width="20" height="20" fill="none" stroke={COLORS.warning} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                </svg>
              }
            />
            <QuickAction
              title="Sandbox"
              description="Experimenta con datos sinteticos"
              color="#8b5cf6"
              onClick={() => navigate('/sandbox')}
              icon={
                <svg width="20" height="20" fill="none" stroke="#8b5cf6" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              }
            />
          </div>
        </div>

        {/* Recent Uploads */}
        <div style={{
          background: COLORS.card,
          borderRadius: 16,
          padding: 28,
          border: `1px solid ${COLORS.border}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: COLORS.text }}>
              Uploads recientes
            </h2>
            <Link to="/data-upload" style={{
              fontSize: 13,
              color: COLORS.primary,
              textDecoration: 'none',
              fontWeight: 500,
            }}>
              Ver todos
            </Link>
          </div>

          {recentUploads.length > 0 ? (
            <div>
              {recentUploads.map((file, idx) => (
                <UploadItem key={idx} file={file} />
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 0' }}>
              <svg width="40" height="40" fill="none" stroke={COLORS.border} viewBox="0 0 24 24" strokeWidth={1.5} style={{ margin: '0 auto 12px', display: 'block' }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
                Todavia no has subido archivos
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Data Upload Form */}
      <div style={{
        background: COLORS.card,
        borderRadius: 16,
        padding: 28,
        marginBottom: 24,
        border: `1px solid ${COLORS.border}`,
      }}>
        <h2 style={{ margin: '0 0 16px', fontSize: 18, fontWeight: 700, color: COLORS.text }}>
          Subir datos a consorcio
        </h2>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 280px' }}>
            <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: COLORS.muted, fontWeight: 500 }}>
              ID del consorcio
            </label>
            <input
              type="text"
              value={uploadConsortiumId}
              onChange={(e) => setUploadConsortiumId(e.target.value)}
              placeholder="UUID del consorcio"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 8,
                border: `1px solid ${COLORS.border}`,
                fontSize: 14,
                color: COLORS.text,
                outline: 'none',
                boxSizing: 'border-box',
              }}
              onFocus={(e) => e.target.style.borderColor = COLORS.primary}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            />
          </div>
          <div style={{ flex: '1 1 200px' }}>
            <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: COLORS.muted, fontWeight: 500 }}>
              Archivo
            </label>
            <input
              ref={fileInputRef}
              type="file"
              onChange={(e) => setUploadFile(e.target.files[0])}
              accept=".csv,.json,.parquet"
              style={{ fontSize: 14, color: COLORS.text }}
            />
          </div>
          <button
            type="submit"
            disabled={!uploadFile || !uploadConsortiumId || uploadStatus?.type === 'loading'}
            style={{
              padding: '10px 24px',
              borderRadius: 8,
              border: 'none',
              background: COLORS.primary,
              color: '#fff',
              fontWeight: 600,
              fontSize: 14,
              cursor: (!uploadFile || !uploadConsortiumId) ? 'not-allowed' : 'pointer',
              opacity: (!uploadFile || !uploadConsortiumId) ? 0.5 : 1,
              transition: 'opacity 0.2s',
            }}
          >
            {uploadStatus?.type === 'loading' ? 'Subiendo...' : 'Subir archivo'}
          </button>
        </form>

        {uploadStatus && uploadStatus.type !== 'loading' && (
          <div style={{
            marginTop: 12,
            padding: '10px 14px',
            borderRadius: 8,
            fontSize: 14,
            background: uploadStatus.type === 'success' ? COLORS.successLight : COLORS.dangerLight,
            color: uploadStatus.type === 'success' ? '#16a34a' : COLORS.danger,
            animation: 'fadeIn 0.3s ease',
          }}>
            {uploadStatus.message}
          </div>
        )}
      </div>

      {/* Trial Expired CTA */}
      {isExpired && (
        <div style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          borderRadius: 16,
          padding: 40,
          color: '#fff',
          textAlign: 'center',
          marginBottom: 24,
          animation: 'fadeIn 0.5s ease',
        }}>
          <h2 style={{ margin: '0 0 8px', fontSize: 24, fontWeight: 700 }}>
            Tu periodo de prueba ha expirado
          </h2>
          <p style={{ margin: '0 0 24px', opacity: 0.9, fontSize: 16, lineHeight: 1.5 }}>
            Hace upgrade para seguir usando la plataforma sin limitaciones. Todos tus datos y configuraciones se mantienen.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleUpgrade('starter')}
              style={{
                padding: '14px 36px',
                borderRadius: 10,
                border: '2px solid #fff',
                background: '#fff',
                color: COLORS.primary,
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: 16,
                transition: 'transform 0.2s',
              }}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              Upgrade a Starter - $99/mes
            </button>
            <button
              onClick={() => handleUpgrade('professional')}
              style={{
                padding: '14px 36px',
                borderRadius: 10,
                border: '2px solid rgba(255,255,255,0.5)',
                background: 'transparent',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: 16,
                transition: 'background 0.2s',
              }}
              onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.15)'}
              onMouseOut={(e) => e.target.style.background = 'transparent'}
            >
              Upgrade a Profesional - $499/mes
            </button>
          </div>
        </div>
      )}

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <UpgradeModal
          plans={plans}
          currentTier={status?.tier}
          onUpgrade={handleUpgrade}
          onClose={() => setShowUpgradeModal(false)}
          loading={upgrading}
        />
      )}
    </div>
  )
}

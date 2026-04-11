import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getTrialStatus, getTrialUsage, requestUpgrade } from '../api/trial'
import { getCurrentCompany } from '../api/client'

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

const PLAN_DETAILS = {
  free: { name: 'Gratuito', price: '$0', period: '/mes', color: COLORS.muted },
  starter: { name: 'Starter', price: '$99', period: '/mes', color: COLORS.primary },
  professional: { name: 'Profesional', price: '$499', period: '/mes', color: '#8b5cf6' },
  enterprise: { name: 'Enterprise', price: 'Custom', period: '', color: COLORS.text },
}

const USAGE_ITEMS = [
  { key: 'daily_requests', label: 'Requests hoy', limit_key: 'daily_requests_limit' },
  { key: 'storage_used_mb', label: 'Almacenamiento (MB)', limit_key: 'storage_limit_mb' },
  { key: 'training_runs', label: 'Entrenamientos hoy', limit_key: 'training_runs_limit' },
  { key: 'active_consortiums', label: 'Consorcios activos', limit_key: 'consortiums_limit' },
  { key: 'active_models', label: 'Modelos activos', limit_key: 'models_limit' },
]

const MOCK_INVOICES = [
  { id: 'INV-2026-03', date: '2026-03-01', amount: '$499.00', status: 'Pagado', plan: 'Profesional' },
  { id: 'INV-2026-02', date: '2026-02-01', amount: '$499.00', status: 'Pagado', plan: 'Profesional' },
  { id: 'INV-2026-01', date: '2026-01-01', amount: '$99.00', status: 'Pagado', plan: 'Starter' },
]

function UsageBar({ used, limit, label, color }) {
  const unlimited = limit === -1
  const percentage = unlimited ? 20 : Math.min((used / limit) * 100, 100)
  const isHigh = !unlimited && percentage > 80
  const barColor = isHigh ? COLORS.danger : color || COLORS.primary

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 14, color: COLORS.text }}>{label}</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: isHigh ? COLORS.danger : COLORS.text }}>
          {used.toLocaleString()} / {unlimited ? 'Ilimitado' : limit.toLocaleString()}
        </span>
      </div>
      <div style={{
        width: '100%', height: 8, background: COLORS.border, borderRadius: 4, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', borderRadius: 4, background: barColor,
          width: `${percentage}%`, transition: 'width 0.5s ease', minWidth: 2,
        }} />
      </div>
      {isHigh && (
        <p style={{ fontSize: 12, color: COLORS.danger, margin: '4px 0 0', fontWeight: 500 }}>
          Cerca del limite. Considera hacer upgrade.
        </p>
      )}
    </div>
  )
}

export default function Billing() {
  const [company, setCompany] = useState(null)
  const [trialStatus, setTrialStatus] = useState(null)
  const [usage, setUsage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState(null)
  const [upgradeMsg, setUpgradeMsg] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [companyData, trialData, usageData] = await Promise.allSettled([
          getCurrentCompany(),
          getTrialStatus(),
          getTrialUsage(),
        ])
        if (companyData.status === 'fulfilled') setCompany(companyData.value)
        if (trialData.status === 'fulfilled') setTrialStatus(trialData.value)
        if (usageData.status === 'fulfilled') setUsage(usageData.value)
      } catch (err) {
        // fallback
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleUpgrade = async (tier) => {
    setUpgrading(tier)
    setUpgradeMsg('')
    try {
      await requestUpgrade(tier)
      setUpgradeMsg(`Solicitud de upgrade a ${PLAN_DETAILS[tier]?.name || tier} enviada correctamente.`)
    } catch (err) {
      setUpgradeMsg(`Error: ${err.message}`)
    } finally {
      setUpgrading(null)
    }
  }

  const currentTier = trialStatus?.tier || company?.plan || company?.tier || 'free'
  const planInfo = PLAN_DETAILS[currentTier] || PLAN_DETAILS.free
  const isTrial = trialStatus?.is_trial && !trialStatus?.trial_expired

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando facturacion...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
        Facturacion
      </h1>
      <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 32px' }}>
        Gestiona tu suscripcion, uso y pagos
      </p>

      {upgradeMsg && (
        <div style={{
          background: upgradeMsg.startsWith('Error') ? COLORS.dangerLight : COLORS.successLight,
          color: upgradeMsg.startsWith('Error') ? COLORS.danger : COLORS.success,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
          border: `1px solid ${upgradeMsg.startsWith('Error') ? '#fecaca' : '#bbf7d0'}`,
        }}>
          {upgradeMsg}
        </div>
      )}

      {/* Current plan */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 28, marginBottom: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
              Plan actual
            </p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 32, fontWeight: 700, color: COLORS.text }}>{planInfo.name}</span>
              {isTrial && (
                <span style={{
                  padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff',
                }}>
                  Periodo de prueba - {trialStatus.trial_days_remaining || 0} dias restantes
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: planInfo.color }}>{planInfo.price}</span>
              <span style={{ fontSize: 15, color: COLORS.muted }}>{planInfo.period}</span>
            </div>
          </div>
          <Link to="/pricing" style={{
            padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            background: COLORS.card, color: COLORS.text, textDecoration: 'none',
            fontSize: 14, fontWeight: 500,
          }}>
            Ver todos los planes
          </Link>
        </div>

        {/* Upgrade buttons */}
        {currentTier !== 'enterprise' && (
          <div style={{ display: 'flex', gap: 12, marginTop: 24, flexWrap: 'wrap' }}>
            {currentTier === 'free' && (
              <button onClick={() => handleUpgrade('starter')} disabled={upgrading === 'starter'}
                style={{
                  padding: '10px 20px', borderRadius: 8, border: 'none',
                  background: upgrading === 'starter' ? '#a5b4fc' : COLORS.primary,
                  color: '#fff', fontSize: 14, fontWeight: 600, cursor: upgrading ? 'not-allowed' : 'pointer',
                }}>
                {upgrading === 'starter' ? 'Procesando...' : 'Upgrade a Starter ($99/mes)'}
              </button>
            )}
            {(currentTier === 'free' || currentTier === 'starter') && (
              <button onClick={() => handleUpgrade('professional')} disabled={upgrading === 'professional'}
                style={{
                  padding: '10px 20px', borderRadius: 8, border: 'none',
                  background: upgrading === 'professional' ? '#c4b5fd' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff', fontSize: 14, fontWeight: 600, cursor: upgrading ? 'not-allowed' : 'pointer',
                }}>
                {upgrading === 'professional' ? 'Procesando...' : 'Upgrade a Profesional ($499/mes)'}
              </button>
            )}
            <button onClick={() => handleUpgrade('enterprise')} disabled={upgrading === 'enterprise'}
              style={{
                padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                background: COLORS.card, color: COLORS.text, fontSize: 14, fontWeight: 500,
                cursor: upgrading ? 'not-allowed' : 'pointer',
              }}>
              Contactar para Enterprise
            </button>
          </div>
        )}
      </div>

      {/* Usage */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 28, marginBottom: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Uso actual
        </h2>

        {USAGE_ITEMS.map((item) => {
          const used = usage?.[item.key] || 0
          const limit = usage?.[item.limit_key] || trialStatus?.limits?.[item.limit_key] || 100
          return (
            <UsageBar
              key={item.key}
              used={used}
              limit={limit}
              label={item.label}
              color={COLORS.primary}
            />
          )
        })}
      </div>

      {/* Payment history */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 28,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Historial de pagos
        </h2>

        {MOCK_INVOICES.length === 0 ? (
          <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '16px 0' }}>
            No hay pagos registrados.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Factura', 'Fecha', 'Plan', 'Monto', 'Estado'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '10px 12px', fontSize: 13,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_INVOICES.map((inv) => (
                <tr key={inv.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: '12px', fontSize: 14, fontFamily: 'monospace', color: COLORS.text }}>
                    {inv.id}
                  </td>
                  <td style={{ padding: '12px', fontSize: 14, color: COLORS.muted }}>
                    {new Date(inv.date).toLocaleDateString('es-AR')}
                  </td>
                  <td style={{ padding: '12px', fontSize: 14, color: COLORS.text }}>{inv.plan}</td>
                  <td style={{ padding: '12px', fontSize: 14, fontWeight: 600, color: COLORS.text }}>
                    {inv.amount}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      background: COLORS.successLight, color: COLORS.success,
                    }}>
                      {inv.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <p style={{ fontSize: 13, color: COLORS.muted, margin: '16px 0 0', textAlign: 'center' }}>
          Para consultas sobre facturacion, contacta a soporte@xcapit.com
        </p>
      </div>
    </div>
  )
}

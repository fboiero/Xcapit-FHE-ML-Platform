import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getPlansComparison, formatBytes, formatLimit } from '../api/trial'

const COLORS = {
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  bg: '#f9fafb',
  card: '#ffffff',
  text: '#111827',
  muted: '#6b7280',
  border: '#e5e7eb',
}

const PLAN_META = {
  free: {
    name: 'Gratuito',
    price: '$0',
    period: 'para siempre',
    description: 'Ideal para explorar la plataforma y hacer pruebas iniciales.',
    cta: 'Empezar gratis',
    ctaLink: '/register',
    highlight: false,
    icon: (
      <svg width="28" height="28" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
  starter: {
    name: 'Starter',
    price: '$99',
    period: '/mes',
    description: 'Para equipos pequenos que necesitan mas capacidad y soporte.',
    cta: 'Comenzar con Starter',
    ctaLink: '/register',
    highlight: false,
    icon: (
      <svg width="28" height="28" fill="none" stroke="#6366f1" viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.58-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
      </svg>
    ),
  },
  professional: {
    name: 'Profesional',
    price: '$499',
    period: '/mes',
    description: 'Para empresas con necesidades avanzadas de ML y privacidad.',
    cta: 'Elegir Profesional',
    ctaLink: '/register',
    highlight: true,
    icon: (
      <svg width="28" height="28" fill="none" stroke="#6366f1" viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
  },
  enterprise: {
    name: 'Enterprise',
    price: 'Contactar',
    period: '',
    description: 'Solucion personalizada con soporte dedicado y SLA garantizado.',
    cta: 'Contactar ventas',
    ctaLink: 'mailto:sales@xcapit.com?subject=Plan%20Enterprise',
    highlight: false,
    icon: (
      <svg width="28" height="28" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
      </svg>
    ),
  },
}

const FEATURES_TABLE = [
  { category: 'Uso general', features: [
    { name: 'Requests por dia', key: 'daily_requests' },
    { name: 'Rate limit (req/min)', key: 'rate_limit_rpm' },
    { name: 'Modelos simultaneos', key: 'max_models' },
    { name: 'Consorcios activos', key: 'max_consortiums' },
  ]},
  { category: 'Datos y entrenamiento', features: [
    { name: 'Almacenamiento de datos', key: 'max_upload_mb', format: 'mb' },
    { name: 'Entrenamientos por dia', key: 'training_runs_per_day' },
    { name: 'Sandboxes activos', key: 'max_sandboxes' },
  ]},
  { category: 'Funcionalidades', features: [
    { name: 'Encriptacion homomorfica (FHE)', key: 'fhe', type: 'bool' },
    { name: 'Aprendizaje federado', key: 'federated', type: 'bool' },
    { name: 'Dashboard en tiempo real', key: 'dashboard', type: 'bool' },
    { name: 'API REST completa', key: 'api', type: 'bool' },
    { name: 'Soporte prioritario', key: 'priority_support', type: 'bool' },
    { name: 'SLA garantizado', key: 'sla', type: 'bool' },
    { name: 'On-premise deployment', key: 'on_premise', type: 'bool' },
  ]},
]

const FEATURES_BOOLS = {
  free:         { fhe: true,  federated: false, dashboard: true,  api: true,  priority_support: false, sla: false, on_premise: false },
  starter:      { fhe: true,  federated: true,  dashboard: true,  api: true,  priority_support: false, sla: false, on_premise: false },
  professional: { fhe: true,  federated: true,  dashboard: true,  api: true,  priority_support: true,  sla: true,  on_premise: false },
  enterprise:   { fhe: true,  federated: true,  dashboard: true,  api: true,  priority_support: true,  sla: true,  on_premise: true },
}

const FAQ_ITEMS = [
  {
    q: 'Que incluye el periodo de prueba gratuito?',
    a: 'Al registrarte obtienes 14 dias con todas las funcionalidades del plan Profesional. Sin necesidad de tarjeta de credito. Al finalizar, puedes elegir un plan o continuar con el plan Gratuito.',
  },
  {
    q: 'Puedo cambiar de plan en cualquier momento?',
    a: 'Si, puedes hacer upgrade o downgrade cuando quieras. Los cambios se aplican inmediatamente y el cobro se prorratea al siguiente ciclo de facturacion.',
  },
  {
    q: 'Como funciona la encriptacion homomorfica (FHE)?',
    a: 'FHE permite realizar computaciones sobre datos encriptados sin necesidad de desencriptarlos. Esto garantiza la privacidad total de los datos durante el entrenamiento de modelos de ML colaborativo.',
  },
  {
    q: 'Que significa aprendizaje federado?',
    a: 'El aprendizaje federado permite entrenar modelos de ML de forma colaborativa entre multiples participantes sin compartir los datos crudos. Cada participante entrena localmente y solo se comparten los parametros del modelo.',
  },
  {
    q: 'Ofrecen soporte para integracion?',
    a: 'Si. Los planes Profesional y Enterprise incluyen soporte tecnico dedicado. Ademas, ofrecemos SDK en Python para facilitar la integracion con tus sistemas existentes.',
  },
  {
    q: 'Los datos estan seguros?',
    a: 'Absolutamente. Usamos encriptacion de extremo a extremo, FHE para computaciones, y nunca tenemos acceso a tus datos en texto plano. Cumplimos con GDPR, HIPAA y SOC 2.',
  },
]

const FALLBACK_PLANS = [
  { tier: 'free', name: 'Gratuito', daily_requests: 100, rate_limit_rpm: 10, max_models: 2, max_consortiums: 1, max_upload_mb: 50, training_runs_per_day: 5, max_sandboxes: 1 },
  { tier: 'starter', name: 'Starter', daily_requests: 5000, rate_limit_rpm: 60, max_models: 10, max_consortiums: 5, max_upload_mb: 500, training_runs_per_day: 50, max_sandboxes: 5 },
  { tier: 'professional', name: 'Profesional', daily_requests: 50000, rate_limit_rpm: 300, max_models: 50, max_consortiums: 25, max_upload_mb: 5000, training_runs_per_day: 200, max_sandboxes: 20 },
  { tier: 'enterprise', name: 'Enterprise', daily_requests: -1, rate_limit_rpm: -1, max_models: -1, max_consortiums: -1, max_upload_mb: -1, training_runs_per_day: -1, max_sandboxes: -1 },
]

function PlanCard({ plan, meta, isAnnual }) {
  const isHighlight = meta.highlight
  const isEnterprise = plan.tier === 'enterprise'

  return (
    <div style={{
      background: isHighlight ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : COLORS.card,
      borderRadius: 16,
      padding: isHighlight ? 3 : 0,
      flex: '1 1 240px',
      minWidth: 240,
      maxWidth: 300,
      position: 'relative',
    }}>
      {isHighlight && (
        <div style={{
          position: 'absolute',
          top: -12,
          left: '50%',
          transform: 'translateX(-50%)',
          background: COLORS.warning,
          color: '#fff',
          padding: '4px 16px',
          borderRadius: 20,
          fontSize: 12,
          fontWeight: 700,
          whiteSpace: 'nowrap',
        }}>
          Mas popular
        </div>
      )}
      <div style={{
        background: COLORS.card,
        borderRadius: isHighlight ? 14 : 16,
        border: isHighlight ? 'none' : `1px solid ${COLORS.border}`,
        padding: 28,
        height: '100%',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ marginBottom: 20 }}>
          <div style={{ marginBottom: 12 }}>{meta.icon}</div>
          <h3 style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: '0 0 4px' }}>
            {meta.name}
          </h3>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 2, marginBottom: 8 }}>
            <span style={{ fontSize: 36, fontWeight: 800, color: COLORS.text }}>
              {isEnterprise ? '' : meta.price}
            </span>
            {!isEnterprise && (
              <span style={{ fontSize: 15, color: COLORS.muted }}>{meta.period}</span>
            )}
            {isEnterprise && (
              <span style={{ fontSize: 20, fontWeight: 700, color: COLORS.text }}>Contactar</span>
            )}
          </div>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: 0, lineHeight: 1.5 }}>
            {meta.description}
          </p>
        </div>

        {/* Features list */}
        <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', flex: 1 }}>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.daily_requests === -1 ? 'Requests ilimitados' : `${plan.daily_requests.toLocaleString()} requests/dia`}</span>
          </li>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.max_consortiums === -1 ? 'Consorcios ilimitados' : `${plan.max_consortiums} consorcios`}</span>
          </li>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.max_models === -1 ? 'Modelos ilimitados' : `${plan.max_models} modelos`}</span>
          </li>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.max_upload_mb === -1 ? 'Almacenamiento ilimitado' : `${plan.max_upload_mb} MB almacenamiento`}</span>
          </li>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.training_runs_per_day === -1 ? 'Entrenamientos ilimitados' : `${plan.training_runs_per_day} entrenamientos/dia`}</span>
          </li>
          <li style={featureItemStyle}>
            <CheckIcon color={COLORS.success} />
            <span>{plan.max_sandboxes === -1 ? 'Sandboxes ilimitados' : `${plan.max_sandboxes} sandboxes`}</span>
          </li>
        </ul>

        {/* CTA */}
        {isEnterprise ? (
          <a
            href={meta.ctaLink}
            style={{
              display: 'block',
              textAlign: 'center',
              padding: '14px 0',
              borderRadius: 10,
              border: `2px solid ${COLORS.primary}`,
              background: 'transparent',
              color: COLORS.primary,
              fontWeight: 600,
              fontSize: 15,
              textDecoration: 'none',
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => { e.currentTarget.style.background = COLORS.primaryLight }}
            onMouseOut={(e) => { e.currentTarget.style.background = 'transparent' }}
          >
            {meta.cta}
          </a>
        ) : (
          <Link
            to={meta.ctaLink}
            style={{
              display: 'block',
              textAlign: 'center',
              padding: '14px 0',
              borderRadius: 10,
              border: 'none',
              background: isHighlight ? COLORS.primary : COLORS.primaryLight,
              color: isHighlight ? '#fff' : COLORS.primary,
              fontWeight: 600,
              fontSize: 15,
              textDecoration: 'none',
              transition: 'background 0.2s, transform 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = isHighlight ? COLORS.primaryHover : '#ddd6fe'
              e.currentTarget.style.transform = 'translateY(-1px)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = isHighlight ? COLORS.primary : COLORS.primaryLight
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            {meta.cta}
          </Link>
        )}
      </div>
    </div>
  )
}

function CheckIcon({ color }) {
  return (
    <svg width="18" height="18" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={2.5} style={{ flexShrink: 0 }}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  )
}

function XIcon() {
  return (
    <svg width="18" height="18" fill="none" stroke="#d1d5db" viewBox="0 0 24 24" strokeWidth={2} style={{ flexShrink: 0 }}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

const featureItemStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  fontSize: 14,
  color: '#374151',
  padding: '6px 0',
}

function FAQItem({ item, isOpen, onToggle }) {
  return (
    <div style={{
      borderBottom: `1px solid ${COLORS.border}`,
      paddingBottom: isOpen ? 16 : 0,
    }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 0',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <span style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, paddingRight: 16 }}>
          {item.q}
        </span>
        <svg
          width="20"
          height="20"
          fill="none"
          stroke={COLORS.muted}
          viewBox="0 0 24 24"
          strokeWidth={2}
          style={{
            flexShrink: 0,
            transition: 'transform 0.2s',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <p style={{
          margin: 0,
          fontSize: 15,
          color: COLORS.muted,
          lineHeight: 1.6,
          paddingBottom: 4,
        }}>
          {item.a}
        </p>
      )}
    </div>
  )
}

export default function Pricing() {
  const [plans, setPlans] = useState(FALLBACK_PLANS)
  const [loading, setLoading] = useState(true)
  const [openFaq, setOpenFaq] = useState(null)

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await getPlansComparison()
        if (data && data.length > 0) {
          setPlans(data)
        }
      } catch (err) {
        // Use fallback plans
      } finally {
        setLoading(false)
      }
    }
    fetchPlans()
  }, [])

  const formatFeatureValue = (plan, feature) => {
    if (feature.type === 'bool') {
      const bools = FEATURES_BOOLS[plan.tier] || {}
      return bools[feature.key] ? <CheckIcon color={COLORS.success} /> : <XIcon />
    }
    const value = plan[feature.key]
    if (value === undefined || value === null) return '-'
    if (value === -1) return 'Ilimitado'
    if (feature.format === 'mb') {
      return value === -1 ? 'Ilimitado' : `${value.toLocaleString()} MB`
    }
    return value.toLocaleString()
  }

  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg }}>
      {/* Navigation */}
      <nav style={{
        background: COLORS.card,
        borderBottom: `1px solid ${COLORS.border}`,
        padding: '12px 24px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}>
            <div style={{
              width: 32,
              height: 32,
              background: COLORS.primary,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <svg width="18" height="18" fill="none" stroke="#fff" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span style={{ fontSize: 20, fontWeight: 600, color: COLORS.text }}>Xcapit</span>
            <span style={{ fontSize: 20, fontWeight: 300, color: COLORS.primary }}>Privacy</span>
          </Link>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <Link to="/login" style={{ color: COLORS.muted, textDecoration: 'none', fontSize: 14, fontWeight: 500 }}>
              Iniciar sesion
            </Link>
            <Link
              to="/register"
              style={{
                background: COLORS.primary,
                color: '#fff',
                padding: '8px 20px',
                borderRadius: 8,
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        textAlign: 'center',
        padding: '64px 24px 48px',
        maxWidth: 800,
        margin: '0 auto',
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 16px',
          background: COLORS.primaryLight,
          borderRadius: 20,
          fontSize: 13,
          fontWeight: 600,
          color: COLORS.primary,
          marginBottom: 20,
        }}>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
          Planes y precios
        </div>
        <h1 style={{ fontSize: 42, fontWeight: 800, color: COLORS.text, margin: '0 0 16px', lineHeight: 1.2 }}>
          El plan perfecto para tu equipo
        </h1>
        <p style={{ fontSize: 18, color: COLORS.muted, margin: 0, lineHeight: 1.6 }}>
          Comienza gratis con 14 dias de prueba con todas las funcionalidades.
          Escala cuando estes listo.
        </p>
      </section>

      {/* Plan Cards */}
      <section style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '0 24px 64px',
      }}>
        <div style={{
          display: 'flex',
          gap: 20,
          justifyContent: 'center',
          flexWrap: 'wrap',
        }}>
          {plans.map((plan) => {
            const meta = PLAN_META[plan.tier]
            if (!meta) return null
            return (
              <PlanCard
                key={plan.tier}
                plan={plan}
                meta={meta}
              />
            )
          })}
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section style={{
        maxWidth: 1000,
        margin: '0 auto',
        padding: '0 24px 64px',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, textAlign: 'center', marginBottom: 40 }}>
          Comparacion detallada de planes
        </h2>

        <div style={{
          background: COLORS.card,
          borderRadius: 16,
          border: `1px solid ${COLORS.border}`,
          overflow: 'hidden',
        }}>
          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr repeat(4, 120px)',
            background: '#f8fafc',
            borderBottom: `1px solid ${COLORS.border}`,
            padding: '16px 24px',
            gap: 8,
          }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.muted }}>Caracteristica</div>
            {plans.map((plan) => (
              <div key={plan.tier} style={{ textAlign: 'center', fontSize: 14, fontWeight: 700, color: COLORS.text }}>
                {PLAN_META[plan.tier]?.name || plan.tier}
              </div>
            ))}
          </div>

          {/* Table body */}
          {FEATURES_TABLE.map((section) => (
            <div key={section.category}>
              {/* Section header */}
              <div style={{
                padding: '12px 24px',
                background: '#f1f5f9',
                borderBottom: `1px solid ${COLORS.border}`,
                borderTop: `1px solid ${COLORS.border}`,
              }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.text, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  {section.category}
                </span>
              </div>

              {section.features.map((feature, fIdx) => (
                <div
                  key={feature.key}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr repeat(4, 120px)',
                    padding: '12px 24px',
                    borderBottom: `1px solid ${COLORS.border}`,
                    background: fIdx % 2 === 0 ? COLORS.card : '#fafbfc',
                    gap: 8,
                    alignItems: 'center',
                  }}
                >
                  <div style={{ fontSize: 14, color: '#374151' }}>{feature.name}</div>
                  {plans.map((plan) => (
                    <div key={plan.tier} style={{ textAlign: 'center', fontSize: 14, color: COLORS.text, fontWeight: 500 }}>
                      {formatFeatureValue(plan, feature)}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section style={{
        maxWidth: 720,
        margin: '0 auto',
        padding: '0 24px 64px',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, textAlign: 'center', marginBottom: 40 }}>
          Preguntas frecuentes
        </h2>

        <div style={{
          background: COLORS.card,
          borderRadius: 16,
          border: `1px solid ${COLORS.border}`,
          padding: '0 28px',
        }}>
          {FAQ_ITEMS.map((item, idx) => (
            <FAQItem
              key={idx}
              item={item}
              isOpen={openFaq === idx}
              onToggle={() => setOpenFaq(openFaq === idx ? null : idx)}
            />
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{
        maxWidth: 800,
        margin: '0 auto',
        padding: '0 24px 80px',
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          borderRadius: 20,
          padding: '48px 40px',
          textAlign: 'center',
          color: '#fff',
        }}>
          <h2 style={{ fontSize: 30, fontWeight: 700, margin: '0 0 12px' }}>
            Listo para empezar?
          </h2>
          <p style={{ fontSize: 17, margin: '0 0 28px', opacity: 0.9, lineHeight: 1.5 }}>
            Crea tu cuenta gratuita hoy y obtiene 14 dias de prueba con todas las funcionalidades del plan Profesional.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link
              to="/register"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '14px 32px',
                background: '#fff',
                color: COLORS.primary,
                borderRadius: 10,
                fontWeight: 700,
                fontSize: 16,
                textDecoration: 'none',
                transition: 'transform 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Crear cuenta gratuita
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link
              to="/sandbox-demo"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '14px 32px',
                background: 'transparent',
                border: '2px solid rgba(255,255,255,0.5)',
                color: '#fff',
                borderRadius: 10,
                fontWeight: 600,
                fontSize: 16,
                textDecoration: 'none',
                transition: 'background 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.15)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            >
              Probar sandbox demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: `1px solid ${COLORS.border}`,
        padding: '32px 24px',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
          2026 Xcapit Privacy Platform. Todos los derechos reservados.
        </p>
      </footer>
    </div>
  )
}

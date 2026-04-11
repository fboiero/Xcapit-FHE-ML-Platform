import { useState } from 'react'

const COLORS = {
  primary: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f8fafc',
  card: '#ffffff',
  text: '#1e293b',
  muted: '#64748b',
  border: '#e5e7eb',
  accent: '#06d6a0',
  info: '#3b82f6',
  infoLight: '#eff6ff',
}

const FRAMEWORKS = [
  { id: 'gdpr', name: 'GDPR', score: 94, status: 'Cumple', lastAssessed: '2026-03-10', controls: 42, passed: 40 },
  { id: 'hipaa', name: 'HIPAA', score: 87, status: 'Parcial', lastAssessed: '2026-03-05', controls: 38, passed: 33 },
  { id: 'ccpa', name: 'CCPA', score: 91, status: 'Cumple', lastAssessed: '2026-03-12', controls: 28, passed: 26 },
  { id: 'iso27001', name: 'ISO 27001', score: 78, status: 'En progreso', lastAssessed: '2026-02-28', controls: 55, passed: 43 },
]

const FINDINGS = [
  { id: 1, title: 'Certificados TLS proximos a expirar en 30 dias', severity: 'warning', framework: 'ISO 27001', date: '2026-03-13' },
  { id: 2, title: 'Politica de retencion de datos actualizada correctamente', severity: 'info', framework: 'GDPR', date: '2026-03-12' },
  { id: 3, title: 'Falta consentimiento explicito en formulario de registro', severity: 'critical', framework: 'GDPR', date: '2026-03-11' },
  { id: 4, title: 'Logs de acceso habilitados en todos los endpoints', severity: 'info', framework: 'HIPAA', date: '2026-03-10' },
  { id: 5, title: 'Encriptacion en reposo no verificada en backup secundario', severity: 'critical', framework: 'HIPAA', date: '2026-03-09' },
  { id: 6, title: 'Respuesta a solicitud de eliminacion excede plazo de 30 dias', severity: 'warning', framework: 'CCPA', date: '2026-03-08' },
]

const CONTROLS = [
  { name: 'Encriptacion de datos en transito', status: 'pass', framework: 'Todos' },
  { name: 'Encriptacion de datos en reposo', status: 'pass', framework: 'HIPAA' },
  { name: 'Autenticacion multifactor (MFA)', status: 'pass', framework: 'ISO 27001' },
  { name: 'Registro de consentimiento del usuario', status: 'fail', framework: 'GDPR' },
  { name: 'Derecho al olvido implementado', status: 'pass', framework: 'GDPR' },
  { name: 'Plan de respuesta a incidentes', status: 'pass', framework: 'ISO 27001' },
  { name: 'Evaluacion de impacto de privacidad (DPIA)', status: 'pass', framework: 'GDPR' },
  { name: 'Backup y recuperacion automatizados', status: 'fail', framework: 'ISO 27001' },
  { name: 'Notificacion de brechas en 72h', status: 'pass', framework: 'GDPR' },
  { name: 'Acceso basado en roles (RBAC)', status: 'pass', framework: 'Todos' },
]

const SEVERITY_STYLES = {
  info: { bg: '#eff6ff', color: '#3b82f6', label: 'Info' },
  warning: { bg: COLORS.warningLight, color: COLORS.warning, label: 'Advertencia' },
  critical: { bg: COLORS.dangerLight, color: COLORS.danger, label: 'Critico' },
}

function ScoreCircle({ score, size = 80 }) {
  const radius = (size - 10) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 90 ? COLORS.success : score >= 75 ? COLORS.warning : COLORS.danger

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={COLORS.border} strokeWidth={5} />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color}
          strokeWidth={5} strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: size * 0.25, fontWeight: 700, color }}>{score}%</span>
      </div>
    </div>
  )
}

export default function Compliance() {
  const [selectedFramework, setSelectedFramework] = useState(null)

  const overallScore = Math.round(FRAMEWORKS.reduce((s, f) => s + f.score, 0) / FRAMEWORKS.length)

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Cumplimiento Regulatorio
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Monitorea el estado de cumplimiento y hallazgos de auditoria
        </p>
      </div>

      {/* Overall score + Framework cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 24, marginBottom: 28 }}>
        {/* Overall */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 12px', fontWeight: 600 }}>Puntuacion global</p>
          <ScoreCircle score={overallScore} size={100} />
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '12px 0 0' }}>
            {FRAMEWORKS.filter(f => f.status === 'Cumple').length}/{FRAMEWORKS.length} frameworks
          </p>
        </div>

        {/* Framework cards grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          {FRAMEWORKS.map((fw) => {
            const statusColor = fw.status === 'Cumple' ? COLORS.success : fw.status === 'Parcial' ? COLORS.warning : COLORS.primary
            const statusBg = fw.status === 'Cumple' ? COLORS.successLight : fw.status === 'Parcial' ? COLORS.warningLight : COLORS.primaryLight
            return (
              <div
                key={fw.id}
                onClick={() => setSelectedFramework(selectedFramework === fw.id ? null : fw.id)}
                style={{
                  background: selectedFramework === fw.id ? COLORS.primaryLight : COLORS.card,
                  borderRadius: 12, border: `1px solid ${selectedFramework === fw.id ? COLORS.primary : COLORS.border}`,
                  padding: 20, cursor: 'pointer', transition: 'border-color 0.2s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.text, margin: 0 }}>{fw.name}</h3>
                  <span style={{
                    padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: statusBg, color: statusColor,
                  }}>
                    {fw.status}
                  </span>
                </div>
                <ScoreCircle score={fw.score} size={64} />
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '10px 0 0' }}>
                  Evaluado: {new Date(fw.lastAssessed).toLocaleDateString('es-AR')}
                </p>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '2px 0 0' }}>
                  Controles: {fw.passed}/{fw.controls} aprobados
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Two-column layout: Findings + Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Recent findings */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Hallazgos recientes
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {FINDINGS.map((finding) => {
              const sevStyle = SEVERITY_STYLES[finding.severity]
              return (
                <div key={finding.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: '12px 0', borderBottom: `1px solid ${COLORS.border}`,
                }}>
                  <span style={{
                    padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: sevStyle.bg, color: sevStyle.color, whiteSpace: 'nowrap', marginTop: 2,
                  }}>
                    {sevStyle.label}
                  </span>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 14, color: COLORS.text, margin: '0 0 4px', lineHeight: 1.4 }}>
                      {finding.title}
                    </p>
                    <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>
                      {finding.framework} - {new Date(finding.date).toLocaleDateString('es-AR')}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Controls checklist */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Controles de seguridad
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {CONTROLS.map((control, idx) => (
              <div key={idx} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 0', borderBottom: `1px solid ${COLORS.border}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 22, height: 22, borderRadius: 6,
                    background: control.status === 'pass' ? COLORS.successLight : COLORS.dangerLight,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontWeight: 700,
                    color: control.status === 'pass' ? COLORS.success : COLORS.danger,
                  }}>
                    {control.status === 'pass' ? '\u2713' : '\u2717'}
                  </div>
                  <span style={{ fontSize: 14, color: COLORS.text }}>{control.name}</span>
                </div>
                <span style={{ fontSize: 12, color: COLORS.muted }}>{control.framework}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: COLORS.muted }}>
              {CONTROLS.filter(c => c.status === 'pass').length}/{CONTROLS.length} controles aprobados
            </span>
            <span style={{
              fontSize: 13, fontWeight: 600,
              color: CONTROLS.filter(c => c.status === 'fail').length > 0 ? COLORS.warning : COLORS.success,
            }}>
              {CONTROLS.filter(c => c.status === 'fail').length} pendientes
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

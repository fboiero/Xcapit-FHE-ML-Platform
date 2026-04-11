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
}

const REPORT_TYPES = [
  { id: 'rendimiento', label: 'Rendimiento', color: COLORS.primary },
  { id: 'compliance', label: 'Compliance', color: '#a855f7' },
  { id: 'uso', label: 'Uso', color: COLORS.accent },
  { id: 'seguridad', label: 'Seguridad', color: COLORS.danger },
  { id: 'custom', label: 'Custom', color: COLORS.warning },
]

const SECTIONS_BY_TYPE = {
  rendimiento: [
    { id: 'r1', label: 'Metricas de precision (R\u00B2, MAE, RMSE)' },
    { id: 'r2', label: 'Historial de entrenamiento' },
    { id: 'r3', label: 'Comparacion de modelos' },
    { id: 'r4', label: 'Importancia de features' },
    { id: 'r5', label: 'Predicciones vs valores reales' },
  ],
  compliance: [
    { id: 'c1', label: 'Cumplimiento HIPAA/GDPR' },
    { id: 'c2', label: 'Registros de auditoria' },
    { id: 'c3', label: 'Politicas de privacidad' },
    { id: 'c4', label: 'Niveles de encriptacion' },
    { id: 'c5', label: 'Accesos y permisos' },
  ],
  uso: [
    { id: 'u1', label: 'Usuarios activos por periodo' },
    { id: 'u2', label: 'Consumo de recursos FHE' },
    { id: 'u3', label: 'Entrenamientos ejecutados' },
    { id: 'u4', label: 'Datos procesados (volumen)' },
    { id: 'u5', label: 'API calls por endpoint' },
  ],
  seguridad: [
    { id: 's1', label: 'Intentos de acceso no autorizado' },
    { id: 's2', label: 'Vulnerabilidades detectadas' },
    { id: 's3', label: 'Estado de certificados' },
    { id: 's4', label: 'Configuracion de FHE' },
    { id: 's5', label: 'Logs de seguridad' },
  ],
  custom: [
    { id: 'x1', label: 'Resumen ejecutivo' },
    { id: 'x2', label: 'Metricas seleccionadas' },
    { id: 'x3', label: 'Graficos personalizados' },
    { id: 'x4', label: 'Recomendaciones' },
    { id: 'x5', label: 'Apendice tecnico' },
  ],
}

const CONSORTIUMS = [
  { id: 'all', name: 'Todos los consorcios' },
  { id: 'salud', name: 'Consorcio Salud Argentina' },
  { id: 'finanzas', name: 'Consorcio FinTech Latam' },
  { id: 'seguros', name: 'Consorcio Seguros Unidos' },
]

const RECENT_REPORTS = [
  { id: 1, name: 'Rendimiento Q1 2026', type: 'rendimiento', date: '2026-03-10', size: '2.4 MB', status: 'listo' },
  { id: 2, name: 'Compliance HIPAA Marzo', type: 'compliance', date: '2026-03-08', size: '1.8 MB', status: 'listo' },
  { id: 3, name: 'Uso Mensual Feb 2026', type: 'uso', date: '2026-03-01', size: '3.1 MB', status: 'listo' },
  { id: 4, name: 'Auditoria Seguridad', type: 'seguridad', date: '2026-02-28', size: '4.2 MB', status: 'listo' },
  { id: 5, name: 'Reporte Personalizado', type: 'custom', date: '2026-02-20', size: '1.5 MB', status: 'expirado' },
]

export default function ReportBuilder() {
  const [selectedType, setSelectedType] = useState('rendimiento')
  const [dateStart, setDateStart] = useState('2026-03-01')
  const [dateEnd, setDateEnd] = useState('2026-03-14')
  const [consortium, setConsortium] = useState('all')
  const [checkedSections, setCheckedSections] = useState({})
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)

  const sections = SECTIONS_BY_TYPE[selectedType] || []
  const selectedSections = sections.filter(s => checkedSections[s.id] !== false)
  const typeInfo = REPORT_TYPES.find(t => t.id === selectedType)

  const toggleSection = (id) => {
    setCheckedSections(prev => ({ ...prev, [id]: prev[id] === false ? true : false }))
  }

  const handleGenerate = () => {
    setGenerating(true)
    setGenerated(false)
    setTimeout(() => {
      setGenerating(false)
      setGenerated(true)
    }, 2000)
  }

  const handleTypeChange = (typeId) => {
    setSelectedType(typeId)
    setCheckedSections({})
    setGenerated(false)
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Generador de Reportes
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Crea reportes personalizados de rendimiento, compliance y uso
        </p>
      </div>

      {/* Report type selector */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
        {REPORT_TYPES.map(t => (
          <button
            key={t.id}
            onClick={() => handleTypeChange(t.id)}
            style={{
              padding: '10px 20px', borderRadius: 8, border: 'none',
              background: selectedType === t.id ? t.color : COLORS.bg,
              color: selectedType === t.id ? '#fff' : COLORS.text,
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 20 }}>
        {/* Configuration panel */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Configuracion
          </h3>

          {/* Date range */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, color: COLORS.muted, display: 'block', marginBottom: 8 }}>
              Rango de fechas
            </label>
            <div style={{ display: 'flex', gap: 12 }}>
              <input
                type="date"
                value={dateStart}
                onChange={e => setDateStart(e.target.value)}
                style={{
                  flex: 1, padding: '10px 12px', borderRadius: 8,
                  border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                  outline: 'none',
                }}
              />
              <input
                type="date"
                value={dateEnd}
                onChange={e => setDateEnd(e.target.value)}
                style={{
                  flex: 1, padding: '10px 12px', borderRadius: 8,
                  border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                  outline: 'none',
                }}
              />
            </div>
          </div>

          {/* Consortium selector */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, color: COLORS.muted, display: 'block', marginBottom: 8 }}>
              Consorcio
            </label>
            <select
              value={consortium}
              onChange={e => setConsortium(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8,
                border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                outline: 'none', background: COLORS.card,
              }}
            >
              {CONSORTIUMS.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          {/* Sections checklist */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, color: COLORS.muted, display: 'block', marginBottom: 8 }}>
              Secciones a incluir
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {sections.map(s => {
                const checked = checkedSections[s.id] !== false
                return (
                  <label
                    key={s.id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                      padding: '8px 12px', borderRadius: 8, background: checked ? COLORS.primaryLight : COLORS.bg,
                      transition: 'background 0.2s',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleSection(s.id)}
                      style={{ accentColor: COLORS.primary }}
                    />
                    <span style={{ fontSize: 14, color: COLORS.text }}>{s.label}</span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={generating || selectedSections.length === 0}
            style={{
              width: '100%', padding: '12px 20px', borderRadius: 8, border: 'none',
              background: generating || selectedSections.length === 0 ? COLORS.border : COLORS.primary,
              color: '#fff', fontSize: 14, fontWeight: 600,
              cursor: generating || selectedSections.length === 0 ? 'not-allowed' : 'pointer',
            }}
          >
            {generating ? 'Generando reporte...' : 'Generar Reporte'}
          </button>
        </div>

        {/* Preview panel */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Vista previa del reporte
          </h3>

          {/* Report outline */}
          <div style={{
            background: COLORS.bg, borderRadius: 8, padding: 20, marginBottom: 20,
            border: `1px dashed ${COLORS.border}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <span style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: typeInfo.color + '20', color: typeInfo.color,
              }}>
                {typeInfo.label}
              </span>
              <span style={{ fontSize: 12, color: COLORS.muted }}>
                {dateStart} a {dateEnd}
              </span>
            </div>
            <h4 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 4px' }}>
              Reporte de {typeInfo.label}
            </h4>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 16px' }}>
              {CONSORTIUMS.find(c => c.id === consortium)?.name}
            </p>

            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px', textTransform: 'uppercase' }}>
              Contenido ({selectedSections.length} secciones)
            </p>
            {selectedSections.map((s, idx) => (
              <div key={s.id} style={{
                padding: '8px 0', borderBottom: idx < selectedSections.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{ fontSize: 13, color: COLORS.primary, fontWeight: 600, minWidth: 20 }}>{idx + 1}.</span>
                <span style={{ fontSize: 14, color: COLORS.text }}>{s.label}</span>
              </div>
            ))}
          </div>

          {/* Generated report card */}
          {generated && (
            <div style={{
              background: COLORS.successLight, borderRadius: 8, padding: 20,
              border: `1px solid ${COLORS.success}40`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <span style={{ fontSize: 16, color: COLORS.success }}>{'\u2713'}</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.success }}>Reporte generado exitosamente</span>
              </div>
              <p style={{ fontSize: 13, color: COLORS.text, margin: '0 0 12px' }}>
                Reporte de {typeInfo.label} - {new Date().toLocaleDateString('es-AR')} - 2.1 MB
              </p>
              <button style={{
                padding: '8px 16px', borderRadius: 6, border: 'none',
                background: COLORS.success, color: '#fff', fontSize: 13,
                fontWeight: 600, cursor: 'pointer',
              }}>
                Descargar PDF
              </button>
            </div>
          )}

          {generating && (
            <div style={{
              background: COLORS.warningLight, borderRadius: 8, padding: 20,
              border: `1px solid ${COLORS.warning}40`, textAlign: 'center',
            }}>
              <p style={{ fontSize: 14, color: COLORS.warning, fontWeight: 600, margin: '0 0 8px' }}>
                Generando reporte...
              </p>
              <div style={{
                width: '100%', height: 6, background: COLORS.border, borderRadius: 3, overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', background: COLORS.warning, borderRadius: 3,
                  width: '60%', animation: 'none',
                }} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent reports */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginTop: 24,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Reportes Recientes
        </h3>

        {/* Table header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 80px 100px',
          gap: 12, padding: '10px 16px', background: COLORS.bg, borderRadius: 8,
          fontSize: 12, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
          marginBottom: 4,
        }}>
          <span>Nombre</span>
          <span>Tipo</span>
          <span>Fecha</span>
          <span>Tamano</span>
          <span>Estado</span>
        </div>

        {RECENT_REPORTS.map(report => {
          const rType = REPORT_TYPES.find(t => t.id === report.type)
          return (
            <div key={report.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 80px 100px',
              gap: 12, padding: '14px 16px', alignItems: 'center',
              borderBottom: `1px solid ${COLORS.border}`,
            }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{report.name}</span>
              <span style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: rType.color + '20', color: rType.color,
                display: 'inline-block', width: 'fit-content',
              }}>
                {rType.label}
              </span>
              <span style={{ fontSize: 14, color: COLORS.muted }}>{report.date}</span>
              <span style={{ fontSize: 14, color: COLORS.muted }}>{report.size}</span>
              <span style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: report.status === 'listo' ? COLORS.successLight : COLORS.warningLight,
                color: report.status === 'listo' ? COLORS.success : COLORS.warning,
                display: 'inline-block', width: 'fit-content',
              }}>
                {report.status === 'listo' ? 'Listo' : 'Expirado'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

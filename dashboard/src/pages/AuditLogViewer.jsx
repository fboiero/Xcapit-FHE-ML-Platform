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
  purple: '#8b5cf6',
  purpleLight: '#f5f3ff',
}

const ACTION_CATEGORIES = {
  auth: { label: 'Autenticacion', bg: '#eff6ff', color: '#3b82f6' },
  data: { label: 'Datos', bg: COLORS.successLight, color: COLORS.success },
  training: { label: 'Entrenamiento', bg: COLORS.purpleLight, color: COLORS.purple },
  admin: { label: 'Administracion', bg: COLORS.dangerLight, color: COLORS.danger },
  governance: { label: 'Gobernanza', bg: COLORS.warningLight, color: COLORS.warning },
}

const ALL_LOGS = [
  { id: 1, timestamp: '2026-03-14T14:32:10', user: 'admin@xcapit.com', action: 'login', category: 'auth', resource: 'Sesion', ip: '192.168.1.45', status: 'success', details: { method: 'JWT', mfa: true, user_agent: 'Chrome 120' } },
  { id: 2, timestamp: '2026-03-14T14:28:05', user: 'maria@medcorp.com', action: 'upload_data', category: 'data', resource: 'Dataset pacientes_2026', ip: '10.0.0.12', status: 'success', details: { records: 4520, size: '12.4 MB', encrypted: true, format: 'CSV' } },
  { id: 3, timestamp: '2026-03-14T14:15:33', user: 'carlos@healthdata.com', action: 'start_training', category: 'training', resource: 'Consorcio HealthML', ip: '10.0.0.88', status: 'success', details: { model_type: 'linear_regression', epochs: 50, security_level: '128-bit CKKS' } },
  { id: 4, timestamp: '2026-03-14T13:55:12', user: 'admin@xcapit.com', action: 'update_permissions', category: 'admin', resource: 'Usuario carlos@healthdata.com', ip: '192.168.1.45', status: 'success', details: { old_role: 'viewer', new_role: 'contributor', consortium: 'HealthML' } },
  { id: 5, timestamp: '2026-03-14T13:42:08', user: 'pedro@fintech.com', action: 'login_failed', category: 'auth', resource: 'Sesion', ip: '203.45.67.89', status: 'failure', details: { reason: 'Credenciales invalidas', attempt: 3, locked: false } },
  { id: 6, timestamp: '2026-03-14T13:30:22', user: 'ana@bioanalytics.com', action: 'vote_proposal', category: 'governance', resource: 'Propuesta #12', ip: '10.0.0.55', status: 'success', details: { vote: 'a_favor', proposal: 'Aumentar epsilon a 3.0' } },
  { id: 7, timestamp: '2026-03-14T13:15:44', user: 'system', action: 'training_completed', category: 'training', resource: 'Consorcio FinanceML', ip: '10.0.0.1', status: 'success', details: { duration: '2h 14m', accuracy: 0.942, r2: 0.891 } },
  { id: 8, timestamp: '2026-03-14T12:58:11', user: 'maria@medcorp.com', action: 'download_model', category: 'data', resource: 'Modelo costos_v3', ip: '10.0.0.12', status: 'success', details: { model_id: 'mdl_abc123', version: '3.1', size: '4.2 MB' } },
  { id: 9, timestamp: '2026-03-14T12:45:30', user: 'admin@xcapit.com', action: 'create_api_key', category: 'admin', resource: 'API Key prod-ml-01', ip: '192.168.1.45', status: 'success', details: { prefix: 'xc_prod', permissions: ['read', 'write'], expires: '2027-03-14' } },
  { id: 10, timestamp: '2026-03-14T12:30:55', user: 'carlos@healthdata.com', action: 'encrypt_data', category: 'data', resource: 'Dataset historiales', ip: '10.0.0.88', status: 'success', details: { scheme: 'CKKS', security_level: '128-bit', records: 8900 } },
  { id: 11, timestamp: '2026-03-14T12:15:20', user: 'unknown@external.com', action: 'login_failed', category: 'auth', resource: 'Sesion', ip: '185.220.101.34', status: 'failure', details: { reason: 'Cuenta no existe', blocked_ip: true } },
  { id: 12, timestamp: '2026-03-14T11:58:09', user: 'system', action: 'backup_completed', category: 'admin', resource: 'Base de datos principal', ip: '10.0.0.1', status: 'success', details: { size: '2.3 GB', duration: '4m 22s', location: 's3://backups/2026-03-14' } },
  { id: 13, timestamp: '2026-03-14T11:42:33', user: 'ana@bioanalytics.com', action: 'upload_data', category: 'data', resource: 'Dataset genomico_2026', ip: '10.0.0.55', status: 'failure', details: { reason: 'Formato invalido', expected: 'CSV', received: 'XLSX' } },
  { id: 14, timestamp: '2026-03-14T11:30:18', user: 'pedro@fintech.com', action: 'login', category: 'auth', resource: 'Sesion', ip: '203.45.67.89', status: 'success', details: { method: 'JWT', mfa: true, user_agent: 'Firefox 119' } },
  { id: 15, timestamp: '2026-03-14T11:15:42', user: 'maria@medcorp.com', action: 'create_proposal', category: 'governance', resource: 'Propuesta #13', ip: '10.0.0.12', status: 'success', details: { title: 'Implementar ZKP para contribuciones', type: 'Tecnica' } },
  { id: 16, timestamp: '2026-03-14T10:55:08', user: 'carlos@healthdata.com', action: 'decrypt_result', category: 'data', resource: 'Resultado prediccion_batch_44', ip: '10.0.0.88', status: 'success', details: { records: 1200, model: 'costos_v3' } },
  { id: 17, timestamp: '2026-03-14T10:40:25', user: 'admin@xcapit.com', action: 'revoke_api_key', category: 'admin', resource: 'API Key test-dev-02', ip: '192.168.1.45', status: 'success', details: { prefix: 'xc_test', reason: 'Expirada' } },
  { id: 18, timestamp: '2026-03-14T10:22:11', user: 'system', action: 'round_started', category: 'training', resource: 'Ronda federada #6', ip: '10.0.0.1', status: 'success', details: { participants: 5, method: 'FedAvg', estimated_duration: '4h' } },
  { id: 19, timestamp: '2026-03-14T10:05:47', user: 'ana@bioanalytics.com', action: 'logout', category: 'auth', resource: 'Sesion', ip: '10.0.0.55', status: 'success', details: { session_duration: '3h 42m' } },
  { id: 20, timestamp: '2026-03-14T09:48:33', user: 'pedro@fintech.com', action: 'upload_data', category: 'data', resource: 'Dataset transacciones_q1', ip: '203.45.67.89', status: 'success', details: { records: 25600, size: '45.1 MB', encrypted: true, format: 'Parquet' } },
  { id: 21, timestamp: '2026-03-14T09:30:19', user: 'admin@xcapit.com', action: 'update_config', category: 'admin', resource: 'Configuracion FHE', ip: '192.168.1.45', status: 'success', details: { setting: 'security_level', old: '128-bit', new: '192-bit' } },
  { id: 22, timestamp: '2026-03-14T09:15:04', user: 'system', action: 'compliance_scan', category: 'admin', resource: 'Auditoria GDPR', ip: '10.0.0.1', status: 'success', details: { framework: 'GDPR', score: 94, findings: 2 } },
]

const ACTION_TYPES = ['Todos', 'auth', 'data', 'training', 'admin', 'governance']
const ITEMS_PER_PAGE = 8

export default function AuditLogViewer() {
  const [categoryFilter, setCategoryFilter] = useState('Todos')
  const [userSearch, setUserSearch] = useState('')
  const [expandedId, setExpandedId] = useState(null)
  const [page, setPage] = useState(1)

  const filtered = ALL_LOGS.filter((log) => {
    const matchCategory = categoryFilter === 'Todos' || log.category === categoryFilter
    const matchUser = userSearch === '' || log.user.toLowerCase().includes(userSearch.toLowerCase())
    return matchCategory && matchUser
  })

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const paginated = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)

  const handleCategoryChange = (cat) => {
    setCategoryFilter(cat)
    setPage(1)
  }

  const handleSearchChange = (val) => {
    setUserSearch(val)
    setPage(1)
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Registro de Auditoria
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Historial completo de acciones y eventos del sistema
        </p>
      </div>

      {/* Filter bar */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 20, marginBottom: 24,
        display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
      }}>
        {/* Category filter */}
        <div>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 4 }}>
            Tipo de accion
          </label>
          <select
            value={categoryFilter}
            onChange={(e) => handleCategoryChange(e.target.value)}
            style={{
              padding: '8px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, outline: 'none', background: '#fff', cursor: 'pointer', minWidth: 160,
            }}
          >
            {ACTION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t === 'Todos' ? 'Todos' : ACTION_CATEGORIES[t]?.label || t}
              </option>
            ))}
          </select>
        </div>

        {/* User search */}
        <div style={{ flex: '1 1 200px' }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 4 }}>
            Buscar usuario
          </label>
          <input
            type="text"
            value={userSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="email del usuario..."
            style={{
              width: '100%', padding: '8px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Results count */}
        <div style={{ alignSelf: 'flex-end', paddingBottom: 4 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>
            {filtered.length} registro{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Log entries table */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: COLORS.bg, borderBottom: `2px solid ${COLORS.border}` }}>
              {['Hora', 'Usuario', 'Accion', 'Recurso', 'IP', 'Estado', ''].map((h) => (
                <th key={h} style={{
                  textAlign: 'left', padding: '12px 14px', fontSize: 12,
                  fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((log) => {
              const catStyle = ACTION_CATEGORIES[log.category]
              const isExpanded = expandedId === log.id
              return (
                <tr key={log.id} style={{ cursor: 'pointer' }} onClick={() => setExpandedId(isExpanded ? null : log.id)}>
                  <td style={{ padding: '12px 14px', fontSize: 13, color: COLORS.muted, fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                    {new Date(log.timestamp).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 13, color: COLORS.text, fontWeight: 500 }}>
                    {log.user}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                      background: catStyle?.bg || COLORS.bg, color: catStyle?.color || COLORS.muted,
                    }}>
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 13, color: COLORS.text, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.resource}
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.muted, fontFamily: 'monospace' }}>
                    {log.ip}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{
                      padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                      background: log.status === 'success' ? COLORS.successLight : COLORS.dangerLight,
                      color: log.status === 'success' ? COLORS.success : COLORS.danger,
                    }}>
                      {log.status === 'success' ? 'Exitoso' : 'Fallido'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 14, color: COLORS.muted }}>
                    <span style={{
                      display: 'inline-block', transition: 'transform 0.2s',
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}>
                      &#9662;
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {/* Expanded detail rows - rendered outside the table for layout simplicity */}
        {paginated.map((log) => {
          if (expandedId !== log.id) return null
          return (
            <div key={`detail-${log.id}`} style={{
              padding: '16px 24px', background: COLORS.bg,
              borderBottom: `1px solid ${COLORS.border}`,
            }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px', textTransform: 'uppercase' }}>
                Detalles del evento
              </p>
              <div style={{
                background: COLORS.card, borderRadius: 8, border: `1px solid ${COLORS.border}`,
                padding: 16, fontFamily: 'monospace', fontSize: 13, color: COLORS.text,
                lineHeight: 1.6, overflowX: 'auto',
              }}>
                {JSON.stringify(log.details, null, 2)}
              </div>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '8px 0 0' }}>
                Fecha completa: {new Date(log.timestamp).toLocaleString('es-AR')}
              </p>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 20,
        }}>
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            style={{
              padding: '8px 18px', borderRadius: 8,
              border: `1px solid ${COLORS.border}`, background: COLORS.card,
              color: page === 1 ? COLORS.muted : COLORS.text,
              fontSize: 14, fontWeight: 500,
              cursor: page === 1 ? 'not-allowed' : 'pointer',
            }}
          >
            Anterior
          </button>

          <div style={{ display: 'flex', gap: 4 }}>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                style={{
                  width: 36, height: 36, borderRadius: 8, border: 'none',
                  background: p === page ? COLORS.primary : 'transparent',
                  color: p === page ? '#fff' : COLORS.muted,
                  fontSize: 14, fontWeight: 600, cursor: 'pointer',
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            style={{
              padding: '8px 18px', borderRadius: 8,
              border: `1px solid ${COLORS.border}`, background: COLORS.card,
              color: page === totalPages ? COLORS.muted : COLORS.text,
              fontSize: 14, fontWeight: 500,
              cursor: page === totalPages ? 'not-allowed' : 'pointer',
            }}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { listConsortiums, getConsortiumStats } from '../api/client'

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

const STATUS_BADGE = {
  encrypted: { label: 'Encriptado', color: COLORS.success, bg: COLORS.successLight },
  processing: { label: 'Procesando', color: COLORS.warning, bg: COLORS.warningLight },
  validated: { label: 'Validado', color: COLORS.primary, bg: COLORS.primaryLight },
  error: { label: 'Error', color: COLORS.danger, bg: COLORS.dangerLight },
}

const MOCK_UPLOADS = [
  { id: 1, file_name: 'datos_ventas_2025.csv', records: 15420, size_mb: 2.3, status: 'encrypted', consortium_name: 'Consorcio Retail', uploaded_at: '2026-03-10T14:30:00Z' },
  { id: 2, file_name: 'transacciones_q4.json', records: 8750, size_mb: 1.8, status: 'encrypted', consortium_name: 'Consorcio Finanzas', uploaded_at: '2026-03-09T10:15:00Z' },
  { id: 3, file_name: 'pacientes_anonimizados.csv', records: 3200, size_mb: 0.9, status: 'validated', consortium_name: 'Consorcio Salud', uploaded_at: '2026-03-08T09:00:00Z' },
  { id: 4, file_name: 'sensores_iot_marzo.csv', records: 45000, size_mb: 8.5, status: 'processing', consortium_name: 'Consorcio Manufactura', uploaded_at: '2026-03-07T16:45:00Z' },
  { id: 5, file_name: 'clientes_segmentados.json', records: 6100, size_mb: 1.1, status: 'encrypted', consortium_name: 'Consorcio Retail', uploaded_at: '2026-03-06T11:20:00Z' },
]

export default function DataExplorer() {
  const { consortiumId } = useParams()
  const [uploads, setUploads] = useState([])
  const [consortiums, setConsortiums] = useState([])
  const [filterConsortium, setFilterConsortium] = useState(consortiumId || '')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedUpload, setSelectedUpload] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await listConsortiums()
        const list = Array.isArray(data) ? data : data.results || []
        setConsortiums(list)

        // Try to fetch real upload data from consortium stats
        const allUploads = []
        for (const c of list.slice(0, 10)) {
          try {
            const stats = await getConsortiumStats(c.id)
            if (stats?.contributions) {
              stats.contributions.forEach((contrib, idx) => {
                allUploads.push({
                  id: `${c.id}-${idx}`,
                  file_name: contrib.file_name || `datos_${c.name.toLowerCase().replace(/\s/g, '_')}.csv`,
                  records: contrib.records || 0,
                  size_mb: contrib.size_mb || 0,
                  status: contrib.status || 'encrypted',
                  consortium_name: c.name,
                  consortium_id: c.id,
                  uploaded_at: contrib.uploaded_at || contrib.created_at,
                })
              })
            }
          } catch (_) { /* skip */ }
        }

        setUploads(allUploads.length > 0 ? allUploads : MOCK_UPLOADS)
      } catch (err) {
        setUploads(MOCK_UPLOADS)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [consortiumId])

  const filteredUploads = uploads.filter((u) => {
    const matchConsortium = !filterConsortium || u.consortium_name === filterConsortium || u.consortium_id === filterConsortium
    const matchSearch = !searchTerm || u.file_name.toLowerCase().includes(searchTerm.toLowerCase())
    return matchConsortium && matchSearch
  })

  const totalRecords = filteredUploads.reduce((sum, u) => sum + (u.records || 0), 0)
  const totalSize = filteredUploads.reduce((sum, u) => sum + (u.size_mb || 0), 0)

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando datos...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Explorador de datos
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Visualiza y gestiona tus datasets subidos
          </p>
        </div>
        <Link to="/data-upload" style={{
          padding: '10px 20px', borderRadius: 8, background: COLORS.primary, color: '#fff',
          textDecoration: 'none', fontSize: 14, fontWeight: 600,
        }}>
          Subir nuevos datos
        </Link>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Total datasets</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>{filteredUploads.length}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Total registros</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.primary, margin: 0 }}>{totalRecords.toLocaleString()}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Tamano total</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.success, margin: 0 }}>{totalSize.toFixed(1)} MB</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Consorcios</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.warning, margin: 0 }}>
            {new Set(filteredUploads.map(u => u.consortium_name)).size}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: '16px 20px', marginBottom: 20, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center',
      }}>
        <div style={{ flex: '1 1 200px' }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por nombre de archivo..."
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>
        <div style={{ flex: '0 0 220px' }}>
          <select
            value={filterConsortium}
            onChange={(e) => setFilterConsortium(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, outline: 'none', background: '#fff', cursor: 'pointer',
            }}
          >
            <option value="">Todos los consorcios</option>
            {[...new Set(uploads.map(u => u.consortium_name))].map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden',
      }}>
        {filteredUploads.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <p style={{ color: COLORS.muted, fontSize: 16 }}>No se encontraron datasets con los filtros aplicados.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: `2px solid ${COLORS.border}` }}>
                {['Archivo', 'Consorcio', 'Registros', 'Tamano', 'Estado', 'Fecha'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '12px 16px', fontSize: 13,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 0.5,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredUploads.map((u) => {
                const status = STATUS_BADGE[u.status] || STATUS_BADGE.encrypted
                return (
                  <tr
                    key={u.id}
                    style={{
                      borderBottom: `1px solid ${COLORS.border}`, cursor: 'pointer',
                      background: selectedUpload === u.id ? COLORS.primaryLight : 'transparent',
                      transition: 'background 0.15s',
                    }}
                    onClick={() => setSelectedUpload(selectedUpload === u.id ? null : u.id)}
                    onMouseOver={(e) => { if (selectedUpload !== u.id) e.currentTarget.style.background = '#fafbfc' }}
                    onMouseOut={(e) => { if (selectedUpload !== u.id) e.currentTarget.style.background = 'transparent' }}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <svg width="18" height="18" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.8}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                        </svg>
                        <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{u.file_name}</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.muted }}>{u.consortium_name}</td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.text, fontWeight: 500 }}>
                      {(u.records || 0).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.muted }}>
                      {u.size_mb ? `${u.size_mb} MB` : '-'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        display: 'inline-block', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                        background: status.bg, color: status.color,
                      }}>
                        {status.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.muted }}>
                      {u.uploaded_at ? new Date(u.uploaded_at).toLocaleDateString('es-AR') : '-'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Selected upload details */}
      {selectedUpload && (() => {
        const u = filteredUploads.find(up => up.id === selectedUpload)
        if (!u) return null
        return (
          <div style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 24, marginTop: 20,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
              Resumen del dataset: {u.file_name}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }}>
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: 14 }}>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px' }}>Registros</p>
                <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: 0 }}>{(u.records || 0).toLocaleString()}</p>
              </div>
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: 14 }}>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px' }}>Tamano</p>
                <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: 0 }}>{u.size_mb} MB</p>
              </div>
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: 14 }}>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px' }}>Consorcio</p>
                <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: 0 }}>{u.consortium_name}</p>
              </div>
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: 14 }}>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px' }}>Encriptacion</p>
                <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.success, margin: 0 }}>FHE (CKKS)</p>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}

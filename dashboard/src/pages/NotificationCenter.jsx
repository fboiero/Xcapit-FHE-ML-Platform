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

const INITIAL_NOTIFICATIONS = [
  { id: 1, type: 'training', title: 'Entrenamiento completado', desc: 'Modelo Riesgo Salud v2 finalizo con R²=0.94', time: 'Hace 5 min', read: false },
  { id: 2, type: 'security', title: 'Alerta de seguridad', desc: '3 intentos de acceso fallidos desde IP 192.168.1.45', time: 'Hace 12 min', read: false },
  { id: 3, type: 'system', title: 'Actualizacion del sistema', desc: 'Plataforma actualizada a v2.4.1 — mejoras de rendimiento FHE', time: 'Hace 30 min', read: false },
  { id: 4, type: 'training', title: 'Nuevo modelo disponible', desc: 'Modelo Consorcio Fraude v1.3.2 listo para despliegue', time: 'Hace 1 hora', read: false },
  { id: 5, type: 'system', title: 'Nuevo miembro unido', desc: 'FinTech Solutions se unio al consorcio HealthData', time: 'Hace 2 horas', read: true },
  { id: 6, type: 'security', title: 'Certificado SSL renovado', desc: 'Certificado TLS del endpoint api.xcapit.io renovado exitosamente', time: 'Hace 3 horas', read: true },
  { id: 7, type: 'training', title: 'Entrenamiento iniciado', desc: 'Pipeline de reentrenamiento semanal del modelo Churn iniciado', time: 'Hace 4 horas', read: true },
  { id: 8, type: 'system', title: 'Backup completado', desc: 'Backup diario de base de datos completado (2.3 GB)', time: 'Hace 5 horas', read: true },
  { id: 9, type: 'security', title: 'Clave API revocada', desc: 'La API Key con prefijo xcp_3f2a fue revocada por expiracion', time: 'Hace 6 horas', read: true },
  { id: 10, type: 'training', title: 'Alerta de presupuesto', desc: 'Presupuesto de privacidad epsilon al 85% del limite configurado', time: 'Hace 8 horas', read: false },
  { id: 11, type: 'system', title: 'Mantenimiento programado', desc: 'Ventana de mantenimiento el 16/03 de 02:00 a 04:00 UTC', time: 'Hace 10 horas', read: true },
  { id: 12, type: 'training', title: 'Datos validados', desc: 'Dataset healthcare_v3.csv paso todas las verificaciones de calidad', time: 'Hace 12 horas', read: true },
  { id: 13, type: 'security', title: 'Auditoria completada', desc: 'Auditoria de seguridad trimestral completada sin hallazgos criticos', time: 'Hace 1 dia', read: true },
  { id: 14, type: 'system', title: 'Almacenamiento al 80%', desc: 'El almacenamiento del tier actual esta al 80% de capacidad', time: 'Hace 1 dia', read: false },
  { id: 15, type: 'training', title: 'Modelo deprecado', desc: 'Modelo Local A v0.8 marcado como deprecado — migrar a v2', time: 'Hace 2 dias', read: true },
  { id: 16, type: 'security', title: 'Nuevo dispositivo detectado', desc: 'Inicio de sesion desde un nuevo dispositivo (MacBook Pro, Buenos Aires)', time: 'Hace 2 dias', read: true },
]

const TABS = [
  { key: 'all', label: 'Todas' },
  { key: 'unread', label: 'Sin leer' },
  { key: 'system', label: 'Sistema' },
  { key: 'training', label: 'Training' },
  { key: 'security', label: 'Seguridad' },
]

const TYPE_ICONS = {
  training: { path: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0', color: '#8b5cf6', bg: '#f5f3ff' },
  security: { path: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z', color: COLORS.danger, bg: COLORS.dangerLight },
  system: { path: 'M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93s.844.136 1.175-.108l.712-.57a1.148 1.148 0 011.52.13l.773.774c.39.389.44 1.002.13 1.452l-.57.713c-.244.33-.27.78-.108 1.175s.506.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.424.07-.764.384-.93.78s-.136.844.108 1.175l.57.712a1.148 1.148 0 01-.13 1.52l-.773.773a1.148 1.148 0 01-1.452.13l-.713-.57c-.33-.244-.78-.27-1.175-.108s-.71.506-.78.93l-.15.893c-.09.543-.56.94-1.109.94h-1.094c-.55 0-1.02-.397-1.11-.94l-.148-.893a1.354 1.354 0 00-.78-.93 1.354 1.354 0 00-1.176.108l-.712.57a1.148 1.148 0 01-1.52-.13l-.774-.773a1.148 1.148 0 01-.13-1.452', color: COLORS.primary, bg: COLORS.primaryLight },
}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS)
  const [activeTab, setActiveTab] = useState('all')

  const unreadCount = notifications.filter(n => !n.read).length

  const markAsRead = (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const filtered = notifications.filter(n => {
    if (activeTab === 'unread') return !n.read
    if (activeTab === 'all') return true
    return n.type === activeTab
  })

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>
            Centro de Notificaciones
          </h1>
          {unreadCount > 0 && (
            <span style={{
              padding: '4px 10px', borderRadius: 12, background: COLORS.danger, color: '#fff',
              fontSize: 12, fontWeight: 700,
            }}>
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllAsRead} style={{
            padding: '8px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            background: '#fff', color: COLORS.text, fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>
            Marcar todas como leidas
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: `2px solid ${COLORS.border}` }}>
        {TABS.map(tab => {
          const count = tab.key === 'all' ? notifications.length
            : tab.key === 'unread' ? unreadCount
            : notifications.filter(n => n.type === tab.key).length
          return (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
              padding: '10px 18px', border: 'none', background: 'none', fontSize: 13,
              fontWeight: 600, cursor: 'pointer',
              color: activeTab === tab.key ? COLORS.primary : COLORS.muted,
              borderBottom: activeTab === tab.key ? `2px solid ${COLORS.primary}` : '2px solid transparent',
              marginBottom: -2, display: 'flex', alignItems: 'center', gap: 6,
            }}>
              {tab.label}
              <span style={{
                padding: '1px 7px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                background: activeTab === tab.key ? COLORS.primaryLight : COLORS.bg,
                color: activeTab === tab.key ? COLORS.primary : COLORS.muted,
              }}>{count}</span>
            </button>
          )
        })}
      </div>

      {/* Notification list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px', color: COLORS.muted }}>
            <p style={{ fontSize: 15, margin: 0 }}>No hay notificaciones en esta categoria</p>
          </div>
        ) : (
          filtered.map(notif => {
            const typeInfo = TYPE_ICONS[notif.type]
            return (
              <div key={notif.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: 14, padding: '16px 20px',
                background: notif.read ? COLORS.card : COLORS.primaryLight + '44',
                borderBottom: `1px solid ${COLORS.border}`, borderRadius: 0,
                transition: 'background 0.2s',
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8, background: typeInfo.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2,
                }}>
                  <svg width="18" height="18" fill="none" stroke={typeInfo.color} viewBox="0 0 24 24" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={typeInfo.path} />
                  </svg>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                    <h4 style={{ fontSize: 14, fontWeight: notif.read ? 500 : 700, color: COLORS.text, margin: 0 }}>
                      {notif.title}
                    </h4>
                    {!notif.read && (
                      <div style={{ width: 7, height: 7, borderRadius: '50%', background: COLORS.primary, flexShrink: 0 }} />
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: COLORS.muted, margin: '2px 0 0', lineHeight: 1.5 }}>{notif.desc}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                  <span style={{ fontSize: 12, color: COLORS.muted, whiteSpace: 'nowrap' }}>{notif.time}</span>
                  {!notif.read && (
                    <button onClick={() => markAsRead(notif.id)} style={{
                      padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.border}`,
                      background: '#fff', color: COLORS.muted, fontSize: 11, fontWeight: 600,
                      cursor: 'pointer', whiteSpace: 'nowrap',
                    }}>
                      Marcar leida
                    </button>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

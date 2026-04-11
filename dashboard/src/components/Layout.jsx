import { useState, useEffect, useCallback } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { clearApiKey, isDemoMode } from '../api/client'
import { getTrialStatus } from '../api/trial'

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
  sidebarBg: '#1e1b4b',
  sidebarText: '#c7d2fe',
  sidebarActive: '#6366f1',
  sidebarHover: '#312e81',
}

const SIDEBAR_WIDTH = 240
const SIDEBAR_COLLAPSED_WIDTH = 64

// SVG Icons as inline components
const icons = {
  dashboard: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  ),
  trial: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  consortium: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772" />
    </svg>
  ),
  sandbox: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
    </svg>
  ),
  training: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
    </svg>
  ),
  upload: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  ),
  governance: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  ),
  compliance: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375" />
    </svg>
  ),
  monitoring: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ),
  billing: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
    </svg>
  ),
  settings: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  team: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  logout: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
    </svg>
  ),
  menu: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  ),
  pricing: (color) => (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
    </svg>
  ),
}

const NAV_SECTIONS = [
  {
    title: 'Principal',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
      { path: '/trial', label: 'Prueba', icon: 'trial', trialBadge: true },
    ],
  },
  {
    title: 'Consorcios',
    items: [
      { path: '/consortiums/new', label: 'Crear consorcio', icon: 'consortium' },
      { path: '/governance', label: 'Gobernanza', icon: 'governance' },
      { path: '/compliance', label: 'Cumplimiento', icon: 'compliance' },
    ],
  },
  {
    title: 'Datos y Modelos',
    items: [
      { path: '/data-upload', label: 'Subir datos', icon: 'upload' },
      { path: '/training', label: 'Entrenamiento', icon: 'training' },
      { path: '/sandbox', label: 'Sandbox', icon: 'sandbox' },
      { path: '/monitoring', label: 'Monitoreo', icon: 'monitoring' },
    ],
  },
  {
    title: 'Administracion',
    items: [
      { path: '/team', label: 'Equipo', icon: 'team' },
      { path: '/billing', label: 'Facturacion', icon: 'billing' },
      { path: '/settings', label: 'Configuracion', icon: 'settings' },
    ],
  },
]

function TrialHeaderBadge({ trialStatus }) {
  if (!trialStatus || !trialStatus.is_trial || trialStatus.trial_expired) return null

  const daysLeft = trialStatus.trial_days_remaining || 0
  const isUrgent = daysLeft <= 3

  return (
    <Link
      to="/trial"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 14px',
        borderRadius: 20,
        background: isUrgent
          ? 'linear-gradient(135deg, #ef4444, #f97316)'
          : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        color: '#fff',
        fontSize: 13,
        fontWeight: 600,
        textDecoration: 'none',
        transition: 'transform 0.2s, box-shadow 0.2s',
        boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.transform = 'translateY(-1px)'
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(99,102,241,0.4)'
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(99,102,241,0.3)'
      }}
    >
      <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {daysLeft} {daysLeft === 1 ? 'dia' : 'dias'} restantes
    </Link>
  )
}

function SidebarNavItem({ item, isActive, collapsed, trialStatus }) {
  const iconFn = icons[item.icon]
  const color = isActive ? '#fff' : COLORS.sidebarText
  const showTrialDot = item.trialBadge && trialStatus?.is_trial && !trialStatus?.trial_expired

  return (
    <Link
      to={item.path}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: collapsed ? 0 : 12,
        padding: collapsed ? '10px 0' : '10px 16px',
        borderRadius: 8,
        background: isActive ? COLORS.sidebarActive : 'transparent',
        color,
        textDecoration: 'none',
        fontSize: 14,
        fontWeight: isActive ? 600 : 400,
        transition: 'background 0.15s',
        justifyContent: collapsed ? 'center' : 'flex-start',
        position: 'relative',
      }}
      onMouseOver={(e) => { if (!isActive) e.currentTarget.style.background = COLORS.sidebarHover }}
      onMouseOut={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
      title={collapsed ? item.label : ''}
    >
      {iconFn && iconFn(color)}
      {!collapsed && <span>{item.label}</span>}
      {showTrialDot && (
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: COLORS.success,
          marginLeft: collapsed ? 0 : 'auto',
          position: collapsed ? 'absolute' : 'static',
          top: collapsed ? 6 : undefined,
          right: collapsed ? 6 : undefined,
          boxShadow: `0 0 6px ${COLORS.success}`,
        }} />
      )}
    </Link>
  )
}

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [trialStatus, setTrialStatus] = useState(null)

  useEffect(() => {
    const fetchTrialStatus = async () => {
      try {
        const data = await getTrialStatus()
        setTrialStatus(data)
      } catch (err) {
        // Non-critical, don't block layout
      }
    }
    fetchTrialStatus()
  }, [location.pathname])

  const handleLogout = () => {
    clearApiKey()
    navigate('/login')
  }

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH
  const isDemo = isDemoMode()

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: COLORS.bg }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarWidth,
        background: COLORS.sidebarBg,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: 40,
        overflowX: 'hidden',
        overflowY: 'auto',
      }}>
        {/* Logo */}
        <div style={{
          padding: collapsed ? '20px 8px' : '20px 20px',
          borderBottom: '1px solid #312e81',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          flexShrink: 0,
        }}>
          <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}>
            <div style={{
              width: 32,
              height: 32,
              background: COLORS.primary,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <svg width="18" height="18" fill="none" stroke="#fff" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            {!collapsed && (
              <span style={{ fontSize: 18, fontWeight: 600, color: '#fff', whiteSpace: 'nowrap' }}>
                Xcapit
              </span>
            )}
          </Link>
          {!collapsed && (
            <button
              onClick={() => setCollapsed(true)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 4,
                borderRadius: 4,
              }}
            >
              <svg width="18" height="18" fill="none" stroke={COLORS.sidebarText} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
              </svg>
            </button>
          )}
        </div>

        {collapsed && (
          <div style={{ padding: '12px 0', textAlign: 'center', borderBottom: '1px solid #312e81' }}>
            <button
              onClick={() => setCollapsed(false)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 6,
                borderRadius: 4,
              }}
            >
              <svg width="18" height="18" fill="none" stroke={COLORS.sidebarText} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 4.5l7.5 7.5-7.5 7.5m-6-15l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav style={{ flex: 1, padding: collapsed ? '12px 8px' : '12px 12px', overflowY: 'auto' }}>
          {NAV_SECTIONS.map((section) => (
            <div key={section.title} style={{ marginBottom: 20 }}>
              {!collapsed && (
                <p style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#818cf8',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                  margin: '0 0 6px 4px',
                }}>
                  {section.title}
                </p>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {section.items.map((item) => (
                  <SidebarNavItem
                    key={item.path}
                    item={item}
                    isActive={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
                    collapsed={collapsed}
                    trialStatus={trialStatus}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div style={{
          padding: collapsed ? '12px 8px' : '12px 12px',
          borderTop: '1px solid #312e81',
          flexShrink: 0,
        }}>
          {/* Pricing link */}
          <Link
            to="/pricing"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: collapsed ? 0 : 12,
              padding: collapsed ? '10px 0' : '10px 16px',
              borderRadius: 8,
              background: 'transparent',
              color: COLORS.sidebarText,
              textDecoration: 'none',
              fontSize: 14,
              justifyContent: collapsed ? 'center' : 'flex-start',
              marginBottom: 4,
              transition: 'background 0.15s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = COLORS.sidebarHover}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            title={collapsed ? 'Planes y precios' : ''}
          >
            {icons.pricing(COLORS.sidebarText)}
            {!collapsed && <span>Planes y precios</span>}
          </Link>

          {/* Logout */}
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: collapsed ? 0 : 12,
              padding: collapsed ? '10px 0' : '10px 16px',
              borderRadius: 8,
              background: 'transparent',
              border: 'none',
              color: COLORS.sidebarText,
              fontSize: 14,
              cursor: 'pointer',
              width: '100%',
              justifyContent: collapsed ? 'center' : 'flex-start',
              transition: 'background 0.15s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = COLORS.sidebarHover}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            title={collapsed ? 'Cerrar sesion' : ''}
          >
            {icons.logout(COLORS.sidebarText)}
            {!collapsed && <span>Cerrar sesion</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div style={{
        flex: 1,
        marginLeft: sidebarWidth,
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        transition: 'margin-left 0.2s ease',
      }}>
        {/* Top header bar */}
        <header style={{
          background: COLORS.card,
          borderBottom: `1px solid ${COLORS.border}`,
          padding: '0 24px',
          height: 56,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 30,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {isDemo && (
              <span style={{
                padding: '4px 12px',
                borderRadius: 6,
                background: COLORS.warningLight,
                color: '#92400e',
                fontSize: 12,
                fontWeight: 600,
              }}>
                MODO DEMO
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <TrialHeaderBadge trialStatus={trialStatus} />

            {/* Notifications icon */}
            <Link
              to="/notifications"
              style={{
                width: 36,
                height: 36,
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                textDecoration: 'none',
                transition: 'background 0.15s',
              }}
              onMouseOver={(e) => e.currentTarget.style.background = COLORS.bg}
              onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <svg width="20" height="20" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
            </Link>

            {/* User avatar */}
            <Link
              to="/settings"
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: COLORS.primary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                textDecoration: 'none',
                color: '#fff',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              U
            </Link>
          </div>
        </header>

        {/* Trial expired banner across top */}
        {trialStatus?.trial_expired && (
          <div style={{
            background: 'linear-gradient(90deg, #ef4444, #f97316)',
            padding: '10px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
          }}>
            <span style={{ color: '#fff', fontSize: 14, fontWeight: 500 }}>
              Tu periodo de prueba ha expirado. Hace upgrade para continuar sin limitaciones.
            </span>
            <Link
              to="/trial"
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                background: '#fff',
                color: COLORS.danger,
                fontSize: 13,
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              Hacer upgrade
            </Link>
          </div>
        )}

        {/* Page content */}
        <main style={{ flex: 1, padding: 0 }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
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
  borderFocus: '#6366f1',
}

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
}

const labelStyle = {
  display: 'block',
  fontSize: 14,
  fontWeight: 500,
  color: '#374151',
  marginBottom: 6,
}

export default function UserSettings() {
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('profile')

  // Profile form
  const [companyName, setCompanyName] = useState('')
  const [email, setEmail] = useState('')
  const [profileMsg, setProfileMsg] = useState('')
  const [profileSaving, setProfileSaving] = useState(false)

  // Password form
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordMsg, setPasswordMsg] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)

  // API Keys
  const [apiKeys, setApiKeys] = useState([])
  const [newKeyName, setNewKeyName] = useState('')
  const [creatingKey, setCreatingKey] = useState(false)
  const [newKeyResult, setNewKeyResult] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getCurrentCompany()
        setCompany(data)
        setCompanyName(data.name || '')
        setEmail(data.email || '')
        setApiKeys(data.api_keys || [
          { id: 1, prefix: 'xcp_...a3f2', name: 'Clave principal', created_at: '2026-02-15T10:00:00Z', last_used: '2026-03-13T08:30:00Z' },
        ])
      } catch (err) {
        // fallback
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setProfileSaving(true)
    setProfileMsg('')
    try {
      // Simulate API call
      await new Promise(r => setTimeout(r, 800))
      setProfileMsg('Perfil actualizado correctamente.')
    } catch (err) {
      setProfileMsg(`Error: ${err.message}`)
    } finally {
      setProfileSaving(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    if (newPassword.length < 12) {
      setPasswordMsg('Error: La contrasena debe tener al menos 12 caracteres.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg('Error: Las contrasenas no coinciden.')
      return
    }
    setPasswordSaving(true)
    setPasswordMsg('')
    try {
      await new Promise(r => setTimeout(r, 800))
      setPasswordMsg('Contrasena actualizada correctamente.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordMsg(`Error: ${err.message}`)
    } finally {
      setPasswordSaving(false)
    }
  }

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) return
    setCreatingKey(true)
    try {
      await new Promise(r => setTimeout(r, 600))
      const mockKey = `xcp_${Math.random().toString(36).slice(2, 10)}_${Math.random().toString(36).slice(2, 14)}`
      setNewKeyResult(mockKey)
      setApiKeys((prev) => [
        ...prev,
        { id: Date.now(), prefix: `xcp_...${mockKey.slice(-4)}`, name: newKeyName, created_at: new Date().toISOString(), last_used: null },
      ])
      setNewKeyName('')
    } catch (err) {
      // handle error
    } finally {
      setCreatingKey(false)
    }
  }

  const handleRevokeKey = (keyId) => {
    setApiKeys((prev) => prev.filter(k => k.id !== keyId))
  }

  const tabs = [
    { key: 'profile', label: 'Perfil' },
    { key: 'password', label: 'Contrasena' },
    { key: 'apikeys', label: 'API Keys' },
    { key: 'account', label: 'Cuenta' },
  ]

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando configuracion...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
        Configuracion
      </h1>
      <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 32px' }}>
        Gestiona tu perfil, seguridad y API Keys
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: `2px solid ${COLORS.border}` }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '12px 24px', border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500,
              background: 'transparent',
              color: activeTab === tab.key ? COLORS.primary : COLORS.muted,
              borderBottom: activeTab === tab.key ? `2px solid ${COLORS.primary}` : '2px solid transparent',
              marginBottom: -2, transition: 'color 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile tab */}
      {activeTab === 'profile' && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Informacion del perfil
          </h2>
          {profileMsg && (
            <div style={{
              background: profileMsg.startsWith('Error') ? COLORS.dangerLight : COLORS.successLight,
              color: profileMsg.startsWith('Error') ? COLORS.danger : COLORS.success,
              padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
            }}>
              {profileMsg}
            </div>
          )}
          <form onSubmit={handleSaveProfile}>
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Nombre de la empresa</label>
              <input type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)}
                style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>
            <button type="submit" disabled={profileSaving} style={{
              padding: '12px 24px', borderRadius: 10, border: 'none',
              background: profileSaving ? '#a5b4fc' : COLORS.primary,
              color: '#fff', fontSize: 15, fontWeight: 600,
              cursor: profileSaving ? 'not-allowed' : 'pointer',
            }}>
              {profileSaving ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </form>
        </div>
      )}

      {/* Password tab */}
      {activeTab === 'password' && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Cambiar contrasena
          </h2>
          {passwordMsg && (
            <div style={{
              background: passwordMsg.startsWith('Error') ? COLORS.dangerLight : COLORS.successLight,
              color: passwordMsg.startsWith('Error') ? COLORS.danger : COLORS.success,
              padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
            }}>
              {passwordMsg}
            </div>
          )}
          <form onSubmit={handleChangePassword}>
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Contrasena actual</label>
              <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)}
                required style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Nueva contrasena</label>
              <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                required minLength={12} style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
              <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>Minimo 12 caracteres.</p>
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>Confirmar nueva contrasena</label>
              <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                required style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>
            <button type="submit" disabled={passwordSaving} style={{
              padding: '12px 24px', borderRadius: 10, border: 'none',
              background: passwordSaving ? '#a5b4fc' : COLORS.primary,
              color: '#fff', fontSize: 15, fontWeight: 600,
              cursor: passwordSaving ? 'not-allowed' : 'pointer',
            }}>
              {passwordSaving ? 'Actualizando...' : 'Cambiar contrasena'}
            </button>
          </form>
        </div>
      )}

      {/* API Keys tab */}
      {activeTab === 'apikeys' && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            API Keys
          </h2>

          {newKeyResult && (
            <div style={{
              background: COLORS.warningLight, borderRadius: 10, padding: 16, marginBottom: 20,
              border: `1px solid #fde68a`,
            }}>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#92400e', margin: '0 0 6px' }}>
                Nueva API Key creada. Copiala ahora, no se mostrara de nuevo.
              </p>
              <code style={{ fontSize: 13, fontFamily: 'monospace', color: COLORS.text, wordBreak: 'break-all' }}>
                {newKeyResult}
              </code>
              <button
                onClick={() => { navigator.clipboard?.writeText(newKeyResult); setNewKeyResult(null) }}
                style={{
                  display: 'block', marginTop: 8, padding: '6px 14px', borderRadius: 6,
                  border: `1px solid ${COLORS.border}`, background: '#fff', cursor: 'pointer',
                  fontSize: 13, color: COLORS.text,
                }}
              >
                Copiar y cerrar
              </button>
            </div>
          )}

          {/* Create new key */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Nombre de la nueva clave (ej: Produccion)"
              style={{ ...inputStyle, flex: '1 1 200px' }}
              onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            />
            <button
              onClick={handleCreateApiKey}
              disabled={creatingKey || !newKeyName.trim()}
              style={{
                padding: '12px 20px', borderRadius: 10, border: 'none',
                background: (creatingKey || !newKeyName.trim()) ? '#a5b4fc' : COLORS.primary,
                color: '#fff', fontSize: 14, fontWeight: 600,
                cursor: (creatingKey || !newKeyName.trim()) ? 'not-allowed' : 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {creatingKey ? 'Creando...' : 'Crear API Key'}
            </button>
          </div>

          {/* Keys list */}
          {apiKeys.length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '16px 0' }}>
              No hay API keys creadas.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {apiKeys.map((key) => (
                <div key={key.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 0', borderBottom: `1px solid ${COLORS.border}`,
                  flexWrap: 'wrap', gap: 8,
                }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>
                      {key.name || 'Sin nombre'}
                    </div>
                    <div style={{ fontSize: 13, color: COLORS.muted, fontFamily: 'monospace' }}>
                      {key.prefix || 'xcp_...'}
                    </div>
                    <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>
                      Creada: {key.created_at ? new Date(key.created_at).toLocaleDateString('es-AR') : '-'}
                      {key.last_used && ` | Ultimo uso: ${new Date(key.last_used).toLocaleDateString('es-AR')}`}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRevokeKey(key.id)}
                    style={{
                      padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.danger}`,
                      background: 'transparent', color: COLORS.danger, fontSize: 13, fontWeight: 500,
                      cursor: 'pointer', transition: 'background 0.2s',
                    }}
                    onMouseOver={(e) => { e.target.style.background = COLORS.dangerLight }}
                    onMouseOut={(e) => { e.target.style.background = 'transparent' }}
                  >
                    Revocar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Account tab */}
      {activeTab === 'account' && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Informacion de la cuenta
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: `1px solid ${COLORS.border}` }}>
              <span style={{ fontSize: 14, color: COLORS.muted }}>Empresa</span>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{company?.name || companyName || '-'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: `1px solid ${COLORS.border}` }}>
              <span style={{ fontSize: 14, color: COLORS.muted }}>Email</span>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{company?.email || email || '-'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: `1px solid ${COLORS.border}` }}>
              <span style={{ fontSize: 14, color: COLORS.muted }}>Plan actual</span>
              <span style={{
                fontSize: 14, fontWeight: 600, color: COLORS.primary,
                padding: '2px 10px', background: COLORS.primaryLight, borderRadius: 6,
              }}>
                {company?.plan || company?.tier || 'Gratuito'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: `1px solid ${COLORS.border}` }}>
              <span style={{ fontSize: 14, color: COLORS.muted }}>Cuenta creada</span>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>
                {company?.created_at ? new Date(company.created_at).toLocaleDateString('es-AR') : '-'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0' }}>
              <span style={{ fontSize: 14, color: COLORS.muted }}>ID de empresa</span>
              <span style={{ fontSize: 14, fontFamily: 'monospace', color: COLORS.muted }}>
                {company?.id || '-'}
              </span>
            </div>
          </div>

          {/* Danger zone */}
          <div style={{
            marginTop: 32, padding: 20, borderRadius: 10, border: `1px solid #fecaca`,
            background: COLORS.dangerLight,
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.danger, margin: '0 0 8px' }}>
              Zona peligrosa
            </h3>
            <p style={{ fontSize: 14, color: '#991b1b', margin: '0 0 12px' }}>
              Eliminar tu cuenta es permanente. Se borraran todos tus datos, consorcios y modelos.
            </p>
            <button style={{
              padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.danger}`,
              background: 'transparent', color: COLORS.danger, fontSize: 14, fontWeight: 600,
              cursor: 'pointer',
            }}>
              Eliminar cuenta
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

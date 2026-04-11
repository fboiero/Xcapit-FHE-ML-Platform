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

const ROLE_LABELS = {
  owner: { label: 'Propietario', color: COLORS.primary, bg: COLORS.primaryLight },
  admin: { label: 'Administrador', color: COLORS.warning, bg: COLORS.warningLight },
  member: { label: 'Miembro', color: COLORS.muted, bg: '#f3f4f6' },
  viewer: { label: 'Observador', color: COLORS.muted, bg: '#f3f4f6' },
}

const MOCK_MEMBERS = [
  { id: 1, name: 'Carlos Lopez', email: 'carlos@empresa.com', role: 'owner', joined_at: '2026-01-15T10:00:00Z', last_active: '2026-03-13T09:30:00Z' },
  { id: 2, name: 'Maria Garcia', email: 'maria@empresa.com', role: 'admin', joined_at: '2026-02-01T14:00:00Z', last_active: '2026-03-12T16:45:00Z' },
  { id: 3, name: 'Juan Perez', email: 'juan@empresa.com', role: 'member', joined_at: '2026-02-15T09:00:00Z', last_active: '2026-03-11T11:20:00Z' },
  { id: 4, name: 'Ana Martinez', email: 'ana@empresa.com', role: 'member', joined_at: '2026-03-01T08:30:00Z', last_active: '2026-03-10T14:00:00Z' },
]

export default function TeamManagement() {
  const [company, setCompany] = useState(null)
  const [members, setMembers] = useState(MOCK_MEMBERS)
  const [loading, setLoading] = useState(true)
  const [showInvite, setShowInvite] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [inviting, setInviting] = useState(false)
  const [message, setMessage] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [editingRole, setEditingRole] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getCurrentCompany()
        setCompany(data)
        if (data.members && data.members.length > 0) {
          setMembers(data.members)
        }
      } catch (_) {
        // use mock data
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleInvite = async (e) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setInviting(true)
    setMessage('')

    try {
      await new Promise(r => setTimeout(r, 600))
      const newMember = {
        id: Date.now(),
        name: inviteEmail.split('@')[0],
        email: inviteEmail,
        role: inviteRole,
        joined_at: new Date().toISOString(),
        last_active: null,
        pending: true,
      }
      setMembers((prev) => [...prev, newMember])
      setMessage(`Invitacion enviada a ${inviteEmail}`)
      setInviteEmail('')
      setShowInvite(false)
    } catch (err) {
      setMessage(`Error: ${err.message}`)
    } finally {
      setInviting(false)
    }
  }

  const handleRoleChange = (memberId, newRole) => {
    setMembers((prev) =>
      prev.map(m => m.id === memberId ? { ...m, role: newRole } : m)
    )
    setEditingRole(null)
    setMessage('Rol actualizado correctamente.')
  }

  const handleRemoveMember = (memberId) => {
    setMembers((prev) => prev.filter(m => m.id !== memberId))
    setMessage('Miembro eliminado del equipo.')
  }

  const filteredMembers = members.filter(m =>
    !searchTerm ||
    (m.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (m.email || '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando equipo...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Gestion de equipo
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            {company?.name ? `Equipo de ${company.name}` : 'Administra los miembros de tu empresa'}
          </p>
        </div>
        <button
          onClick={() => setShowInvite(!showInvite)}
          style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: COLORS.primary, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}
        >
          Invitar miembro
        </button>
      </div>

      {message && (
        <div style={{
          background: message.startsWith('Error') ? COLORS.dangerLight : COLORS.successLight,
          color: message.startsWith('Error') ? COLORS.danger : COLORS.success,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
          border: `1px solid ${message.startsWith('Error') ? '#fecaca' : '#bbf7d0'}`,
        }}>
          {message}
        </div>
      )}

      {/* Invite form */}
      {showInvite && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Invitar nuevo miembro
          </h2>
          <form onSubmit={handleInvite} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1 1 240px' }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: COLORS.muted, marginBottom: 4 }}>
                Email
              </label>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="email@empresa.com"
                required
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                  fontSize: 14, outline: 'none', boxSizing: 'border-box',
                }}
                onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
                onBlur={(e) => e.target.style.borderColor = COLORS.border}
              />
            </div>
            <div style={{ flex: '0 0 180px' }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: COLORS.muted, marginBottom: 4 }}>
                Rol
              </label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                  fontSize: 14, outline: 'none', background: '#fff', cursor: 'pointer',
                }}
              >
                <option value="admin">Administrador</option>
                <option value="member">Miembro</option>
                <option value="viewer">Observador</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={inviting} style={{
                padding: '10px 20px', borderRadius: 8, border: 'none', background: COLORS.primary,
                color: '#fff', fontSize: 14, fontWeight: 600, cursor: inviting ? 'not-allowed' : 'pointer',
              }}>
                {inviting ? 'Enviando...' : 'Enviar invitacion'}
              </button>
              <button type="button" onClick={() => setShowInvite(false)} style={{
                padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                background: COLORS.card, color: COLORS.text, fontSize: 14, cursor: 'pointer',
              }}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Total miembros</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>{members.length}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Administradores</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.warning, margin: 0 }}>
            {members.filter(m => m.role === 'admin' || m.role === 'owner').length}
          </p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Pendientes</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.primary, margin: 0 }}>
            {members.filter(m => m.pending).length}
          </p>
        </div>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar por nombre o email..."
          style={{
            width: '100%', maxWidth: 400, padding: '10px 14px', borderRadius: 8,
            border: `1px solid ${COLORS.border}`, fontSize: 14, outline: 'none', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Members list */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden',
      }}>
        {filteredMembers.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <p style={{ color: COLORS.muted, fontSize: 16 }}>No se encontraron miembros.</p>
          </div>
        ) : (
          <div>
            {filteredMembers.map((member, idx) => {
              const roleInfo = ROLE_LABELS[member.role] || ROLE_LABELS.member
              return (
                <div key={member.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '16px 24px', borderBottom: idx < filteredMembers.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                  flexWrap: 'wrap', gap: 12,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 42, height: 42, borderRadius: '50%', background: COLORS.primaryLight,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 16, fontWeight: 600, color: COLORS.primary, flexShrink: 0,
                    }}>
                      {(member.name || member.email || 'U')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 15, fontWeight: 500, color: COLORS.text }}>
                          {member.name || member.email}
                        </span>
                        {member.pending && (
                          <span style={{
                            padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                            background: COLORS.warningLight, color: COLORS.warning,
                          }}>
                            Pendiente
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 13, color: COLORS.muted }}>{member.email}</div>
                      {member.last_active && (
                        <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>
                          Ultimo acceso: {new Date(member.last_active).toLocaleDateString('es-AR')}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {editingRole === member.id ? (
                      <select
                        value={member.role}
                        onChange={(e) => handleRoleChange(member.id, e.target.value)}
                        onBlur={() => setEditingRole(null)}
                        autoFocus
                        style={{
                          padding: '6px 12px', borderRadius: 6, border: `1px solid ${COLORS.primary}`,
                          fontSize: 13, outline: 'none', background: '#fff', cursor: 'pointer',
                        }}
                      >
                        <option value="admin">Administrador</option>
                        <option value="member">Miembro</option>
                        <option value="viewer">Observador</option>
                      </select>
                    ) : (
                      <button
                        onClick={() => member.role !== 'owner' && setEditingRole(member.id)}
                        style={{
                          padding: '4px 12px', borderRadius: 6, border: 'none',
                          background: roleInfo.bg, color: roleInfo.color,
                          fontSize: 13, fontWeight: 600, cursor: member.role === 'owner' ? 'default' : 'pointer',
                        }}
                      >
                        {roleInfo.label}
                      </button>
                    )}

                    {member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        style={{
                          padding: '6px 12px', borderRadius: 6, border: `1px solid ${COLORS.border}`,
                          background: 'transparent', color: COLORS.danger, fontSize: 13, cursor: 'pointer',
                          transition: 'background 0.2s',
                        }}
                        onMouseOver={(e) => e.target.style.background = COLORS.dangerLight}
                        onMouseOut={(e) => e.target.style.background = 'transparent'}
                      >
                        Eliminar
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

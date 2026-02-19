import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'

// Simulated team data
const generateTeamMembers = () => [
  { id: '1', name: 'John Smith', email: 'john.smith@company.com', role: 'admin', status: 'active', avatar: 'JS', lastActive: '2024-01-15T10:30:00Z', joinedAt: '2023-06-01T00:00:00Z' },
  { id: '2', name: 'Sarah Johnson', email: 'sarah.j@company.com', role: 'developer', status: 'active', avatar: 'SJ', lastActive: '2024-01-15T09:15:00Z', joinedAt: '2023-08-15T00:00:00Z' },
  { id: '3', name: 'Michael Chen', email: 'michael.c@company.com', role: 'analyst', status: 'active', avatar: 'MC', lastActive: '2024-01-14T18:45:00Z', joinedAt: '2023-09-20T00:00:00Z' },
  { id: '4', name: 'Emily Davis', email: 'emily.d@company.com', role: 'viewer', status: 'pending', avatar: 'ED', lastActive: null, joinedAt: null },
  { id: '5', name: 'Robert Wilson', email: 'robert.w@company.com', role: 'developer', status: 'inactive', avatar: 'RW', lastActive: '2024-01-01T12:00:00Z', joinedAt: '2023-07-10T00:00:00Z' },
]

const roles = [
  { id: 'admin', name: 'Admin', description: 'Full access to all features', permissions: ['read', 'write', 'delete', 'manage_team', 'billing'] },
  { id: 'developer', name: 'Developer', description: 'Create and manage models', permissions: ['read', 'write', 'delete'] },
  { id: 'analyst', name: 'Analyst', description: 'View and analyze data', permissions: ['read', 'write'] },
  { id: 'viewer', name: 'Viewer', description: 'Read-only access', permissions: ['read'] },
]

export default function TeamManagement() {
  const { t } = useTranslation()
  const { consortiumId } = useParams()

  const [members, setMembers] = useState([])
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedMember, setSelectedMember] = useState(null)
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'viewer' })
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    setMembers(generateTeamMembers())
  }, [])

  const handleInvite = () => {
    const newMember = {
      id: `${Date.now()}`,
      name: inviteForm.email.split('@')[0].replace('.', ' '),
      email: inviteForm.email,
      role: inviteForm.role,
      status: 'pending',
      avatar: inviteForm.email.substring(0, 2).toUpperCase(),
      lastActive: null,
      joinedAt: null,
    }
    setMembers([...members, newMember])
    setShowInviteModal(false)
    setInviteForm({ email: '', role: 'viewer' })
  }

  const handleUpdateRole = (memberId, newRole) => {
    setMembers(members.map(m =>
      m.id === memberId ? { ...m, role: newRole } : m
    ))
  }

  const handleRemoveMember = (memberId) => {
    if (confirm('Are you sure you want to remove this team member?')) {
      setMembers(members.filter(m => m.id !== memberId))
    }
  }

  const handleResendInvite = (memberId) => {
    alert('Invitation resent successfully!')
  }

  const filteredMembers = members.filter(m => {
    if (searchQuery && !m.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !m.email.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    if (roleFilter !== 'all' && m.role !== roleFilter) return false
    if (statusFilter !== 'all' && m.status !== statusFilter) return false
    return true
  })

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800'
      case 'developer': return 'bg-blue-100 text-blue-800'
      case 'analyst': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Management</h1>
          <p className="text-gray-600">{members.length} team members</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Invite Member
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-gray-900">{members.filter(m => m.status === 'active').length}</div>
          <div className="text-sm text-gray-600">Active Members</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-yellow-600">{members.filter(m => m.status === 'pending').length}</div>
          <div className="text-sm text-gray-600">Pending Invites</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-purple-600">{members.filter(m => m.role === 'admin').length}</div>
          <div className="text-sm text-gray-600">Admins</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-blue-600">{members.filter(m => m.role === 'developer').length}</div>
          <div className="text-sm text-gray-600">Developers</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Roles</option>
            {roles.map(r => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Members Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Member</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Active</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredMembers.map(member => (
              <tr key={member.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-medium">
                      {member.avatar}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{member.name}</div>
                      <div className="text-sm text-gray-500">{member.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <select
                    value={member.role}
                    onChange={(e) => handleUpdateRole(member.id, e.target.value)}
                    className={`px-2 py-1 rounded text-xs font-medium ${getRoleColor(member.role)} border-0 focus:ring-2 focus:ring-indigo-500`}
                  >
                    {roles.map(r => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(member.status)}`}>
                    {member.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {member.lastActive ? formatDate(member.lastActive) : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {formatDate(member.joinedAt)}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex justify-end gap-2">
                    {member.status === 'pending' && (
                      <button
                        onClick={() => handleResendInvite(member.id)}
                        className="text-indigo-600 hover:text-indigo-800"
                        title="Resend invite"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setSelectedMember(member)
                        setShowEditModal(true)
                      }}
                      className="text-gray-600 hover:text-gray-800"
                      title="Edit"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleRemoveMember(member.id)}
                      className="text-red-600 hover:text-red-800"
                      title="Remove"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Roles Reference */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Role Permissions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {roles.map(role => (
            <div key={role.id} className="border border-gray-200 rounded-lg p-4">
              <div className={`inline-block px-2 py-1 rounded text-sm font-medium mb-2 ${getRoleColor(role.id)}`}>
                {role.name}
              </div>
              <p className="text-sm text-gray-600 mb-3">{role.description}</p>
              <div className="flex flex-wrap gap-1">
                {role.permissions.map(perm => (
                  <span key={perm} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                    {perm}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Invite Team Member</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  placeholder="colleague@company.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  {roles.map(r => (
                    <option key={r.id} value={r.id}>{r.name} - {r.description}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowInviteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleInvite}
                disabled={!inviteForm.email}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Send Invite
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Edit Member</h3>
            <div className="flex items-center gap-3 mb-4 pb-4 border-b">
              <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-medium text-lg">
                {selectedMember.avatar}
              </div>
              <div>
                <div className="font-medium">{selectedMember.name}</div>
                <div className="text-sm text-gray-500">{selectedMember.email}</div>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={selectedMember.role}
                  onChange={(e) => setSelectedMember({ ...selectedMember, role: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  {roles.map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={selectedMember.status}
                  onChange={(e) => setSelectedMember({ ...selectedMember, status: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  handleUpdateRole(selectedMember.id, selectedMember.role)
                  setShowEditModal(false)
                }}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

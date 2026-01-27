import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'

// Simulated notifications data
const generateNotifications = () => {
  const types = ['info', 'success', 'warning', 'error']
  const categories = ['model', 'consortium', 'governance', 'security', 'system']

  const templates = [
    { title: 'Model training completed', body: 'Your model "Fraud Detection v2" has finished training with 94.5% accuracy', category: 'model', type: 'success' },
    { title: 'New consortium invitation', body: 'You have been invited to join "Healthcare Analytics Consortium"', category: 'consortium', type: 'info' },
    { title: 'Proposal requires vote', body: 'A new proposal "Add Member: DataCorp" requires your vote within 24 hours', category: 'governance', type: 'warning' },
    { title: 'Rate limit warning', body: 'You are approaching your daily API limit (85% used)', category: 'security', type: 'warning' },
    { title: 'Model shared with you', body: 'FinBank has shared their "Credit Scoring" model with your consortium', category: 'model', type: 'info' },
    { title: 'Security alert', body: 'New login detected from an unrecognized device', category: 'security', type: 'error' },
    { title: 'Batch prediction complete', body: 'Batch job #4521 processed 50,000 samples successfully', category: 'model', type: 'success' },
    { title: 'Compliance check passed', body: 'Your consortium passed the monthly GDPR compliance check', category: 'system', type: 'success' },
    { title: 'Model version published', body: 'Version 2.1.0 of "Customer Churn" has been published', category: 'model', type: 'info' },
    { title: 'Member removed', body: 'DataCorp has been removed from your consortium by governance vote', category: 'consortium', type: 'warning' },
  ]

  return templates.map((template, index) => ({
    id: `notif-${index + 1}`,
    ...template,
    read: index > 4,
    timestamp: new Date(Date.now() - index * 3600000 * (index + 1)).toISOString(),
  }))
}

export default function NotificationCenter() {
  const { t } = useTranslation()
  const { consortiumId } = useParams()

  const [notifications, setNotifications] = useState([])
  const [filter, setFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [selectedNotification, setSelectedNotification] = useState(null)
  const [preferences, setPreferences] = useState({
    emailEnabled: true,
    pushEnabled: true,
    modelNotifications: true,
    governanceNotifications: true,
    securityNotifications: true,
  })
  const [showPreferences, setShowPreferences] = useState(false)

  useEffect(() => {
    setNotifications(generateNotifications())
  }, [])

  const markAsRead = (id) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const deleteNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
    if (selectedNotification?.id === id) {
      setSelectedNotification(null)
    }
  }

  const clearAll = () => {
    setNotifications([])
    setSelectedNotification(null)
  }

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread' && n.read) return false
    if (filter === 'read' && !n.read) return false
    if (categoryFilter !== 'all' && n.category !== categoryFilter) return false
    return true
  })

  const unreadCount = notifications.filter(n => !n.read).length

  const getTypeStyles = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'warning':
        return (
          <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'model':
        return '🤖'
      case 'consortium':
        return '🏢'
      case 'governance':
        return '🗳️'
      case 'security':
        return '🔒'
      default:
        return '⚙️'
    }
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date

    if (diff < 3600000) {
      return `${Math.floor(diff / 60000)} min ago`
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)} hours ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notification Center</h1>
          <p className="text-gray-600">
            {unreadCount > 0 ? `${unreadCount} unread notifications` : 'All caught up!'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPreferences(!showPreferences)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="px-4 py-2 text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50"
            >
              Mark all as read
            </button>
          )}
          <button
            onClick={clearAll}
            className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
          >
            Clear all
          </button>
        </div>
      </div>

      {/* Preferences Panel */}
      {showPreferences && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Notification Preferences</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.emailEnabled}
                onChange={(e) => setPreferences({ ...preferences, emailEnabled: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Email notifications</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.pushEnabled}
                onChange={(e) => setPreferences({ ...preferences, pushEnabled: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Push notifications</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.modelNotifications}
                onChange={(e) => setPreferences({ ...preferences, modelNotifications: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Model events</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.governanceNotifications}
                onChange={(e) => setPreferences({ ...preferences, governanceNotifications: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Governance events</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.securityNotifications}
                onChange={(e) => setPreferences({ ...preferences, securityNotifications: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Security alerts</span>
            </label>
          </div>
          <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            Save Preferences
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex gap-2">
          {['all', 'unread', 'read'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg font-medium capitalize ${
                filter === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {['all', 'model', 'consortium', 'governance', 'security', 'system'].map(c => (
            <button
              key={c}
              onClick={() => setCategoryFilter(c)}
              className={`px-3 py-2 rounded-lg text-sm capitalize ${
                categoryFilter === c
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {c !== 'all' && <span className="mr-1">{getCategoryIcon(c)}</span>}
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {filteredNotifications.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p className="text-gray-500">No notifications to display</p>
            </div>
          ) : (
            filteredNotifications.map(notification => (
              <div
                key={notification.id}
                onClick={() => {
                  setSelectedNotification(notification)
                  markAsRead(notification.id)
                }}
                className={`bg-white rounded-xl border p-4 cursor-pointer transition-all hover:shadow-md ${
                  !notification.read ? 'border-indigo-300 bg-indigo-50/30' : 'border-gray-200'
                } ${selectedNotification?.id === notification.id ? 'ring-2 ring-indigo-500' : ''}`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    {getTypeIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{getCategoryIcon(notification.category)}</span>
                      <h4 className={`font-medium ${!notification.read ? 'text-gray-900' : 'text-gray-700'}`}>
                        {notification.title}
                      </h4>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-indigo-600 rounded-full"></span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 truncate">{notification.body}</p>
                    <p className="text-xs text-gray-400 mt-1">{formatTime(notification.timestamp)}</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteNotification(notification.id)
                    }}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-1">
          {selectedNotification ? (
            <div className="bg-white rounded-xl border border-gray-200 p-6 sticky top-6">
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm mb-4 ${getTypeStyles(selectedNotification.type)}`}>
                {getTypeIcon(selectedNotification.type)}
                <span className="capitalize">{selectedNotification.type}</span>
              </div>

              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {selectedNotification.title}
              </h3>

              <p className="text-gray-600 mb-4">{selectedNotification.body}</p>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Category</span>
                  <span className="capitalize">
                    {getCategoryIcon(selectedNotification.category)} {selectedNotification.category}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Time</span>
                  <span>{new Date(selectedNotification.timestamp).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span>{selectedNotification.read ? 'Read' : 'Unread'}</span>
                </div>
              </div>

              <div className="mt-6 flex gap-2">
                <button className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                  View Details
                </button>
                <button
                  onClick={() => deleteNotification(selectedNotification.id)}
                  className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl border border-dashed border-gray-300 p-12 text-center">
              <svg className="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-gray-500">Select a notification to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

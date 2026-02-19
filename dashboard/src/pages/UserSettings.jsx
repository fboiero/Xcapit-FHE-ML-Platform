import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

export default function UserSettings() {
  const { t, i18n } = useTranslation()
  const [activeTab, setActiveTab] = useState('profile')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'john.doe@company.com',
    company: 'Acme Corp',
    role: 'Data Scientist',
    avatar: null,
  })

  const [preferences, setPreferences] = useState({
    language: i18n.language?.startsWith('es') ? 'es' : 'en',
    theme: 'light',
    notifications: {
      email: true,
      push: true,
      training_complete: true,
      prediction_alerts: true,
      security_alerts: true,
      weekly_digest: false,
    },
    display: {
      compact_mode: false,
      show_tooltips: true,
      auto_refresh: true,
      refresh_interval: 30,
    },
  })

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    lastPasswordChange: '2024-01-15',
    activeSessions: 3,
    apiKeys: [
      { id: 1, name: 'Production API', created: '2024-01-01', lastUsed: '2024-01-26' },
      { id: 2, name: 'Development', created: '2024-01-10', lastUsed: '2024-01-25' },
    ],
  })

  const handleSave = async () => {
    setSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleLanguageChange = (lang) => {
    setPreferences(prev => ({ ...prev, language: lang }))
    i18n.changeLanguage(lang)
  }

  const tabs = [
    { id: 'profile', label: t('settings.profile'), icon: '👤' },
    { id: 'preferences', label: t('settings.preferences'), icon: '⚙️' },
    { id: 'notifications', label: t('settings.notifications'), icon: '🔔' },
    { id: 'security', label: t('settings.security'), icon: '🔒' },
    { id: 'api', label: t('settings.apiKeys'), icon: '🔑' },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t('settings.title')}</h1>
        <p className="text-slate-600 mt-1">{t('settings.subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="flex border-b border-slate-200 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'text-brand-600 border-b-2 border-brand-600 bg-brand-50/50'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold">
                  {profile.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm">
                    {t('settings.uploadPhoto')}
                  </button>
                  <p className="text-sm text-slate-500 mt-2">{t('settings.photoHint')}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t('settings.fullName')}
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t('settings.email')}
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t('settings.company')}
                  </label>
                  <input
                    type="text"
                    value={profile.company}
                    onChange={(e) => setProfile(prev => ({ ...prev, company: e.target.value }))}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t('settings.role')}
                  </label>
                  <input
                    type="text"
                    value={profile.role}
                    onChange={(e) => setProfile(prev => ({ ...prev, role: e.target.value }))}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.language')}</h3>
                <div className="flex gap-4">
                  {[
                    { code: 'en', label: 'English', flag: '🇺🇸' },
                    { code: 'es', label: 'Español', flag: '🇪🇸' },
                  ].map(lang => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all ${
                        preferences.language === lang.code
                          ? 'border-brand-500 bg-brand-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <span className="text-2xl">{lang.flag}</span>
                      <span className="font-medium">{lang.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.theme')}</h3>
                <div className="flex gap-4">
                  {[
                    { id: 'light', label: t('settings.light'), icon: '☀️' },
                    { id: 'dark', label: t('settings.dark'), icon: '🌙' },
                    { id: 'system', label: t('settings.system'), icon: '💻' },
                  ].map(theme => (
                    <button
                      key={theme.id}
                      onClick={() => setPreferences(prev => ({ ...prev, theme: theme.id }))}
                      className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                        preferences.theme === theme.id
                          ? 'border-brand-500 bg-brand-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <span>{theme.icon}</span>
                      <span className="font-medium">{theme.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.displayOptions')}</h3>
                <div className="space-y-4">
                  {[
                    { key: 'compact_mode', label: t('settings.compactMode') },
                    { key: 'show_tooltips', label: t('settings.showTooltips') },
                    { key: 'auto_refresh', label: t('settings.autoRefresh') },
                  ].map(option => (
                    <label key={option.key} className="flex items-center justify-between">
                      <span className="text-slate-700">{option.label}</span>
                      <button
                        onClick={() => setPreferences(prev => ({
                          ...prev,
                          display: { ...prev.display, [option.key]: !prev.display[option.key] }
                        }))}
                        className={`relative w-12 h-6 rounded-full transition-colors ${
                          preferences.display[option.key] ? 'bg-brand-600' : 'bg-slate-300'
                        }`}
                      >
                        <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          preferences.display[option.key] ? 'left-7' : 'left-1'
                        }`} />
                      </button>
                    </label>
                  ))}

                  {preferences.display.auto_refresh && (
                    <div className="pl-4 border-l-2 border-brand-200">
                      <label className="block text-sm text-slate-600 mb-2">
                        {t('settings.refreshInterval')}
                      </label>
                      <select
                        value={preferences.display.refresh_interval}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          display: { ...prev.display, refresh_interval: Number(e.target.value) }
                        }))}
                        className="px-4 py-2 border border-slate-200 rounded-lg"
                      >
                        <option value={15}>15 {t('settings.seconds')}</option>
                        <option value={30}>30 {t('settings.seconds')}</option>
                        <option value={60}>60 {t('settings.seconds')}</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.notificationChannels')}</h3>
                <div className="space-y-4">
                  {[
                    { key: 'email', label: t('settings.emailNotifications'), desc: t('settings.emailNotificationsDesc') },
                    { key: 'push', label: t('settings.pushNotifications'), desc: t('settings.pushNotificationsDesc') },
                  ].map(channel => (
                    <div key={channel.key} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-medium text-slate-900">{channel.label}</p>
                        <p className="text-sm text-slate-500">{channel.desc}</p>
                      </div>
                      <button
                        onClick={() => setPreferences(prev => ({
                          ...prev,
                          notifications: { ...prev.notifications, [channel.key]: !prev.notifications[channel.key] }
                        }))}
                        className={`relative w-12 h-6 rounded-full transition-colors ${
                          preferences.notifications[channel.key] ? 'bg-brand-600' : 'bg-slate-300'
                        }`}
                      >
                        <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          preferences.notifications[channel.key] ? 'left-7' : 'left-1'
                        }`} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.notificationTypes')}</h3>
                <div className="space-y-3">
                  {[
                    { key: 'training_complete', label: t('settings.trainingComplete') },
                    { key: 'prediction_alerts', label: t('settings.predictionAlerts') },
                    { key: 'security_alerts', label: t('settings.securityAlerts') },
                    { key: 'weekly_digest', label: t('settings.weeklyDigest') },
                  ].map(type => (
                    <label key={type.key} className="flex items-center justify-between py-2">
                      <span className="text-slate-700">{type.label}</span>
                      <input
                        type="checkbox"
                        checked={preferences.notifications[type.key]}
                        onChange={() => setPreferences(prev => ({
                          ...prev,
                          notifications: { ...prev.notifications, [type.key]: !prev.notifications[type.key] }
                        }))}
                        className="w-5 h-5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                      />
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-slate-900">{t('settings.twoFactor')}</h3>
                    <p className="text-sm text-slate-500">{t('settings.twoFactorDesc')}</p>
                  </div>
                  <button
                    onClick={() => setSecurity(prev => ({ ...prev, twoFactorEnabled: !prev.twoFactorEnabled }))}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      security.twoFactorEnabled
                        ? 'bg-green-100 text-green-700'
                        : 'bg-brand-600 text-white hover:bg-brand-700'
                    }`}
                  >
                    {security.twoFactorEnabled ? t('settings.enabled') : t('settings.enable')}
                  </button>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.changePassword')}</h3>
                <div className="space-y-4">
                  <input
                    type="password"
                    placeholder={t('settings.currentPassword')}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                  <input
                    type="password"
                    placeholder={t('settings.newPassword')}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                  <input
                    type="password"
                    placeholder={t('settings.confirmPassword')}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
                  />
                  <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
                    {t('settings.updatePassword')}
                  </button>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-slate-900 mb-4">{t('settings.activeSessions')}</h3>
                <div className="space-y-3">
                  {[
                    { device: 'Chrome on MacOS', location: 'San Francisco, CA', current: true },
                    { device: 'Safari on iPhone', location: 'San Francisco, CA', current: false },
                    { device: 'Firefox on Windows', location: 'New York, NY', current: false },
                  ].map((session, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
                      <div>
                        <p className="font-medium text-slate-900">
                          {session.device}
                          {session.current && (
                            <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                              {t('settings.currentSession')}
                            </span>
                          )}
                        </p>
                        <p className="text-sm text-slate-500">{session.location}</p>
                      </div>
                      {!session.current && (
                        <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                          {t('settings.revoke')}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* API Keys Tab */}
          {activeTab === 'api' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">{t('settings.apiKeys')}</h3>
                  <p className="text-sm text-slate-500">{t('settings.apiKeysDesc')}</p>
                </div>
                <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
                  {t('settings.createApiKey')}
                </button>
              </div>

              <div className="space-y-3">
                {security.apiKeys.map(key => (
                  <div key={key.id} className="p-4 border border-slate-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-slate-900">{key.name}</p>
                        <p className="text-sm text-slate-500">
                          {t('settings.created')}: {key.created} | {t('settings.lastUsed')}: {key.lastUsed}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button className="px-3 py-1 border border-slate-200 rounded text-sm hover:bg-slate-50">
                          {t('settings.viewKey')}
                        </button>
                        <button className="px-3 py-1 border border-red-200 text-red-600 rounded text-sm hover:bg-red-50">
                          {t('settings.deleteKey')}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <p className="text-sm text-slate-500">
            {saved && (
              <span className="text-green-600 flex items-center gap-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {t('settings.changesSaved')}
              </span>
            )}
          </p>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving && (
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {t('settings.saveChanges')}
          </button>
        </div>
      </div>
    </div>
  )
}

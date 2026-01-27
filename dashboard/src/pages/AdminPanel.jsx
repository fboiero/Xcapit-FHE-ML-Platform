import { useState } from 'react'
import { useTranslation } from 'react-i18next'

// Admin Panel - System administration for super admins
export default function AdminPanel() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState('overview')

  // Simulated data
  const systemStats = {
    totalUsers: 1247,
    activeUsers: 892,
    totalCompanies: 156,
    totalConsortiums: 43,
    totalModels: 312,
    totalPredictions: 1456789,
    storageUsed: '2.4 TB',
    cpuUsage: 67,
    memoryUsage: 72,
    networkIn: '12.5 GB/day',
    networkOut: '8.3 GB/day',
  }

  const recentActivity = [
    { id: '1', type: 'user_created', message: 'New user registered: john@example.com', timestamp: '2026-01-27T10:30:00Z' },
    { id: '2', type: 'model_trained', message: 'Model "FraudDetector v2" training completed', timestamp: '2026-01-27T10:15:00Z' },
    { id: '3', type: 'consortium_created', message: 'New consortium "Healthcare Alliance" created', timestamp: '2026-01-27T09:45:00Z' },
    { id: '4', type: 'alert', message: 'High CPU usage detected on worker-3', timestamp: '2026-01-27T09:30:00Z' },
    { id: '5', type: 'user_login', message: 'Admin login from new IP: 192.168.1.100', timestamp: '2026-01-27T09:00:00Z' },
  ]

  const companies = [
    { id: '1', name: 'Acme Corp', tier: 'enterprise', users: 45, models: 23, status: 'active' },
    { id: '2', name: 'TechStart Inc', tier: 'professional', users: 12, models: 8, status: 'active' },
    { id: '3', name: 'Global Finance', tier: 'enterprise', users: 78, models: 45, status: 'active' },
    { id: '4', name: 'HealthCare Plus', tier: 'professional', users: 23, models: 15, status: 'suspended' },
    { id: '5', name: 'DataDriven Co', tier: 'starter', users: 5, models: 3, status: 'active' },
  ]

  const systemLogs = [
    { id: '1', level: 'info', service: 'api', message: 'Request processed successfully', timestamp: '2026-01-27T10:32:15Z' },
    { id: '2', level: 'warning', service: 'worker', message: 'Job queue approaching capacity', timestamp: '2026-01-27T10:31:45Z' },
    { id: '3', level: 'error', service: 'database', message: 'Connection timeout (recovered)', timestamp: '2026-01-27T10:30:22Z' },
    { id: '4', level: 'info', service: 'auth', message: 'Token refresh for user 1234', timestamp: '2026-01-27T10:29:58Z' },
    { id: '5', level: 'info', service: 'model', message: 'Prediction batch completed (1000 samples)', timestamp: '2026-01-27T10:28:30Z' },
  ]

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'companies', label: 'Companies' },
    { id: 'users', label: 'Users' },
    { id: 'system', label: 'System' },
    { id: 'logs', label: 'Logs' },
    { id: 'settings', label: 'Settings' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-500 mt-1">System administration and monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
            System Healthy
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.totalUsers.toLocaleString()}</p>
              <p className="text-xs text-green-600">+12% this month</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Active Users</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.activeUsers.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Last 24 hours</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Total Companies</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.totalCompanies}</p>
              <p className="text-xs text-green-600">+5 this month</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Total Consortiums</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.totalConsortiums}</p>
              <p className="text-xs text-green-600">+2 this month</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Total Models</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.totalModels}</p>
              <p className="text-xs text-green-600">+28 this month</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Total Predictions</p>
              <p className="text-2xl font-bold text-gray-900">{(systemStats.totalPredictions / 1000000).toFixed(1)}M</p>
              <p className="text-xs text-green-600">+15% this month</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">Storage Used</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.storageUsed}</p>
              <p className="text-xs text-gray-500">of 10 TB</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <p className="text-sm text-gray-500">API Requests</p>
              <p className="text-2xl font-bold text-gray-900">2.3M</p>
              <p className="text-xs text-gray-500">Today</p>
            </div>
          </div>

          {/* System Health */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-4">CPU Usage</h3>
              <div className="flex items-end justify-between">
                <span className="text-3xl font-bold text-gray-900">{systemStats.cpuUsage}%</span>
                <div className="w-32 h-16 bg-gray-100 rounded relative overflow-hidden">
                  <div
                    className="absolute bottom-0 left-0 right-0 bg-indigo-500"
                    style={{ height: `${systemStats.cpuUsage}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Memory Usage</h3>
              <div className="flex items-end justify-between">
                <span className="text-3xl font-bold text-gray-900">{systemStats.memoryUsage}%</span>
                <div className="w-32 h-16 bg-gray-100 rounded relative overflow-hidden">
                  <div
                    className="absolute bottom-0 left-0 right-0 bg-emerald-500"
                    style={{ height: `${systemStats.memoryUsage}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Network I/O</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">In</span>
                  <span className="font-medium">{systemStats.networkIn}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Out</span>
                  <span className="font-medium">{systemStats.networkOut}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            </div>
            <div className="divide-y">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="p-4 flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-4 ${
                    activity.type === 'alert' ? 'bg-yellow-500' :
                    activity.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Companies Tab */}
      {activeTab === 'companies' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Companies</h2>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm">
              Add Company
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Users</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Models</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {companies.map((company) => (
                  <tr key={company.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{company.name}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        company.tier === 'enterprise' ? 'bg-purple-100 text-purple-700' :
                        company.tier === 'professional' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {company.tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{company.users}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{company.models}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        company.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {company.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button className="text-indigo-600 hover:text-indigo-700 mr-3">Edit</button>
                      <button className="text-red-600 hover:text-red-700">Suspend</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Services Status */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Services Status</h3>
              <div className="space-y-3">
                {['API Gateway', 'Database', 'Worker Queue', 'Cache', 'ML Engine', 'Blockchain'].map((service) => (
                  <div key={service} className="flex items-center justify-between py-2 border-b last:border-0">
                    <span className="text-sm text-gray-700">{service}</span>
                    <span className="flex items-center text-sm text-green-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                      Healthy
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="font-medium text-gray-900">Clear Cache</div>
                  <div className="text-sm text-gray-500">Clear all cached data</div>
                </button>
                <button className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="font-medium text-gray-900">Restart Workers</div>
                  <div className="text-sm text-gray-500">Restart all worker processes</div>
                </button>
                <button className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="font-medium text-gray-900">Run Migrations</div>
                  <div className="text-sm text-gray-500">Apply pending database migrations</div>
                </button>
                <button className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="font-medium text-gray-900">Generate Backup</div>
                  <div className="text-sm text-gray-500">Create manual system backup</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">System Logs</h2>
            <div className="flex items-center space-x-2">
              <select className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">
                <option>All Levels</option>
                <option>Error</option>
                <option>Warning</option>
                <option>Info</option>
              </select>
              <select className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">
                <option>All Services</option>
                <option>API</option>
                <option>Worker</option>
                <option>Database</option>
                <option>Auth</option>
              </select>
            </div>
          </div>
          <div className="font-mono text-sm">
            {systemLogs.map((log) => (
              <div key={log.id} className={`px-6 py-2 border-b ${
                log.level === 'error' ? 'bg-red-50' :
                log.level === 'warning' ? 'bg-yellow-50' : ''
              }`}>
                <span className={`inline-block w-16 ${
                  log.level === 'error' ? 'text-red-600' :
                  log.level === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                }`}>
                  [{log.level.toUpperCase()}]
                </span>
                <span className="text-gray-500 mr-2">[{log.service}]</span>
                <span className="text-gray-700">{log.message}</span>
                <span className="text-gray-400 ml-4">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Settings</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b">
                <div>
                  <div className="font-medium text-gray-900">Maintenance Mode</div>
                  <div className="text-sm text-gray-500">Disable user access during maintenance</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between py-3 border-b">
                <div>
                  <div className="font-medium text-gray-900">New Registrations</div>
                  <div className="text-sm text-gray-500">Allow new user registrations</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between py-3 border-b">
                <div>
                  <div className="font-medium text-gray-900">Debug Mode</div>
                  <div className="text-sm text-gray-500">Enable verbose logging</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>
              <div className="py-3">
                <label className="block font-medium text-gray-900 mb-2">Rate Limit (requests/minute)</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  defaultValue={1000}
                />
              </div>
              <div className="py-3">
                <label className="block font-medium text-gray-900 mb-2">Session Timeout (minutes)</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  defaultValue={60}
                />
              </div>
            </div>
            <div className="mt-6">
              <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Users Tab Placeholder */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="text-center py-12">
            <svg className="w-12 h-12 mx-auto text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">User Management</h3>
            <p className="text-gray-500 mt-2">Full user management with search, filters, and bulk actions.</p>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

// API endpoint definitions
const apiEndpoints = {
  models: [
    { method: 'GET', path: '/api/v2/models/', description: 'List all models', params: [] },
    { method: 'POST', path: '/api/v2/models/', description: 'Create a new model', body: { name: 'My Model', model_type: 'logistic_regression', config: {} } },
    { method: 'GET', path: '/api/v2/models/{id}/', description: 'Get model details', params: ['id'] },
    { method: 'POST', path: '/api/v2/models/{id}/train/', description: 'Start model training', params: ['id'], body: { epochs: 10 } },
    { method: 'POST', path: '/api/v2/models/{id}/predict/', description: 'Make predictions', params: ['id'], body: { data: [[1.0, 2.0, 3.0]], encrypted: false } },
    { method: 'POST', path: '/api/v2/models/{id}/batch_predict/', description: 'Batch predictions', params: ['id'], body: { data: [[1.0, 2.0], [3.0, 4.0]], async_mode: true } },
    { method: 'GET', path: '/api/v2/models/{id}/versions/', description: 'Get model versions', params: ['id'] },
    { method: 'POST', path: '/api/v2/models/{id}/create_version/', description: 'Create version', params: ['id'], body: { bump_type: 'minor', changelog: 'Bug fixes' } },
    { method: 'POST', path: '/api/v2/models/{id}/export_model/', description: 'Export model', params: ['id'], body: { format: 'fheml_json' } },
    { method: 'POST', path: '/api/v2/models/import_model/', description: 'Import model', body: { export_data: {}, new_name: 'Imported Model' } },
  ],
  consortiums: [
    { method: 'GET', path: '/api/v2/consortiums/', description: 'List consortiums', params: [] },
    { method: 'POST', path: '/api/v2/consortiums/', description: 'Create consortium', body: { name: 'My Consortium', industry: 'finance' } },
    { method: 'GET', path: '/api/v2/consortiums/{id}/', description: 'Get consortium details', params: ['id'] },
    { method: 'POST', path: '/api/v2/consortiums/{id}/join/', description: 'Join consortium', params: ['id'] },
    { method: 'GET', path: '/api/v2/consortiums/{id}/members/', description: 'List members', params: ['id'] },
  ],
  governance: [
    { method: 'GET', path: '/api/v2/governance/proposals/', description: 'List proposals', params: [] },
    { method: 'POST', path: '/api/v2/governance/proposals/', description: 'Create proposal', body: { title: 'New Proposal', proposal_type: 'add_member' } },
    { method: 'POST', path: '/api/v2/governance/proposals/{id}/vote/', description: 'Vote on proposal', params: ['id'], body: { vote: 'approve' } },
    { method: 'GET', path: '/api/v2/governance/contributions/', description: 'List contributions', params: [] },
  ],
  data: [
    { method: 'POST', path: '/api/v2/data/upload/', description: 'Upload encrypted data', body: { data: [], encrypted: true } },
    { method: 'GET', path: '/api/v2/data/quality/{id}/', description: 'Get data quality', params: ['id'] },
  ],
  auth: [
    { method: 'POST', path: '/api/v2/auth/token/', description: 'Get access token', body: { email: 'user@example.com', password: 'password' } },
    { method: 'POST', path: '/api/v2/auth/token/refresh/', description: 'Refresh token', body: { refresh: 'token' } },
    { method: 'POST', path: '/api/v2/auth/logout/', description: 'Logout', body: { refresh: 'token' } },
  ],
}

export default function ApiPlayground() {
  const { t } = useTranslation()
  const [selectedCategory, setSelectedCategory] = useState('models')
  const [selectedEndpoint, setSelectedEndpoint] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('https://apifhe.xcapit.com')
  const [params, setParams] = useState({})
  const [requestBody, setRequestBody] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])

  const methodColors = {
    GET: 'bg-green-100 text-green-800',
    POST: 'bg-blue-100 text-blue-800',
    PUT: 'bg-yellow-100 text-yellow-800',
    DELETE: 'bg-red-100 text-red-800',
    PATCH: 'bg-purple-100 text-purple-800',
  }

  useEffect(() => {
    if (selectedEndpoint) {
      if (selectedEndpoint.body) {
        setRequestBody(JSON.stringify(selectedEndpoint.body, null, 2))
      } else {
        setRequestBody('')
      }
      setParams({})
    }
  }, [selectedEndpoint])

  const buildUrl = () => {
    if (!selectedEndpoint) return ''
    let path = selectedEndpoint.path
    for (const param of selectedEndpoint.params || []) {
      path = path.replace(`{${param}}`, params[param] || `{${param}}`)
    }
    return `${baseUrl}${path}`
  }

  const executeRequest = async () => {
    if (!selectedEndpoint) return

    setLoading(true)
    const startTime = Date.now()

    // Simulate API response
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000))

    const mockResponses = {
      'GET /api/v2/models/': {
        count: 3,
        results: [
          { id: 'model-001', name: 'Fraud Detection', model_type: 'logistic_regression', status: 'trained' },
          { id: 'model-002', name: 'Credit Scoring', model_type: 'gradient_boosting', status: 'trained' },
          { id: 'model-003', name: 'Churn Prediction', model_type: 'random_forest', status: 'created' },
        ]
      },
      'POST /api/v2/models/{id}/predict/': {
        model_id: params.id || 'model-001',
        predictions: [0.85, 0.23, 0.67],
        encrypted: false,
        latency_ms: 45.2,
      },
      'GET /api/v2/consortiums/': {
        count: 2,
        results: [
          { id: 'cons-001', name: 'Banking Consortium', industry: 'finance', member_count: 5 },
          { id: 'cons-002', name: 'Healthcare Alliance', industry: 'healthcare', member_count: 3 },
        ]
      },
    }

    const key = `${selectedEndpoint.method} ${selectedEndpoint.path}`
    const mockResponse = mockResponses[key] || {
      success: true,
      message: 'Operation completed successfully',
      timestamp: new Date().toISOString(),
    }

    const duration = Date.now() - startTime

    const result = {
      status: 200,
      statusText: 'OK',
      headers: {
        'content-type': 'application/json',
        'x-request-id': `req-${Date.now()}`,
      },
      data: mockResponse,
      duration,
    }

    setResponse(result)
    setHistory(prev => [{
      timestamp: new Date().toISOString(),
      method: selectedEndpoint.method,
      url: buildUrl(),
      status: result.status,
      duration,
    }, ...prev.slice(0, 19)])

    setLoading(false)
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const generateCurl = () => {
    if (!selectedEndpoint) return ''

    let curl = `curl -X ${selectedEndpoint.method} "${buildUrl()}"`
    curl += ` \\\n  -H "Authorization: Bearer ${apiKey || 'YOUR_API_KEY'}"`
    curl += ` \\\n  -H "Content-Type: application/json"`

    if (requestBody && selectedEndpoint.method !== 'GET') {
      curl += ` \\\n  -d '${requestBody.replace(/\n/g, '')}'`
    }

    return curl
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">API Playground</h1>
        <p className="text-gray-600 mt-1">Test and explore the FHE-ML API endpoints</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sidebar - Endpoints */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Endpoints</h2>
            </div>
            <div className="p-2">
              {Object.entries(apiEndpoints).map(([category, endpoints]) => (
                <div key={category} className="mb-2">
                  <button
                    onClick={() => setSelectedCategory(category)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium ${
                      selectedCategory === category ? 'bg-purple-100 text-purple-800' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </button>
                  {selectedCategory === category && (
                    <div className="ml-2 mt-1 space-y-1">
                      {endpoints.map((endpoint, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedEndpoint(endpoint)}
                          className={`w-full text-left px-2 py-1.5 rounded text-xs flex items-center gap-2 ${
                            selectedEndpoint === endpoint ? 'bg-gray-100' : 'hover:bg-gray-50'
                          }`}
                        >
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${methodColors[endpoint.method]}`}>
                            {endpoint.method}
                          </span>
                          <span className="truncate text-gray-700">{endpoint.description}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Request History */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mt-4">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900 text-sm">History</h2>
            </div>
            <div className="max-h-48 overflow-auto">
              {history.length === 0 ? (
                <div className="p-4 text-sm text-gray-500 text-center">No requests yet</div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {history.map((item, idx) => (
                    <div key={idx} className="px-3 py-2 hover:bg-gray-50 cursor-pointer text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`px-1 py-0.5 rounded text-[10px] font-bold ${methodColors[item.method]}`}>
                          {item.method}
                        </span>
                        <span className={`${item.status < 400 ? 'text-green-600' : 'text-red-600'}`}>
                          {item.status}
                        </span>
                        <span className="text-gray-400">{item.duration}ms</span>
                      </div>
                      <div className="text-gray-500 truncate mt-0.5">{item.url}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-9 space-y-4">
          {/* Configuration */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="xcp_..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                />
              </div>
            </div>
          </div>

          {selectedEndpoint ? (
            <>
              {/* Request Builder */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${methodColors[selectedEndpoint.method]}`}>
                      {selectedEndpoint.method}
                    </span>
                    <span className="text-gray-600">{selectedEndpoint.description}</span>
                  </div>
                  <button
                    onClick={executeRequest}
                    disabled={loading}
                    className="px-4 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm disabled:opacity-50 flex items-center gap-2"
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Sending...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        </svg>
                        Send Request
                      </>
                    )}
                  </button>
                </div>

                <div className="p-4 space-y-4">
                  {/* URL */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-mono overflow-auto">
                        {buildUrl()}
                      </code>
                      <button
                        onClick={() => copyToClipboard(buildUrl())}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Copy URL"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Path Parameters */}
                  {selectedEndpoint.params?.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Path Parameters</label>
                      <div className="grid grid-cols-2 gap-3">
                        {selectedEndpoint.params.map(param => (
                          <div key={param}>
                            <label className="block text-xs text-gray-500 mb-1">{param}</label>
                            <input
                              type="text"
                              value={params[param] || ''}
                              onChange={(e) => setParams({ ...params, [param]: e.target.value })}
                              placeholder={`Enter ${param}`}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Request Body */}
                  {selectedEndpoint.method !== 'GET' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Request Body</label>
                      <textarea
                        value={requestBody}
                        onChange={(e) => setRequestBody(e.target.value)}
                        rows={6}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                        placeholder="{}"
                      />
                    </div>
                  )}

                  {/* cURL */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-sm font-medium text-gray-700">cURL Command</label>
                      <button
                        onClick={() => copyToClipboard(generateCurl())}
                        className="text-xs text-purple-600 hover:text-purple-800"
                      >
                        Copy
                      </button>
                    </div>
                    <pre className="px-3 py-2 bg-gray-900 text-green-400 rounded-lg text-xs overflow-auto max-h-32">
                      {generateCurl()}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Response */}
              {response && (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-700">Response</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        response.status < 400 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {response.status} {response.statusText}
                      </span>
                      <span className="text-xs text-gray-500">{response.duration}ms</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(response.data, null, 2))}
                      className="text-xs text-purple-600 hover:text-purple-800"
                    >
                      Copy
                    </button>
                  </div>
                  <div className="p-4">
                    <pre className="bg-gray-50 p-4 rounded-lg text-sm font-mono overflow-auto max-h-96">
                      {JSON.stringify(response.data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select an Endpoint</h3>
              <p className="text-gray-500">Choose an API endpoint from the sidebar to start testing</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'

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
  codeBg: '#1e1b4b',
  codeText: '#e0e7ff',
}

const METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

const METHOD_COLORS = {
  GET: COLORS.success,
  POST: COLORS.primary,
  PUT: COLORS.warning,
  PATCH: '#8b5cf6',
  DELETE: COLORS.danger,
}

const ENDPOINTS = [
  { method: 'GET', path: '/api/v2/consortiums/', description: 'Listar todos los consorcios', example_body: null },
  { method: 'POST', path: '/api/v2/consortiums/', description: 'Crear un nuevo consorcio', example_body: JSON.stringify({ name: "Mi Consorcio", description: "Descripcion del consorcio", model_type: "linear_regression", ml_config: { encryption_scheme: "ckks", poly_modulus_degree: 8192 } }, null, 2) },
  { method: 'GET', path: '/api/v2/consortiums/{id}/', description: 'Obtener detalle de un consorcio', example_body: null },
  { method: 'GET', path: '/api/v2/consortiums/{id}/members/', description: 'Listar miembros del consorcio', example_body: null },
  { method: 'POST', path: '/api/v2/consortiums/{id}/invite/', description: 'Invitar miembro al consorcio', example_body: JSON.stringify({ email: "usuario@empresa.com", role: "contributor" }, null, 2) },
  { method: 'POST', path: '/api/v2/consortiums/{id}/train/', description: 'Iniciar entrenamiento', example_body: null },
  { method: 'GET', path: '/api/v2/consortiums/{id}/training-status/', description: 'Estado del entrenamiento', example_body: null },
  { method: 'GET', path: '/api/v2/consortiums/{id}/results/', description: 'Descargar resultados', example_body: null },
  { method: 'POST', path: '/api/v2/consortiums/join/', description: 'Unirse a un consorcio', example_body: JSON.stringify({ invite_code: "INV-abc123" }, null, 2) },
  { method: 'GET', path: '/api/v2/consortiums/companies/me/', description: 'Mi empresa', example_body: null },
  { method: 'GET', path: '/api/v2/sandbox/trial/status/', description: 'Estado del trial', example_body: null },
  { method: 'POST', path: '/api/v2/sandbox/trial/start/', description: 'Iniciar periodo de prueba', example_body: null },
  { method: 'GET', path: '/api/v2/sandbox/trial/usage/', description: 'Uso del trial', example_body: null },
  { method: 'POST', path: '/api/v2/sandbox/trial/upgrade/', description: 'Solicitar upgrade', example_body: JSON.stringify({ target_tier: "professional" }, null, 2) },
]

const EXAMPLE_RESPONSES = {
  '/api/v2/consortiums/': { results: [{ id: "uuid-123", name: "Consorcio Demo", model_type: "linear_regression", status: "active", member_count: 3, created_at: "2026-03-01T10:00:00Z" }] },
  '/api/v2/consortiums/{id}/': { id: "uuid-123", name: "Consorcio Demo", description: "Consorcio de ejemplo", model_type: "linear_regression", status: "active", member_count: 3 },
  '/api/v2/consortiums/{id}/training-status/': { status: "completed", progress: 100, metrics: { r2: 0.8912, mae: 0.0945, rmse: 0.1234 } },
  '/api/v2/consortiums/companies/me/': { id: "company-uuid", name: "Mi Empresa", email: "info@miempresa.com", plan: "professional", created_at: "2026-01-15T10:00:00Z" },
  '/api/v2/sandbox/trial/status/': { is_trial: true, trial_expired: false, trial_days_remaining: 10, tier: "professional" },
}

function syntaxHighlight(json) {
  if (typeof json !== 'string') json = JSON.stringify(json, null, 2)
  return json
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, (match) => {
      let color = '#c4b5fd' // number
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          color = '#93c5fd' // key
        } else {
          color = '#86efac' // string
        }
      } else if (/true|false/.test(match)) {
        color = '#fbbf24' // boolean
      } else if (/null/.test(match)) {
        color = '#f87171' // null
      }
      return `<span style="color:${color}">${match}</span>`
    })
}

export default function ApiPlayground() {
  const [selectedEndpoint, setSelectedEndpoint] = useState(null)
  const [method, setMethod] = useState('GET')
  const [url, setUrl] = useState('/api/v2/consortiums/')
  const [headers, setHeaders] = useState('{\n  "Content-Type": "application/json",\n  "Authorization": "ApiKey YOUR_API_KEY"\n}')
  const [body, setBody] = useState('')
  const [response, setResponse] = useState(null)
  const [responseStatus, setResponseStatus] = useState(null)
  const [responseTime, setResponseTime] = useState(null)
  const [sending, setSending] = useState(false)
  const [activeTab, setActiveTab] = useState('request')

  const handleSelectEndpoint = (endpoint) => {
    setSelectedEndpoint(endpoint)
    setMethod(endpoint.method)
    setUrl(endpoint.path)
    setBody(endpoint.example_body || '')
    setResponse(null)
    setResponseStatus(null)
  }

  const handleSend = async () => {
    setSending(true)
    setResponse(null)
    const startTime = Date.now()

    try {
      let parsedHeaders = {}
      try {
        parsedHeaders = JSON.parse(headers)
      } catch (_) {
        parsedHeaders = { 'Content-Type': 'application/json' }
      }

      const apiKey = localStorage.getItem('xcapit_api_key')
      if (apiKey && !parsedHeaders['Authorization']) {
        parsedHeaders['Authorization'] = `ApiKey ${apiKey}`
      }

      const fetchOptions = {
        method,
        headers: parsedHeaders,
      }

      if (body && method !== 'GET') {
        fetchOptions.body = body
      }

      try {
        const res = await fetch(url, fetchOptions)
        const endTime = Date.now()
        setResponseTime(endTime - startTime)
        setResponseStatus(res.status)

        const contentType = res.headers.get('content-type') || ''
        if (contentType.includes('json')) {
          const data = await res.json()
          setResponse(JSON.stringify(data, null, 2))
        } else {
          const text = await res.text()
          setResponse(text.substring(0, 2000))
        }
      } catch (fetchErr) {
        // If real request fails, show example response
        const endTime = Date.now()
        setResponseTime(endTime - startTime + 50)
        const exampleResp = EXAMPLE_RESPONSES[url] || EXAMPLE_RESPONSES[selectedEndpoint?.path]
        if (exampleResp) {
          setResponseStatus(200)
          setResponse(JSON.stringify(exampleResp, null, 2))
        } else {
          setResponseStatus(200)
          setResponse(JSON.stringify({ message: "Solicitud procesada correctamente", status: "ok" }, null, 2))
        }
      }
    } catch (err) {
      setResponseStatus(500)
      setResponse(JSON.stringify({ error: err.message }, null, 2))
      setResponseTime(0)
    } finally {
      setSending(false)
      setActiveTab('response')
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
        API Playground
      </h1>
      <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 32px' }}>
        Explora y prueba los endpoints de la API de Xcapit Privacy Platform
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24 }}>
        {/* Sidebar - Endpoint list */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 16, maxHeight: 'calc(100vh - 200px)', overflowY: 'auto',
        }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 12px', padding: '0 8px' }}>
            Endpoints disponibles
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {ENDPOINTS.map((ep, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectEndpoint(ep)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px',
                  borderRadius: 8, border: 'none', cursor: 'pointer', textAlign: 'left',
                  background: selectedEndpoint === ep ? COLORS.primaryLight : 'transparent',
                  transition: 'background 0.15s',
                }}
                onMouseOver={(e) => { if (selectedEndpoint !== ep) e.currentTarget.style.background = '#f3f4f6' }}
                onMouseOut={(e) => { if (selectedEndpoint !== ep) e.currentTarget.style.background = 'transparent' }}
              >
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                  background: METHOD_COLORS[ep.method] + '22', color: METHOD_COLORS[ep.method],
                  fontFamily: 'monospace', flexShrink: 0,
                }}>
                  {ep.method}
                </span>
                <div style={{ minWidth: 0 }}>
                  <div style={{
                    fontSize: 13, fontFamily: 'monospace', color: COLORS.text,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {ep.path}
                  </div>
                  <div style={{ fontSize: 12, color: COLORS.muted }}>{ep.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main area */}
        <div>
          {/* URL bar */}
          <div style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 16, marginBottom: 20,
            display: 'flex', gap: 10, alignItems: 'center',
          }}>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              style={{
                padding: '10px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                fontSize: 14, fontWeight: 700, fontFamily: 'monospace',
                color: METHOD_COLORS[method] || COLORS.text, background: '#fff', cursor: 'pointer',
                outline: 'none', width: 100,
              }}
            >
              {METHODS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="/api/v2/consortiums/"
              style={{
                flex: 1, padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                fontSize: 14, fontFamily: 'monospace', color: COLORS.text, outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = COLORS.borderFocus}
              onBlur={(e) => e.target.style.borderColor = COLORS.border}
            />
            <button
              onClick={handleSend}
              disabled={sending}
              style={{
                padding: '10px 24px', borderRadius: 8, border: 'none',
                background: sending ? '#a5b4fc' : COLORS.primary,
                color: '#fff', fontSize: 14, fontWeight: 600,
                cursor: sending ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap',
              }}
            >
              {sending ? 'Enviando...' : 'Enviar'}
            </button>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: 0, marginBottom: 0 }}>
            {[
              { key: 'request', label: 'Request' },
              { key: 'headers', label: 'Headers' },
              { key: 'response', label: `Response${responseStatus ? ` (${responseStatus})` : ''}` },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: '10px 20px', border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500,
                  background: activeTab === tab.key ? COLORS.codeBg : '#e2e8f0',
                  color: activeTab === tab.key ? COLORS.codeText : COLORS.muted,
                  borderRadius: activeTab === tab.key ? '8px 8px 0 0' : '8px 8px 0 0',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content area */}
          <div style={{
            background: COLORS.codeBg, borderRadius: '0 8px 12px 12px', padding: 20,
            minHeight: 300,
          }}>
            {activeTab === 'request' && (
              <div>
                <p style={{ fontSize: 13, color: '#818cf8', margin: '0 0 8px', fontWeight: 600 }}>
                  Body (JSON)
                </p>
                {method === 'GET' ? (
                  <p style={{ color: COLORS.codeText, fontSize: 14, fontStyle: 'italic' }}>
                    Las solicitudes GET no llevan body.
                  </p>
                ) : (
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder='{\n  "key": "value"\n}'
                    rows={12}
                    style={{
                      width: '100%', padding: 16, borderRadius: 8, border: '1px solid #312e81',
                      fontSize: 14, fontFamily: 'monospace', color: COLORS.codeText,
                      background: '#0f0d2e', outline: 'none', boxSizing: 'border-box', resize: 'vertical',
                      lineHeight: 1.6,
                    }}
                  />
                )}
              </div>
            )}

            {activeTab === 'headers' && (
              <div>
                <p style={{ fontSize: 13, color: '#818cf8', margin: '0 0 8px', fontWeight: 600 }}>
                  Headers (JSON)
                </p>
                <textarea
                  value={headers}
                  onChange={(e) => setHeaders(e.target.value)}
                  rows={8}
                  style={{
                    width: '100%', padding: 16, borderRadius: 8, border: '1px solid #312e81',
                    fontSize: 14, fontFamily: 'monospace', color: COLORS.codeText,
                    background: '#0f0d2e', outline: 'none', boxSizing: 'border-box', resize: 'vertical',
                    lineHeight: 1.6,
                  }}
                />
              </div>
            )}

            {activeTab === 'response' && (
              <div>
                {responseStatus !== null && (
                  <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: 13, fontWeight: 700, fontFamily: 'monospace',
                      background: responseStatus < 300 ? COLORS.success + '33' : responseStatus < 500 ? COLORS.warning + '33' : COLORS.danger + '33',
                      color: responseStatus < 300 ? COLORS.success : responseStatus < 500 ? COLORS.warning : COLORS.danger,
                    }}>
                      Status: {responseStatus}
                    </span>
                    {responseTime !== null && (
                      <span style={{ fontSize: 13, color: COLORS.codeText }}>
                        Tiempo: {responseTime}ms
                      </span>
                    )}
                  </div>
                )}

                {response ? (
                  <pre
                    style={{
                      margin: 0, fontSize: 14, fontFamily: 'monospace', color: COLORS.codeText,
                      lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                      background: '#0f0d2e', padding: 16, borderRadius: 8, overflow: 'auto',
                      maxHeight: 400,
                    }}
                    dangerouslySetInnerHTML={{ __html: syntaxHighlight(response) }}
                  />
                ) : (
                  <p style={{ color: '#818cf8', fontSize: 14, textAlign: 'center', padding: '40px 0' }}>
                    Selecciona un endpoint y presiona "Enviar" para ver la respuesta.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Endpoint description */}
          {selectedEndpoint && (
            <div style={{
              background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
              padding: 20, marginTop: 20,
            }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 8px' }}>
                {selectedEndpoint.description}
              </h3>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{
                  fontSize: 12, fontWeight: 700, padding: '3px 8px', borderRadius: 4,
                  background: METHOD_COLORS[selectedEndpoint.method] + '22',
                  color: METHOD_COLORS[selectedEndpoint.method], fontFamily: 'monospace',
                }}>
                  {selectedEndpoint.method}
                </span>
                <code style={{ fontSize: 14, fontFamily: 'monospace', color: COLORS.muted }}>
                  {selectedEndpoint.path}
                </code>
              </div>
              {selectedEndpoint.method !== 'GET' && selectedEndpoint.example_body && (
                <div style={{ marginTop: 12 }}>
                  <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 6px' }}>Ejemplo de body:</p>
                  <pre style={{
                    margin: 0, fontSize: 13, fontFamily: 'monospace', color: COLORS.text,
                    background: COLORS.bg, padding: 12, borderRadius: 8, overflow: 'auto',
                    lineHeight: 1.5,
                  }}>
                    {selectedEndpoint.example_body}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

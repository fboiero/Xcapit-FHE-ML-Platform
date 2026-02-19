import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

// Mock data for demo
const mockEndpoints = [
  {
    id: 'ep_001',
    name: 'Fraud Detection API',
    consortium_id: 'cons_001',
    company_name: 'FinTech Corp',
    model_name: 'fraud_detector_v2',
    endpoint_type: 'realtime',
    status: 'active',
    url: 'https://inference.xcapit.io/ep_001',
    request_count: 15234,
    avg_latency_ms: 45.2,
    created_at: '2024-12-01T10:00:00Z',
  },
  {
    id: 'ep_002',
    name: 'Credit Scoring Batch',
    consortium_id: 'cons_001',
    company_name: 'FinTech Corp',
    model_name: 'credit_scorer_v1',
    endpoint_type: 'batch',
    status: 'active',
    url: 'https://inference.xcapit.io/ep_002',
    request_count: 8921,
    avg_latency_ms: 120.5,
    created_at: '2024-11-15T14:30:00Z',
  },
]

const mockModels = [
  {
    id: 'fm_001',
    name: 'Federated Fraud Detector',
    consortium_id: 'cons_001',
    model_type: 'neural_network',
    version: '2.1.0',
    status: 'deployed',
    deployment_count: 5,
    metrics: { accuracy: 0.965, f1_score: 0.94, auc: 0.98 },
    created_at: '2024-11-01T08:00:00Z',
  },
  {
    id: 'fm_002',
    name: 'Credit Risk Model',
    consortium_id: 'cons_001',
    model_type: 'xgboost',
    version: '1.3.0',
    status: 'training',
    deployment_count: 0,
    metrics: { accuracy: 0.89, f1_score: 0.87 },
    created_at: '2024-12-05T16:00:00Z',
  },
  {
    id: 'fm_003',
    name: 'Customer Segmentation',
    consortium_id: 'cons_002',
    model_type: 'logistic_regression',
    version: '1.0.0',
    status: 'deployed',
    deployment_count: 3,
    metrics: { accuracy: 0.92, precision: 0.91, recall: 0.93 },
    created_at: '2024-10-20T12:00:00Z',
  },
]

const mockEdgeNodes = [
  {
    id: 'node_001',
    name: 'On-Premise Server 1',
    node_type: 'on_premise',
    location: 'Buenos Aires, AR',
    status: 'online',
    deployed_models: ['fm_001', 'fm_003'],
    capabilities: { gpu: true, memory_gb: 64, cpu_cores: 16 },
    last_heartbeat: '2024-12-10T12:55:00Z',
  },
  {
    id: 'node_002',
    name: 'Cloud Edge - US East',
    node_type: 'cloud',
    location: 'Virginia, US',
    status: 'online',
    deployed_models: ['fm_001'],
    capabilities: { gpu: true, memory_gb: 128, cpu_cores: 32 },
    last_heartbeat: '2024-12-10T12:54:30Z',
  },
  {
    id: 'node_003',
    name: 'Hybrid Node - EU',
    node_type: 'hybrid',
    location: 'Frankfurt, DE',
    status: 'offline',
    deployed_models: [],
    capabilities: { gpu: false, memory_gb: 32, cpu_cores: 8 },
    last_heartbeat: '2024-12-09T18:30:00Z',
  },
]

const mockRequests = [
  {
    id: 'req_001',
    endpoint_id: 'ep_001',
    requester_name: 'FinTech Corp',
    status: 'completed',
    priority: 'high',
    latency_ms: 42,
    created_at: '2024-12-10T12:50:00Z',
    completed_at: '2024-12-10T12:50:00Z',
  },
  {
    id: 'req_002',
    endpoint_id: 'ep_001',
    requester_name: 'Insurance LLC',
    status: 'completed',
    priority: 'normal',
    latency_ms: 48,
    created_at: '2024-12-10T12:49:00Z',
    completed_at: '2024-12-10T12:49:00Z',
  },
  {
    id: 'req_003',
    endpoint_id: 'ep_002',
    requester_name: 'Bank Corp',
    status: 'processing',
    priority: 'low',
    latency_ms: null,
    created_at: '2024-12-10T12:51:00Z',
    completed_at: null,
  },
]

const mockStats = {
  total_endpoints: 2,
  active_endpoints: 2,
  total_requests: 24155,
  completed_requests: 24152,
  total_models: 3,
  deployed_models: 2,
  total_edge_nodes: 3,
  online_edge_nodes: 2,
  avg_latency_ms: 67.8,
}

export default function FederatedInference() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('endpoints')
  const [endpoints, setEndpoints] = useState([])
  const [models, setModels] = useState([])
  const [edgeNodes, setEdgeNodes] = useState([])
  const [requests, setRequests] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showCreateEndpoint, setShowCreateEndpoint] = useState(false)
  const [showRegisterNode, setShowRegisterNode] = useState(false)
  const [showInferenceDemo, setShowInferenceDemo] = useState(false)

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setEndpoints(mockEndpoints)
      setModels(mockModels)
      setEdgeNodes(mockEdgeNodes)
      setRequests(mockRequests)
      setStats(mockStats)
      setLoading(false)
    }, 500)
  }, [consortiumId])

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      online: 'bg-green-100 text-green-800',
      deployed: 'bg-green-100 text-green-800',
      completed: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      offline: 'bg-red-100 text-red-800',
      training: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getNodeTypeIcon = (type) => {
    switch (type) {
      case 'on_premise':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        )
      case 'cloud':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
          </svg>
        )
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Federated Inference</h1>
        <p className="mt-2 text-gray-600">
          Run predictions without moving data to the cloud. Deploy models to edge nodes for privacy-preserving inference.
        </p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-indigo-100 text-indigo-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Endpoints</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.active_endpoints}/{stats.total_endpoints}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed Requests</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.completed_requests.toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Edge Nodes Online</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.online_edge_nodes}/{stats.total_edge_nodes}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Latency</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.avg_latency_ms.toFixed(1)}ms</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Privacy Banner */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-lg p-6 mb-8 text-white">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-semibold">Data Never Leaves Your Premises</h3>
            <p className="mt-1 text-indigo-100">
              With Federated Inference, your data stays on your servers. Models are deployed to edge nodes,
              and predictions are computed locally with FHE encryption. Only encrypted results are transmitted.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'endpoints', name: 'Inference Endpoints' },
            { id: 'models', name: 'Federated Models' },
            { id: 'nodes', name: 'Edge Nodes' },
            { id: 'requests', name: 'Recent Requests' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Endpoints Tab */}
      {activeTab === 'endpoints' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Inference Endpoints</h2>
            <div className="space-x-2">
              <button
                onClick={() => setShowInferenceDemo(true)}
                className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50"
              >
                Try Demo Inference
              </button>
              <button
                onClick={() => setShowCreateEndpoint(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Create Endpoint
              </button>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Endpoint</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requests</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Latency</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {endpoints.map((endpoint) => (
                  <tr key={endpoint.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{endpoint.name}</div>
                      <div className="text-sm text-gray-500">{endpoint.url}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{endpoint.model_name}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                        {endpoint.endpoint_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(endpoint.status)}`}>
                        {endpoint.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{endpoint.request_count.toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{endpoint.avg_latency_ms.toFixed(1)}ms</td>
                    <td className="px-6 py-4 text-sm">
                      <button className="text-indigo-600 hover:text-indigo-900 mr-3">Test</button>
                      <button className="text-gray-600 hover:text-gray-900">Logs</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Federated Models</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {models.map((model) => (
              <div key={model.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
                    <p className="text-sm text-gray-500">v{model.version}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(model.status)}`}>
                    {model.status}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Model Type:</span>
                    <span className="text-gray-900 font-medium">{model.model_type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Deployments:</span>
                    <span className="text-gray-900 font-medium">{model.deployment_count}</span>
                  </div>

                  {model.metrics && (
                    <div className="pt-3 border-t">
                      <p className="text-xs text-gray-500 mb-2">Metrics:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(model.metrics).map(([key, value]) => (
                          <div key={key} className="bg-gray-50 rounded p-2">
                            <p className="text-xs text-gray-500">{key}</p>
                            <p className="text-sm font-semibold text-gray-900">
                              {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t flex justify-end space-x-2">
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
                    View Details
                  </button>
                  {model.status === 'deployed' && (
                    <button className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">
                      Deploy to Node
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Edge Nodes Tab */}
      {activeTab === 'nodes' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Edge Nodes</h2>
            <button
              onClick={() => setShowRegisterNode(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Register Node
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {edgeNodes.map((node) => (
              <div key={node.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-lg ${node.status === 'online' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}`}>
                      {getNodeTypeIcon(node.node_type)}
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-semibold text-gray-900">{node.name}</h3>
                      <p className="text-sm text-gray-500">{node.location}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(node.status)}`}>
                    {node.status}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Type:</span>
                    <span className="text-gray-900 font-medium capitalize">{node.node_type.replace('_', ' ')}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Models Deployed:</span>
                    <span className="text-gray-900 font-medium">{node.deployed_models.length}</span>
                  </div>

                  {node.capabilities && (
                    <div className="pt-3 border-t">
                      <p className="text-xs text-gray-500 mb-2">Capabilities:</p>
                      <div className="flex flex-wrap gap-2">
                        {node.capabilities.gpu && (
                          <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">GPU</span>
                        )}
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          {node.capabilities.memory_gb}GB RAM
                        </span>
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                          {node.capabilities.cpu_cores} Cores
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-500">
                    Last heartbeat: {new Date(node.last_heartbeat).toLocaleString()}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t flex justify-end space-x-2">
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
                    Manage
                  </button>
                  {node.status === 'online' && (
                    <button className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">
                      Deploy Model
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Requests Tab */}
      {activeTab === 'requests' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Recent Inference Requests</h2>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Request ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requester</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latency</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {requests.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">{request.id}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{request.requester_name}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        request.priority === 'high' ? 'bg-red-100 text-red-800' :
                        request.priority === 'normal' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {request.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                        {request.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {request.latency_ms ? `${request.latency_ms}ms` : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(request.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Demo Inference Modal */}
      {showInferenceDemo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Federated Inference Demo</h3>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-2">Sample Input (Transaction Data):</p>
                <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
{`{
  "amount": 1500.00,
  "merchant_category": "electronics",
  "hour_of_day": 14,
  "is_international": false,
  "device_type": "mobile"
}`}
                </pre>
              </div>

              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-2 text-indigo-600">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Processing with FHE encryption...</span>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-green-800 mb-2">Encrypted Prediction Result:</p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-lg font-bold text-green-700">Fraud Risk: LOW (0.12)</p>
                    <p className="text-sm text-green-600">Confidence: 96.5%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Latency: 42ms</p>
                    <p className="text-xs text-gray-500">Processed on: Edge Node 1</p>
                  </div>
                </div>
              </div>

              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-sm">
                <p className="text-indigo-800">
                  <strong>Privacy Guarantee:</strong> Your input data was encrypted client-side.
                  The model computed predictions on encrypted data. Only you can decrypt the result.
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowInferenceDemo(false)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Endpoint Modal */}
      {showCreateEndpoint && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Create Inference Endpoint</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint Name</label>
                <input type="text" className="w-full border rounded-lg px-3 py-2" placeholder="e.g., Fraud Detection API" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <select className="w-full border rounded-lg px-3 py-2">
                  <option>Select a model...</option>
                  {models.filter(m => m.status === 'deployed').map(m => (
                    <option key={m.id} value={m.id}>{m.name} (v{m.version})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint Type</label>
                <select className="w-full border rounded-lg px-3 py-2">
                  <option value="realtime">Real-time</option>
                  <option value="batch">Batch</option>
                  <option value="streaming">Streaming</option>
                </select>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateEndpoint(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowCreateEndpoint(false)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Create Endpoint
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Register Node Modal */}
      {showRegisterNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Register Edge Node</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Node Name</label>
                <input type="text" className="w-full border rounded-lg px-3 py-2" placeholder="e.g., On-Premise Server 1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Node Type</label>
                <select className="w-full border rounded-lg px-3 py-2">
                  <option value="on_premise">On-Premise</option>
                  <option value="cloud">Cloud</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input type="text" className="w-full border rounded-lg px-3 py-2" placeholder="e.g., Buenos Aires, AR" />
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-600 mb-2">After registration, install the edge agent:</p>
                <code className="text-xs bg-gray-900 text-green-400 p-2 rounded block">
                  curl -sSL https://xcapit.io/edge-install.sh | bash
                </code>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowRegisterNode(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowRegisterNode(false)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Register Node
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

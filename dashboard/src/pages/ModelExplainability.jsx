import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

export default function ModelExplainability() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [explanations, setExplanations] = useState([])
  const [featureImportance, setFeatureImportance] = useState([])
  const [insights, setInsights] = useState(null)
  const [stats, setStats] = useState(null)
  const [showExplainModal, setShowExplainModal] = useState(false)
  const [explainForm, setExplainForm] = useState({
    explanation_type: 'feature_importance',
    input_data: ''
  })

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      // Mock explanations data
      setExplanations([
        {
          request_id: 'exp_001',
          explanation_type: 'feature_importance',
          status: 'completed',
          requester_id: 'company_a',
          created_at: '2024-12-10T10:30:00Z',
          result: {
            features: [
              { name: 'credit_score', importance: 0.35 },
              { name: 'income', importance: 0.28 },
              { name: 'debt_ratio', importance: 0.18 },
              { name: 'employment_years', importance: 0.12 },
              { name: 'age', importance: 0.07 }
            ]
          }
        },
        {
          request_id: 'exp_002',
          explanation_type: 'shap',
          status: 'completed',
          requester_id: 'company_b',
          created_at: '2024-12-10T11:15:00Z',
          result: {
            base_value: 0.42,
            shap_values: [
              { feature: 'credit_score', value: 0.15, direction: 'positive' },
              { feature: 'income', value: 0.08, direction: 'positive' },
              { feature: 'debt_ratio', value: -0.12, direction: 'negative' }
            ]
          }
        },
        {
          request_id: 'exp_003',
          explanation_type: 'decision_path',
          status: 'completed',
          requester_id: 'company_a',
          created_at: '2024-12-10T12:00:00Z',
          result: {
            path: [
              { node: 1, feature: 'credit_score', threshold: 650, direction: 'right' },
              { node: 3, feature: 'income', threshold: 50000, direction: 'left' },
              { node: 6, feature: 'debt_ratio', threshold: 0.3, direction: 'right' }
            ],
            prediction: 'approved',
            confidence: 0.87
          }
        },
        {
          request_id: 'exp_004',
          explanation_type: 'counterfactual',
          status: 'pending',
          requester_id: 'company_c',
          created_at: '2024-12-10T14:30:00Z'
        }
      ])

      // Mock feature importance
      setFeatureImportance([
        { name: 'credit_score', importance: 0.35, rank: 1 },
        { name: 'income', importance: 0.28, rank: 2 },
        { name: 'debt_ratio', importance: 0.18, rank: 3 },
        { name: 'employment_years', importance: 0.12, rank: 4 },
        { name: 'age', importance: 0.07, rank: 5 },
        { name: 'location', importance: 0.00, rank: 6 }
      ])

      // Mock insights
      setInsights({
        model_type: 'logistic_regression',
        model_complexity: 'medium',
        interpretability_score: 0.78,
        top_features: ['credit_score', 'income', 'debt_ratio'],
        feature_interactions: [
          { features: ['credit_score', 'income'], strength: 0.42 },
          { features: ['debt_ratio', 'employment_years'], strength: 0.28 }
        ],
        decision_boundaries: {
          primary: 'credit_score > 650 AND debt_ratio < 0.4',
          secondary: 'income > 40000 OR employment_years > 3'
        },
        bias_indicators: {
          age: 'low',
          location: 'none detected',
          gender: 'not included'
        }
      })

      // Mock stats
      setStats({
        total_explanations: 156,
        by_type: {
          feature_importance: 45,
          shap: 38,
          decision_path: 42,
          counterfactual: 21,
          summary: 10
        },
        avg_generation_time_ms: 234,
        models_explained: 8
      })

      setLoading(false)
    }, 800)
  }, [consortiumId])

  const handleRequestExplanation = () => {
    const newExplanation = {
      request_id: `exp_${Date.now()}`,
      explanation_type: explainForm.explanation_type,
      status: 'processing',
      requester_id: 'demo_company',
      created_at: new Date().toISOString()
    }
    setExplanations([newExplanation, ...explanations])
    setShowExplainModal(false)
    setExplainForm({ explanation_type: 'feature_importance', input_data: '' })

    // Simulate completion
    setTimeout(() => {
      setExplanations(prev => prev.map(e =>
        e.request_id === newExplanation.request_id
          ? { ...e, status: 'completed', result: { message: 'Explanation generated' } }
          : e
      ))
    }, 2000)
  }

  const getStatusBadge = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeIcon = (type) => {
    const icons = {
      feature_importance: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      shap: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
      ),
      decision_path: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
      counterfactual: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
      summary: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
    return icons[type] || icons.summary
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">Model Explainability</h1>
              <p className="mt-2 text-purple-100">
                Understand ML predictions without exposing training data
              </p>
            </div>
            <button
              onClick={() => setShowExplainModal(true)}
              className="bg-white text-purple-600 px-4 py-2 rounded-lg font-medium hover:bg-purple-50 transition-colors"
            >
              Request Explanation
            </button>
          </div>

          {/* Stats */}
          <div className="mt-8 grid grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{stats.total_explanations}</div>
              <div className="text-purple-200">Total Explanations</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{stats.models_explained}</div>
              <div className="text-purple-200">Models Explained</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{stats.avg_generation_time_ms}ms</div>
              <div className="text-purple-200">Avg Generation Time</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{Math.round(insights.interpretability_score * 100)}%</div>
              <div className="text-purple-200">Interpretability Score</div>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy Banner */}
      <div className="bg-purple-50 border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-purple-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-sm font-medium">
              Privacy Preserved: All explanations are derived from encrypted aggregate statistics - no individual training data is exposed
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="border-b border-gray-200">
          <nav className="flex gap-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'importance', label: 'Feature Importance' },
              { id: 'explanations', label: 'Explanations' },
              { id: 'insights', label: 'Model Insights' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Explanation Types */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Available Explanation Types</h2>
              <div className="grid grid-cols-5 gap-4">
                {Object.entries(stats.by_type).map(([type, count]) => (
                  <div key={type} className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-center mb-2 text-purple-600">
                      {getTypeIcon(type)}
                    </div>
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-sm text-gray-500 capitalize">
                      {type.replace('_', ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Feature Importance */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Top Features Impact</h2>
              <div className="space-y-3">
                {featureImportance.slice(0, 5).map((feature) => (
                  <div key={feature.name} className="flex items-center gap-4">
                    <div className="w-32 text-sm font-medium text-gray-700">
                      {feature.name}
                    </div>
                    <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
                        style={{ width: `${feature.importance * 100}%` }}
                      />
                    </div>
                    <div className="w-16 text-right text-sm text-gray-600">
                      {(feature.importance * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Explanations */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Recent Explanations</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 font-medium">Type</th>
                      <th className="pb-3 font-medium">Requester</th>
                      <th className="pb-3 font-medium">Status</th>
                      <th className="pb-3 font-medium">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {explanations.slice(0, 5).map((exp) => (
                      <tr key={exp.request_id} className="border-b last:border-0">
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-purple-600">{getTypeIcon(exp.explanation_type)}</span>
                            <span className="capitalize">{exp.explanation_type.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="py-3 text-gray-600">{exp.requester_id}</td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(exp.status)}`}>
                            {exp.status}
                          </span>
                        </td>
                        <td className="py-3 text-gray-500 text-sm">
                          {new Date(exp.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Feature Importance Tab */}
        {activeTab === 'importance' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-6">Global Feature Importance</h2>
              <div className="space-y-4">
                {featureImportance.map((feature) => (
                  <div key={feature.name} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                    <div className="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold">
                      {feature.rank}
                    </div>
                    <div className="w-40 font-medium">{feature.name}</div>
                    <div className="flex-1">
                      <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${feature.importance * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-20 text-right font-mono text-lg">
                      {(feature.importance * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-6 text-sm text-gray-500">
                Feature importance scores are calculated using permutation importance on encrypted aggregate predictions.
                No individual data points are exposed in this analysis.
              </p>
            </div>

            {/* Feature Interactions */}
            {insights?.feature_interactions && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-lg font-semibold mb-4">Feature Interactions</h2>
                <div className="space-y-3">
                  {insights.feature_interactions.map((interaction, idx) => (
                    <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm font-medium">
                          {interaction.features[0]}
                        </span>
                        <span className="text-gray-400">x</span>
                        <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-sm font-medium">
                          {interaction.features[1]}
                        </span>
                      </div>
                      <div className="flex-1 h-2 bg-gray-200 rounded-full">
                        <div
                          className="h-full bg-gradient-to-r from-purple-400 to-indigo-400 rounded-full"
                          style={{ width: `${interaction.strength * 100}%` }}
                        />
                      </div>
                      <div className="text-sm font-medium text-gray-600">
                        {(interaction.strength * 100).toFixed(0)}% interaction
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Explanations Tab */}
        {activeTab === 'explanations' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="p-4 border-b flex justify-between items-center">
                <h2 className="text-lg font-semibold">All Explanation Requests</h2>
                <button
                  onClick={() => setShowExplainModal(true)}
                  className="text-purple-600 hover:text-purple-700 font-medium text-sm"
                >
                  + New Request
                </button>
              </div>
              <div className="divide-y">
                {explanations.map((exp) => (
                  <div key={exp.request_id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                          {getTypeIcon(exp.explanation_type)}
                        </div>
                        <div>
                          <div className="font-medium capitalize">
                            {exp.explanation_type.replace('_', ' ')} Explanation
                          </div>
                          <div className="text-sm text-gray-500">
                            Request ID: {exp.request_id}
                          </div>
                          <div className="text-sm text-gray-500">
                            By {exp.requester_id} on {new Date(exp.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(exp.status)}`}>
                        {exp.status}
                      </span>
                    </div>

                    {/* Show result if completed */}
                    {exp.status === 'completed' && exp.result && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        {exp.explanation_type === 'feature_importance' && exp.result.features && (
                          <div className="space-y-2">
                            {exp.result.features.slice(0, 3).map((f, i) => (
                              <div key={i} className="flex items-center gap-2 text-sm">
                                <span className="font-medium">{f.name}:</span>
                                <span className="text-gray-600">{(f.importance * 100).toFixed(1)}%</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {exp.explanation_type === 'shap' && exp.result.shap_values && (
                          <div className="space-y-2">
                            <div className="text-sm">
                              <span className="font-medium">Base value:</span> {exp.result.base_value}
                            </div>
                            {exp.result.shap_values.map((sv, i) => (
                              <div key={i} className="flex items-center gap-2 text-sm">
                                <span className={sv.direction === 'positive' ? 'text-green-600' : 'text-red-600'}>
                                  {sv.direction === 'positive' ? '+' : ''}{sv.value.toFixed(3)}
                                </span>
                                <span className="text-gray-600">{sv.feature}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {exp.explanation_type === 'decision_path' && exp.result.path && (
                          <div className="space-y-2">
                            <div className="text-sm font-medium">
                              Prediction: {exp.result.prediction} ({(exp.result.confidence * 100).toFixed(0)}% confidence)
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              {exp.result.path.map((step, i) => (
                                <span key={i} className="flex items-center gap-1">
                                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                                    {step.feature} {step.direction === 'right' ? '>' : '<='} {step.threshold}
                                  </span>
                                  {i < exp.result.path.length - 1 && (
                                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                  )}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Model Insights Tab */}
        {activeTab === 'insights' && insights && (
          <div className="space-y-6">
            {/* Model Summary */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Model Summary</h2>
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <div className="text-sm text-gray-500">Model Type</div>
                  <div className="text-lg font-medium capitalize">{insights.model_type.replace('_', ' ')}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Complexity</div>
                  <div className="text-lg font-medium capitalize">{insights.model_complexity}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Interpretability</div>
                  <div className="text-lg font-medium">{(insights.interpretability_score * 100).toFixed(0)}%</div>
                </div>
              </div>
            </div>

            {/* Decision Boundaries */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Decision Logic (Simplified)</h2>
              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="text-sm text-green-600 font-medium mb-1">Primary Rule</div>
                  <code className="text-green-800">{insights.decision_boundaries.primary}</code>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-sm text-blue-600 font-medium mb-1">Secondary Rule</div>
                  <code className="text-blue-800">{insights.decision_boundaries.secondary}</code>
                </div>
              </div>
              <p className="mt-4 text-sm text-gray-500">
                These rules represent a simplified approximation of the model's decision process.
                The actual model may use more complex combinations of features.
              </p>
            </div>

            {/* Bias Analysis */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Fairness Indicators</h2>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(insights.bias_indicators).map(([feature, status]) => (
                  <div key={feature} className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-medium capitalize mb-1">{feature}</div>
                    <div className={`text-sm ${
                      status === 'none detected' || status === 'not included'
                        ? 'text-green-600'
                        : status === 'low'
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }`}>
                      {status}
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm text-gray-500">
                Bias indicators are computed on aggregate encrypted data to preserve privacy while
                detecting potential fairness issues.
              </p>
            </div>

            {/* Top Contributing Features */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Key Decision Factors</h2>
              <div className="flex gap-3">
                {insights.top_features.map((feature, idx) => (
                  <div
                    key={feature}
                    className={`px-4 py-2 rounded-full font-medium ${
                      idx === 0
                        ? 'bg-purple-100 text-purple-700'
                        : idx === 1
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    #{idx + 1} {feature}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Request Explanation Modal */}
      {showExplainModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Request New Explanation</h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Explanation Type
                </label>
                <select
                  value={explainForm.explanation_type}
                  onChange={(e) => setExplainForm({ ...explainForm, explanation_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="feature_importance">Feature Importance</option>
                  <option value="shap">SHAP Values</option>
                  <option value="decision_path">Decision Path</option>
                  <option value="counterfactual">Counterfactual</option>
                  <option value="summary">Model Summary</option>
                </select>
              </div>

              {(explainForm.explanation_type === 'shap' ||
                explainForm.explanation_type === 'decision_path' ||
                explainForm.explanation_type === 'counterfactual') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Input Data (JSON)
                  </label>
                  <textarea
                    value={explainForm.input_data}
                    onChange={(e) => setExplainForm({ ...explainForm, input_data: e.target.value })}
                    placeholder='{"credit_score": 720, "income": 55000, ...}'
                    rows={4}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                  />
                </div>
              )}

              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-purple-700">
                    Explanations are generated using privacy-preserving techniques.
                    No training data will be exposed.
                  </p>
                </div>
              </div>
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-xl">
              <button
                onClick={() => setShowExplainModal(false)}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={handleRequestExplanation}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Request Explanation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

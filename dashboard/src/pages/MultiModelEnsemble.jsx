import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

export default function MultiModelEnsemble() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('ensembles')
  const [loading, setLoading] = useState(true)
  const [ensembles, setEnsembles] = useState([])
  const [selectedEnsemble, setSelectedEnsemble] = useState(null)
  const [stats, setStats] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showPredictModal, setShowPredictModal] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    ensemble_type: 'voting'
  })
  const [predictForm, setPredictForm] = useState('')
  const [prediction, setPrediction] = useState(null)

  useEffect(() => {
    setTimeout(() => {
      // Mock ensembles
      setEnsembles([
        {
          id: 'ens_001',
          name: 'Fraud Detection Ensemble',
          description: 'Combines fraud detection models from 3 financial consortiums',
          ensemble_type: 'voting',
          status: 'active',
          model_count: 3,
          created_at: '2024-12-08',
          models: [
            { model_id: 'model_a1', consortium_id: 'cons_bank_1', model_type: 'logistic_regression', weight: 1.0 },
            { model_id: 'model_b2', consortium_id: 'cons_bank_2', model_type: 'decision_tree', weight: 1.2 },
            { model_id: 'model_c3', consortium_id: 'cons_fintech', model_type: 'logistic_regression', weight: 0.8 }
          ],
          performance: {
            total_predictions: 1250,
            avg_confidence: 0.87,
            avg_latency_ms: 45
          }
        },
        {
          id: 'ens_002',
          name: 'Credit Risk Weighted',
          description: 'Weighted ensemble for credit risk assessment',
          ensemble_type: 'weighted',
          status: 'active',
          model_count: 4,
          created_at: '2024-12-09',
          models: [
            { model_id: 'model_d1', consortium_id: 'cons_credit_1', model_type: 'linear_regression', weight: 1.5 },
            { model_id: 'model_e2', consortium_id: 'cons_credit_2', model_type: 'logistic_regression', weight: 1.0 },
            { model_id: 'model_f3', consortium_id: 'cons_credit_3', model_type: 'decision_tree', weight: 0.8 },
            { model_id: 'model_g4', consortium_id: 'cons_bank_1', model_type: 'logistic_regression', weight: 1.2 }
          ],
          performance: {
            total_predictions: 890,
            avg_confidence: 0.82,
            avg_latency_ms: 62
          }
        },
        {
          id: 'ens_003',
          name: 'Healthcare Diagnosis',
          description: 'Averaging ensemble for diagnostic predictions',
          ensemble_type: 'averaging',
          status: 'draft',
          model_count: 2,
          created_at: '2024-12-10',
          models: [
            { model_id: 'model_h1', consortium_id: 'cons_hospital_1', model_type: 'logistic_regression', weight: 1.0 },
            { model_id: 'model_i2', consortium_id: 'cons_clinic_1', model_type: 'decision_tree', weight: 1.0 }
          ],
          performance: {
            total_predictions: 0,
            avg_confidence: 0,
            avg_latency_ms: 0
          }
        }
      ])

      // Mock stats
      setStats({
        total_ensembles: 3,
        active_ensembles: 2,
        total_models_in_ensembles: 9,
        total_predictions: 2140,
        by_type: {
          voting: 1,
          weighted: 1,
          averaging: 1
        }
      })

      setLoading(false)
    }, 600)
  }, [])

  const handleCreateEnsemble = () => {
    const newEnsemble = {
      id: `ens_${Date.now()}`,
      name: createForm.name,
      description: createForm.description,
      ensemble_type: createForm.ensemble_type,
      status: 'draft',
      model_count: 0,
      created_at: new Date().toISOString().split('T')[0],
      models: [],
      performance: { total_predictions: 0, avg_confidence: 0, avg_latency_ms: 0 }
    }
    setEnsembles([newEnsemble, ...ensembles])
    setShowCreateModal(false)
    setCreateForm({ name: '', description: '', ensemble_type: 'voting' })
  }

  const handlePredict = () => {
    // Simulate prediction
    setTimeout(() => {
      const models = selectedEnsemble.models.map(m => ({
        ...m,
        prediction: Math.random().toFixed(4)
      }))

      const avgPred = models.reduce((acc, m) => acc + parseFloat(m.prediction), 0) / models.length

      setPrediction({
        prediction: avgPred.toFixed(4),
        confidence: (0.75 + Math.random() * 0.2).toFixed(4),
        models_used: models.length,
        model_predictions: models,
        latency_ms: (20 + Math.random() * 40).toFixed(1)
      })
    }, 500)
  }

  const getStatusBadge = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-yellow-100 text-yellow-800',
      inactive: 'bg-gray-100 text-gray-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeIcon = (type) => {
    const icons = {
      voting: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      averaging: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      weighted: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
        </svg>
      ),
      stacking: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      boosting: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
    }
    return icons[type] || icons.voting
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">Multi-Model Ensemble</h1>
              <p className="mt-2 text-orange-100">
                Combine models from multiple consortiums for enhanced predictions
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-white text-orange-600 px-4 py-2 rounded-lg font-medium hover:bg-orange-50 transition-colors"
            >
              Create Ensemble
            </button>
          </div>

          {/* Stats */}
          {stats && (
            <div className="mt-8 grid grid-cols-4 gap-4">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{stats.total_ensembles}</div>
                <div className="text-orange-200">Total Ensembles</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{stats.active_ensembles}</div>
                <div className="text-orange-200">Active</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{stats.total_models_in_ensembles}</div>
                <div className="text-orange-200">Models Combined</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{stats.total_predictions.toLocaleString()}</div>
                <div className="text-orange-200">Total Predictions</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Privacy Banner */}
      <div className="bg-orange-50 border-b border-orange-100">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-orange-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-sm font-medium">
              Each model's training data remains encrypted - only combined predictions are shared
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="border-b border-gray-200">
          <nav className="flex gap-8">
            {[
              { id: 'ensembles', label: 'Ensembles' },
              { id: 'types', label: 'Ensemble Types' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-orange-600 text-orange-600'
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
        {/* Ensembles Tab */}
        {activeTab === 'ensembles' && (
          <div className="space-y-6">
            {ensembles.map(ensemble => (
              <div key={ensemble.id} className="bg-white rounded-xl shadow-sm border overflow-hidden">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-orange-100 text-orange-600 rounded-lg">
                        {getTypeIcon(ensemble.ensemble_type)}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{ensemble.name}</h3>
                        <p className="text-gray-500 text-sm">{ensemble.description}</p>
                        <div className="flex items-center gap-4 mt-2 text-sm">
                          <span className="text-gray-500">Type: <span className="capitalize font-medium">{ensemble.ensemble_type}</span></span>
                          <span className="text-gray-500">Models: <span className="font-medium">{ensemble.model_count}</span></span>
                          <span className="text-gray-500">Created: {ensemble.created_at}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(ensemble.status)}`}>
                        {ensemble.status}
                      </span>
                      {ensemble.status === 'active' && (
                        <button
                          onClick={() => {
                            setSelectedEnsemble(ensemble)
                            setShowPredictModal(true)
                          }}
                          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
                        >
                          Predict
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Models in ensemble */}
                  <div className="mt-4 pt-4 border-t">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Member Models</h4>
                    <div className="grid grid-cols-4 gap-3">
                      {ensemble.models.map((m, idx) => (
                        <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-500">{m.consortium_id}</span>
                            {ensemble.ensemble_type === 'weighted' && (
                              <span className="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded">
                                w: {m.weight}
                              </span>
                            )}
                          </div>
                          <div className="font-medium text-sm">{m.model_type.replace('_', ' ')}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Performance stats */}
                  {ensemble.status === 'active' && (
                    <div className="mt-4 pt-4 border-t flex gap-8">
                      <div>
                        <span className="text-sm text-gray-500">Predictions:</span>
                        <span className="ml-2 font-semibold">{ensemble.performance.total_predictions.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Avg Confidence:</span>
                        <span className="ml-2 font-semibold">{(ensemble.performance.avg_confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Avg Latency:</span>
                        <span className="ml-2 font-semibold">{ensemble.performance.avg_latency_ms}ms</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Types Tab */}
        {activeTab === 'types' && (
          <div className="grid grid-cols-2 gap-6">
            {[
              { type: 'voting', name: 'Voting', desc: 'Majority vote for classification tasks. Each model votes, final prediction is the majority.', best: 'Classification with multiple models' },
              { type: 'averaging', name: 'Averaging', desc: 'Simple average of all predictions. Works well when models have similar accuracy.', best: 'Regression, probability estimation' },
              { type: 'weighted', name: 'Weighted', desc: 'Weighted average based on model confidence or performance. Better models contribute more.', best: 'When model quality varies' },
              { type: 'stacking', name: 'Stacking', desc: 'Meta-learner combines model outputs. Trains a new model on ensemble predictions.', best: 'Complex prediction tasks' },
              { type: 'boosting', name: 'Boosting', desc: 'Sequential combination where each model learns from previous errors.', best: 'Improving weak learners' }
            ].map(t => (
              <div key={t.type} className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-orange-100 text-orange-600 rounded-lg">
                    {getTypeIcon(t.type)}
                  </div>
                  <h3 className="text-lg font-semibold">{t.name}</h3>
                </div>
                <p className="text-gray-600 mb-4">{t.desc}</p>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <span className="text-sm font-medium text-orange-700">Best for:</span>
                  <span className="ml-2 text-sm text-orange-600">{t.best}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Ensemble Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Create New Ensemble</h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ensemble Name
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="e.g., Fraud Detection Ensemble"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Describe the purpose of this ensemble..."
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ensemble Type
                </label>
                <select
                  value={createForm.ensemble_type}
                  onChange={(e) => setCreateForm({ ...createForm, ensemble_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
                >
                  <option value="voting">Voting</option>
                  <option value="averaging">Averaging</option>
                  <option value="weighted">Weighted</option>
                  <option value="stacking">Stacking</option>
                  <option value="boosting">Boosting</option>
                </select>
              </div>
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-xl">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateEnsemble}
                disabled={!createForm.name}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
              >
                Create Ensemble
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Predict Modal */}
      {showPredictModal && selectedEnsemble && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Ensemble Prediction</h3>
              <p className="text-sm text-gray-500">{selectedEnsemble.name}</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Input Data (JSON)
                </label>
                <textarea
                  value={predictForm}
                  onChange={(e) => setPredictForm(e.target.value)}
                  placeholder='{"feature1": 0.5, "feature2": 100, ...}'
                  rows={4}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 font-mono text-sm"
                />
              </div>

              {prediction && (
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="font-semibold text-green-700 mb-3">Ensemble Result</h4>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <div className="text-2xl font-bold text-green-600">{prediction.prediction}</div>
                      <div className="text-sm text-gray-500">Prediction</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{(prediction.confidence * 100).toFixed(0)}%</div>
                      <div className="text-sm text-gray-500">Confidence</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{prediction.latency_ms}ms</div>
                      <div className="text-sm text-gray-500">Latency</div>
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Model Predictions:</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {prediction.model_predictions.map((mp, idx) => (
                        <span key={idx} className="px-2 py-1 bg-white rounded text-xs">
                          {mp.model_type}: {mp.prediction}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-xl">
              <button
                onClick={() => {
                  setShowPredictModal(false)
                  setPrediction(null)
                  setPredictForm('')
                }}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Close
              </button>
              <button
                onClick={handlePredict}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                Run Prediction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  BeakerIcon,
  PlusIcon,
  PlayIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  CircleStackIcon,
  CpuChipIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  SparklesIcon,
  TableCellsIcon,
  EyeIcon,
  RocketLaunchIcon,
  ShieldExclamationIcon,
  BanknotesIcon,
  HeartIcon,
  ShoppingBagIcon,
  Cog6ToothIcon,
  LockClosedIcon,
} from '@heroicons/react/24/outline'

// Industry configuration
const IndustryConfig = {
  fraud: {
    name: 'Fraud Detection',
    icon: ShieldExclamationIcon,
    color: 'red',
    bgColor: 'bg-red-50',
    textColor: 'text-red-600',
  },
  credit: {
    name: 'Credit Scoring',
    icon: BanknotesIcon,
    color: 'green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-600',
  },
  health: {
    name: 'Healthcare',
    icon: HeartIcon,
    color: 'pink',
    bgColor: 'bg-pink-50',
    textColor: 'text-pink-600',
  },
  retail: {
    name: 'Retail',
    icon: ShoppingBagIcon,
    color: 'purple',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
  },
  general: {
    name: 'General',
    icon: BeakerIcon,
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
  },
}

// Status configuration
const StatusConfig = {
  pending: { label: 'Pendiente', color: 'text-gray-600', bgColor: 'bg-gray-100', icon: ClockIcon },
  running: { label: 'Ejecutando', color: 'text-blue-600', bgColor: 'bg-blue-100', icon: ArrowPathIcon },
  completed: { label: 'Completado', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircleIcon },
  failed: { label: 'Fallido', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircleIcon },
}

// Mock templates
const MOCK_TEMPLATES = [
  {
    id: 'tpl_fraud_basic',
    name: 'Fraud Detection Starter',
    description: 'Ambiente basico para detectar fraudes en transacciones financieras',
    industry: 'fraud',
    template_type: 'starter',
    datasets: [
      { type: 'transactions', records: 10000, fraud_rate: 0.02 },
      { type: 'accounts', records: 1000 }
    ],
    experiments: [
      { type: 'training', model: 'logistic_regression' },
      { type: 'evaluation', metrics: ['accuracy', 'precision', 'recall'] }
    ]
  },
  {
    id: 'tpl_credit_basic',
    name: 'Credit Scoring Starter',
    description: 'Ambiente para construir modelos de scoring crediticio',
    industry: 'credit',
    template_type: 'starter',
    datasets: [
      { type: 'applications', records: 5000, default_rate: 0.15 },
      { type: 'payments', records: 50000 }
    ],
    experiments: [
      { type: 'training', model: 'decision_tree' },
      { type: 'evaluation', metrics: ['auc', 'gini', 'ks'] }
    ]
  },
  {
    id: 'tpl_health_basic',
    name: 'Healthcare Analytics Starter',
    description: 'Ambiente para analisis de datos clinicos y prediccion',
    industry: 'health',
    template_type: 'starter',
    datasets: [
      { type: 'patients', records: 2000 },
      { type: 'diagnoses', records: 8000 },
      { type: 'lab_results', records: 20000 }
    ],
    experiments: [
      { type: 'training', model: 'logistic_regression' },
      { type: 'clustering', model: 'kmeans' }
    ]
  },
  {
    id: 'tpl_retail_basic',
    name: 'Retail Analytics Starter',
    description: 'Ambiente para analisis de clientes y prediccion de churn',
    industry: 'retail',
    template_type: 'starter',
    datasets: [
      { type: 'customers', records: 5000 },
      { type: 'transactions', records: 100000 },
      { type: 'products', records: 500 }
    ],
    experiments: [
      { type: 'segmentation', model: 'kmeans' },
      { type: 'churn_prediction', model: 'logistic_regression' }
    ]
  },
  {
    id: 'tpl_advanced_fhe',
    name: 'FHE Advanced Workshop',
    description: 'Ambiente avanzado para experimentar con encriptacion homomorfica',
    industry: 'general',
    template_type: 'advanced',
    datasets: [
      { type: 'numeric', records: 1000, features: 20 },
      { type: 'encrypted_sample', records: 100 }
    ],
    experiments: [
      { type: 'encryption_benchmark' },
      { type: 'training_encrypted' },
      { type: 'inference_encrypted' }
    ]
  }
]

// Mock sandbox
const MOCK_SANDBOX = {
  id: 'sandbox_demo123',
  name: 'Mi Sandbox de Prueba',
  description: 'Ambiente para probar modelos de deteccion de fraude',
  owner_name: 'Mi Empresa',
  template_type: 'starter',
  industry: 'fraud',
  status: 'active',
  created_at: '2024-12-08T10:00:00Z',
  expires_at: '2024-12-15T10:00:00Z',
  dataset_count: 2,
  experiment_count: 3,
}

// Mock datasets
const MOCK_DATASETS = [
  {
    id: 'ds_001',
    name: 'Sample Transactions',
    dataset_type: 'transactions',
    record_count: 10000,
    feature_count: 7,
    features: [
      { name: 'transaction_id', type: 'string', description: 'Unique transaction ID' },
      { name: 'amount', type: 'float', description: 'Transaction amount' },
      { name: 'merchant_category', type: 'category', description: 'Merchant category' },
      { name: 'time_of_day', type: 'integer', description: 'Hour of day' },
      { name: 'day_of_week', type: 'integer', description: 'Day of week' },
      { name: 'is_international', type: 'boolean', description: 'International transaction' },
      { name: 'is_fraud', type: 'boolean', description: 'Fraud label' }
    ],
    statistics: { fraud_rate: 0.02, avg_amount: 150.50, max_amount: 5000.00 },
    data_preview: [
      { transaction_id: 'txn_abc123', amount: 125.50, merchant_category: 'retail', time_of_day: 14, day_of_week: 2, is_international: false, is_fraud: false },
      { transaction_id: 'txn_def456', amount: 2500.00, merchant_category: 'travel', time_of_day: 3, day_of_week: 6, is_international: true, is_fraud: true },
      { transaction_id: 'txn_ghi789', amount: 45.00, merchant_category: 'food', time_of_day: 12, day_of_week: 1, is_international: false, is_fraud: false },
    ],
    created_at: '2024-12-08T10:05:00Z',
  },
  {
    id: 'ds_002',
    name: 'Sample Accounts',
    dataset_type: 'accounts',
    record_count: 1000,
    feature_count: 5,
    features: [
      { name: 'account_id', type: 'string', description: 'Account ID' },
      { name: 'age', type: 'integer', description: 'Account age in months' },
      { name: 'balance', type: 'float', description: 'Current balance' },
      { name: 'status', type: 'category', description: 'Account status' },
      { name: 'risk_score', type: 'float', description: 'Risk score' }
    ],
    statistics: { avg_balance: 5000, avg_age: 24 },
    data_preview: [
      { account_id: 'acc_001', age: 36, balance: 12500.00, status: 'active', risk_score: 0.15 },
      { account_id: 'acc_002', age: 12, balance: 3200.00, status: 'active', risk_score: 0.35 },
    ],
    created_at: '2024-12-08T10:06:00Z',
  }
]

// Mock experiments
const MOCK_EXPERIMENTS = [
  {
    id: 'exp_001',
    name: 'Training Fraud Model',
    experiment_type: 'training',
    model_type: 'logistic_regression',
    dataset_id: 'ds_001',
    dataset_name: 'Sample Transactions',
    status: 'completed',
    config: { learning_rate: 0.01, epochs: 100 },
    results: {
      status: 'success',
      epochs: 100,
      training_time_seconds: 12.5,
      final_loss: 0.234,
      metrics: { accuracy: 0.923, precision: 0.867, recall: 0.812, f1_score: 0.839 }
    },
    created_at: '2024-12-08T10:10:00Z',
    completed_at: '2024-12-08T10:12:00Z',
  },
  {
    id: 'exp_002',
    name: 'Model Evaluation',
    experiment_type: 'evaluation',
    model_type: 'logistic_regression',
    dataset_id: 'ds_001',
    dataset_name: 'Sample Transactions',
    status: 'completed',
    config: { test_split: 0.2 },
    results: {
      status: 'success',
      metrics: { accuracy: 0.912, auc: 0.945, precision: 0.856, recall: 0.798 },
      confusion_matrix: { true_positive: 890, true_negative: 920, false_positive: 80, false_negative: 110 }
    },
    created_at: '2024-12-08T10:15:00Z',
    completed_at: '2024-12-08T10:16:00Z',
  },
  {
    id: 'exp_003',
    name: 'FHE Benchmark',
    experiment_type: 'encryption_benchmark',
    status: 'pending',
    config: {},
    results: {},
    created_at: '2024-12-08T10:20:00Z',
  }
]

// Mock stats
const MOCK_STATS = {
  total_sandboxes: 3,
  active_sandboxes: 2,
  total_datasets: 8,
  total_experiments: 15,
  completed_experiments: 12,
}

function TemplateCard({ template, onSelect }) {
  const config = IndustryConfig[template.industry] || IndustryConfig.general
  const Icon = config.icon

  return (
    <button
      onClick={() => onSelect(template)}
      className="w-full bg-white rounded-xl border p-5 hover:shadow-lg hover:border-brand-300 transition text-left group"
    >
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl ${config.bgColor} flex items-center justify-center group-hover:scale-110 transition`}>
          <Icon className={`w-6 h-6 ${config.textColor}`} />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
          <p className="text-sm text-gray-500 mb-3">{template.description}</p>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <CircleStackIcon className="w-4 h-4" />
              {template.datasets.length} datasets
            </span>
            <span className="flex items-center gap-1">
              <BeakerIcon className="w-4 h-4" />
              {template.experiments.length} experimentos
            </span>
          </div>
        </div>
      </div>
    </button>
  )
}

function DatasetCard({ dataset, onView, onDelete }) {
  return (
    <div className="bg-white rounded-xl border p-5 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
            <CircleStackIcon className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{dataset.name}</h4>
            <span className="text-xs text-gray-500">{dataset.dataset_type}</span>
          </div>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => onView(dataset)}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
            title="Ver detalles"
          >
            <EyeIcon className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={() => onDelete(dataset.id)}
            className="p-2 hover:bg-red-50 rounded-lg transition"
            title="Eliminar"
          >
            <TrashIcon className="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center bg-gray-50 rounded-lg p-3">
        <div>
          <div className="text-lg font-bold text-gray-900">{dataset.record_count.toLocaleString()}</div>
          <div className="text-xs text-gray-500">Registros</div>
        </div>
        <div>
          <div className="text-lg font-bold text-gray-900">{dataset.feature_count}</div>
          <div className="text-xs text-gray-500">Features</div>
        </div>
        <div>
          <div className="text-lg font-bold text-gray-900">{dataset.data_preview?.length || 0}</div>
          <div className="text-xs text-gray-500">Preview</div>
        </div>
      </div>
    </div>
  )
}

function ExperimentCard({ experiment, onRun, onView, onDelete }) {
  const statusConfig = StatusConfig[experiment.status] || StatusConfig.pending
  const StatusIcon = statusConfig.icon

  return (
    <div className="bg-white rounded-xl border p-5 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <BeakerIcon className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{experiment.name}</h4>
            <span className="text-xs text-gray-500">{experiment.experiment_type}</span>
          </div>
        </div>
        <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
          <StatusIcon className={`w-3 h-3 ${experiment.status === 'running' ? 'animate-spin' : ''}`} />
          {statusConfig.label}
        </span>
      </div>

      {experiment.model_type && (
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <CpuChipIcon className="w-4 h-4" />
          {experiment.model_type}
          {experiment.dataset_name && (
            <>
              <span className="text-gray-300">|</span>
              <CircleStackIcon className="w-4 h-4" />
              {experiment.dataset_name}
            </>
          )}
        </div>
      )}

      {experiment.status === 'completed' && experiment.results?.metrics && (
        <div className="grid grid-cols-2 gap-2 bg-green-50 rounded-lg p-3 mb-3">
          {Object.entries(experiment.results.metrics).slice(0, 4).map(([key, value]) => (
            <div key={key} className="text-center">
              <div className="text-sm font-bold text-green-700">{(value * 100).toFixed(1)}%</div>
              <div className="text-xs text-green-600">{key}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end gap-2">
        {experiment.status === 'pending' && (
          <button
            onClick={() => onRun(experiment.id)}
            className="flex items-center gap-1 px-3 py-1.5 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 transition"
          >
            <PlayIcon className="w-4 h-4" />
            Ejecutar
          </button>
        )}
        {experiment.status === 'completed' && (
          <button
            onClick={() => onView(experiment)}
            className="flex items-center gap-1 px-3 py-1.5 border text-sm rounded-lg hover:bg-gray-50 transition"
          >
            <ChartBarIcon className="w-4 h-4" />
            Ver Resultados
          </button>
        )}
        <button
          onClick={() => onDelete(experiment.id)}
          className="p-1.5 hover:bg-red-50 rounded-lg transition"
          title="Eliminar"
        >
          <TrashIcon className="w-4 h-4 text-red-500" />
        </button>
      </div>
    </div>
  )
}

function DatasetDetailModal({ dataset, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center">
              <CircleStackIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{dataset.name}</h2>
              <span className="text-sm text-gray-500">{dataset.dataset_type} - {dataset.record_count.toLocaleString()} registros</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <XCircleIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Features */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">Features ({dataset.feature_count})</h3>
            <div className="grid gap-2">
              {dataset.features?.map((feature, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">{feature.type}</span>
                  <span className="font-medium text-gray-900">{feature.name}</span>
                  <span className="text-sm text-gray-500">{feature.description}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Statistics */}
          {dataset.statistics && Object.keys(dataset.statistics).length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Estadisticas</h3>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(dataset.statistics).map(([key, value]) => (
                  <div key={key} className="p-3 bg-blue-50 rounded-lg text-center">
                    <div className="text-lg font-bold text-blue-700">
                      {typeof value === 'number' ? value.toLocaleString() : value}
                    </div>
                    <div className="text-xs text-blue-600">{key.replace(/_/g, ' ')}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Preview */}
          {dataset.data_preview && dataset.data_preview.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Preview de Datos</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      {Object.keys(dataset.data_preview[0]).map((key) => (
                        <th key={key} className="px-3 py-2 text-left text-xs font-medium text-gray-500">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {dataset.data_preview.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {Object.values(row).map((value, j) => (
                          <td key={j} className="px-3 py-2 text-gray-700">
                            {typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

function ExperimentResultsModal({ experiment, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">{experiment.name}</h2>
          <span className="text-sm text-gray-500">{experiment.experiment_type}</span>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {experiment.results && (
            <>
              {/* Status */}
              <div className="flex items-center gap-2 mb-4">
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                <span className="font-medium text-green-700">Completado exitosamente</span>
              </div>

              {/* Metrics */}
              {experiment.results.metrics && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Metricas</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(experiment.results.metrics).map(([key, value]) => (
                      <div key={key} className="p-4 bg-green-50 rounded-lg text-center">
                        <div className="text-2xl font-bold text-green-700">{(value * 100).toFixed(1)}%</div>
                        <div className="text-sm text-green-600">{key}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confusion Matrix */}
              {experiment.results.confusion_matrix && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Matriz de Confusion</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-green-100 rounded-lg text-center">
                      <div className="text-xl font-bold text-green-700">{experiment.results.confusion_matrix.true_positive}</div>
                      <div className="text-xs text-green-600">True Positive</div>
                    </div>
                    <div className="p-3 bg-red-100 rounded-lg text-center">
                      <div className="text-xl font-bold text-red-700">{experiment.results.confusion_matrix.false_positive}</div>
                      <div className="text-xs text-red-600">False Positive</div>
                    </div>
                    <div className="p-3 bg-red-100 rounded-lg text-center">
                      <div className="text-xl font-bold text-red-700">{experiment.results.confusion_matrix.false_negative}</div>
                      <div className="text-xs text-red-600">False Negative</div>
                    </div>
                    <div className="p-3 bg-green-100 rounded-lg text-center">
                      <div className="text-xl font-bold text-green-700">{experiment.results.confusion_matrix.true_negative}</div>
                      <div className="text-xs text-green-600">True Negative</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Other Results */}
              {experiment.results.training_time_seconds && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-gray-900">{experiment.results.epochs}</div>
                      <div className="text-xs text-gray-500">Epochs</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-900">{experiment.results.training_time_seconds}s</div>
                      <div className="text-xs text-gray-500">Training Time</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-900">{experiment.results.final_loss?.toFixed(4)}</div>
                      <div className="text-xs text-gray-500">Final Loss</div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="p-6 border-t bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

function CreateSandboxModal({ templates, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!name.trim()) return
    setCreating(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    onCreate({ name, description, template_id: selectedTemplate?.id })
    setCreating(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">Crear Nuevo Sandbox</h2>
          <p className="text-sm text-gray-500">Ambiente de prueba con datos sinteticos</p>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Mi Sandbox de Prueba"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe el proposito de este sandbox..."
                rows={2}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Seleccionar Template (opcional)</label>
            <div className="grid gap-3">
              {templates.map((template) => {
                const config = IndustryConfig[template.industry] || IndustryConfig.general
                const Icon = config.icon
                const isSelected = selectedTemplate?.id === template.id

                return (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(isSelected ? null : template)}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition text-left ${
                      isSelected ? 'border-brand-500 bg-brand-50' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg ${config.bgColor} flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${config.textColor}`} />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{template.name}</div>
                      <div className="text-sm text-gray-500">{template.description}</div>
                    </div>
                    {isSelected && <CheckCircleIcon className="w-6 h-6 text-brand-600" />}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition">
            Cancelar
          </button>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || creating}
            className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition disabled:opacity-50 flex items-center gap-2"
          >
            {creating ? (
              <>
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                Creando...
              </>
            ) : (
              <>
                <PlusIcon className="w-5 h-5" />
                Crear Sandbox
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Sandbox() {
  const [activeTab, setActiveTab] = useState('overview')
  const [templates, setTemplates] = useState(MOCK_TEMPLATES)
  const [sandbox, setSandbox] = useState(MOCK_SANDBOX)
  const [datasets, setDatasets] = useState(MOCK_DATASETS)
  const [experiments, setExperiments] = useState(MOCK_EXPERIMENTS)
  const [stats, setStats] = useState(MOCK_STATS)
  const [loading, setLoading] = useState(false)

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [selectedExperiment, setSelectedExperiment] = useState(null)

  const industryConfig = IndustryConfig[sandbox.industry] || IndustryConfig.general
  const IndustryIcon = industryConfig.icon

  const handleCreateSandbox = (data) => {
    setShowCreateModal(false)
    // Would create sandbox via API
  }

  const handleRunExperiment = (experimentId) => {
    setExperiments(experiments.map(exp =>
      exp.id === experimentId ? { ...exp, status: 'running' } : exp
    ))
    // Simulate completion
    setTimeout(() => {
      setExperiments(experiments.map(exp =>
        exp.id === experimentId ? {
          ...exp,
          status: 'completed',
          completed_at: new Date().toISOString(),
          results: {
            status: 'success',
            encryption_time_ms: 125.5,
            decryption_time_ms: 95.2,
            key_generation_time_ms: 350.0,
            ciphertext_size_kb: 45.2,
            noise_budget: 32.5
          }
        } : exp
      ))
    }, 2000)
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BeakerIcon },
    { id: 'datasets', label: 'Datasets', icon: CircleStackIcon, count: datasets.length },
    { id: 'experiments', label: 'Experimentos', icon: CpuChipIcon, count: experiments.length },
    { id: 'templates', label: 'Templates', icon: DocumentDuplicateIcon },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-100 rounded-lg">
            <BeakerIcon className="w-8 h-8 text-brand-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sandbox Mode</h1>
            <p className="text-gray-600">Ambiente de prueba con datos sinteticos</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          Nuevo Sandbox
        </button>
      </div>

      {/* Stats Banner */}
      <div className="bg-gradient-to-r from-brand-600 to-blue-600 rounded-xl p-6 mb-6 text-white">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <div>
            <div className="text-3xl font-bold">{stats.total_sandboxes}</div>
            <div className="text-sm text-white/80">Sandboxes</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.active_sandboxes}</div>
            <div className="text-sm text-white/80">Activos</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.total_datasets}</div>
            <div className="text-sm text-white/80">Datasets</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.total_experiments}</div>
            <div className="text-sm text-white/80">Experimentos</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.completed_experiments}</div>
            <div className="text-sm text-white/80">Completados</div>
          </div>
        </div>
      </div>

      {/* Current Sandbox Card */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-14 h-14 rounded-xl ${industryConfig.bgColor} flex items-center justify-center`}>
              <IndustryIcon className={`w-7 h-7 ${industryConfig.textColor}`} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{sandbox.name}</h2>
              <p className="text-gray-600">{sandbox.description}</p>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <ClockIcon className="w-4 h-4" />
                  Expira: {new Date(sandbox.expires_at).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1">
                  <CircleStackIcon className="w-4 h-4" />
                  {sandbox.dataset_count} datasets
                </span>
                <span className="flex items-center gap-1">
                  <BeakerIcon className="w-4 h-4" />
                  {sandbox.experiment_count} experimentos
                </span>
              </div>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${industryConfig.bgColor} ${industryConfig.textColor}`}>
            {industryConfig.name}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Datasets Recientes</h3>
            <div className="space-y-4">
              {datasets.slice(0, 2).map((dataset) => (
                <DatasetCard
                  key={dataset.id}
                  dataset={dataset}
                  onView={setSelectedDataset}
                  onDelete={() => {}}
                />
              ))}
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Experimentos Recientes</h3>
            <div className="space-y-4">
              {experiments.slice(0, 2).map((experiment) => (
                <ExperimentCard
                  key={experiment.id}
                  experiment={experiment}
                  onRun={handleRunExperiment}
                  onView={setSelectedExperiment}
                  onDelete={() => {}}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'datasets' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Datasets Sinteticos</h3>
            <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2">
              <PlusIcon className="w-5 h-5" />
              Generar Dataset
            </button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {datasets.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onView={setSelectedDataset}
                onDelete={() => setDatasets(datasets.filter(d => d.id !== dataset.id))}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'experiments' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Experimentos</h3>
            <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2">
              <PlusIcon className="w-5 h-5" />
              Nuevo Experimento
            </button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {experiments.map((experiment) => (
              <ExperimentCard
                key={experiment.id}
                experiment={experiment}
                onRun={handleRunExperiment}
                onView={setSelectedExperiment}
                onDelete={() => setExperiments(experiments.filter(e => e.id !== experiment.id))}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-4">Templates Disponibles</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {templates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onSelect={(t) => setShowCreateModal(true)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <LockClosedIcon className="w-8 h-8 text-blue-600 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-blue-900 mb-2">Sobre Sandbox Mode</h3>
            <p className="text-blue-800 text-sm">
              El modo Sandbox te permite experimentar con datos sinteticos antes de usar datos reales.
              Los datasets generados simulan patrones realistas de la industria seleccionada,
              permitiendo entrenar y evaluar modelos FHE sin riesgos de privacidad.
              Los sandboxes expiran automaticamente despues del periodo configurado.
            </p>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateSandboxModal
          templates={templates}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateSandbox}
        />
      )}

      {selectedDataset && (
        <DatasetDetailModal
          dataset={selectedDataset}
          onClose={() => setSelectedDataset(null)}
        />
      )}

      {selectedExperiment && (
        <ExperimentResultsModal
          experiment={selectedExperiment}
          onClose={() => setSelectedExperiment(null)}
        />
      )}
    </div>
  )
}

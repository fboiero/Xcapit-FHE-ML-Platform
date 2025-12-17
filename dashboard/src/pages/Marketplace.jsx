import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ShoppingBagIcon,
  MagnifyingGlassIcon,
  StarIcon,
  ArrowDownTrayIcon,
  CheckBadgeIcon,
  SparklesIcon,
  CpuChipIcon,
  BeakerIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  HeartIcon,
  BuildingOffice2Icon,
  BanknotesIcon,
  ShieldExclamationIcon,
  UserGroupIcon,
  ChartBarIcon,
  ArrowRightIcon,
  FunnelIcon,
  XMarkIcon,
  RocketLaunchIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'

// Industry configuration
const IndustryConfig = {
  cat_fraud: {
    name: 'Deteccion de Fraude',
    icon: ShieldExclamationIcon,
    color: 'red',
    bgColor: 'bg-red-50',
    textColor: 'text-red-600',
    borderColor: 'border-red-200',
  },
  cat_credit: {
    name: 'Credit Scoring',
    icon: BanknotesIcon,
    color: 'green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-600',
    borderColor: 'border-green-200',
  },
  cat_health: {
    name: 'Salud',
    icon: HeartIcon,
    color: 'pink',
    bgColor: 'bg-pink-50',
    textColor: 'text-pink-600',
    borderColor: 'border-pink-200',
  },
  cat_retail: {
    name: 'Retail',
    icon: ShoppingBagIcon,
    color: 'purple',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
    borderColor: 'border-purple-200',
  },
  cat_insurance: {
    name: 'Seguros',
    icon: ShieldCheckIcon,
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
  },
}

// Model type configuration
const ModelTypeConfig = {
  linear_regression: { name: 'Regresion Lineal', icon: ChartBarIcon },
  logistic_regression: { name: 'Regresion Logistica', icon: CpuChipIcon },
  decision_tree: { name: 'Decision Tree', icon: BeakerIcon },
  kmeans: { name: 'K-Means', icon: SparklesIcon },
}

// Mock categories with counts
const MOCK_CATEGORIES = [
  { id: 'cat_fraud', name: 'Deteccion de Fraude', description: 'Modelos para detectar transacciones fraudulentas', icon: 'shield', model_count: 2 },
  { id: 'cat_credit', name: 'Credit Scoring', description: 'Modelos de evaluacion de riesgo crediticio', icon: 'currency', model_count: 2 },
  { id: 'cat_health', name: 'Salud', description: 'Modelos de prediccion clinica y diagnostico', icon: 'heart', model_count: 2 },
  { id: 'cat_retail', name: 'Retail', description: 'Modelos de prediccion de clientes y recomendacion', icon: 'shopping', model_count: 2 },
  { id: 'cat_insurance', name: 'Seguros', description: 'Modelos de evaluacion de riesgo y fraude', icon: 'shield', model_count: 2 },
]

// Mock models
const MOCK_MODELS = [
  {
    id: 'model_fraud_001',
    name: 'Transaction Fraud Detector',
    description: 'Modelo de deteccion de fraude en transacciones financieras usando logistic regression',
    industry: 'cat_fraud',
    model_type: 'logistic_regression',
    version: '2.1.0',
    accuracy: 0.956,
    training_samples: 500000,
    features: ['transaction_amount', 'merchant_category', 'time_of_day', 'location_distance'],
    use_cases: ['Bancos', 'Fintech', 'Payment Processors'],
    pricing_type: 'free',
    price: 0,
    is_featured: true,
    downloads: 1250,
    rating: 4.7,
    rating_count: 89,
  },
  {
    id: 'model_fraud_002',
    name: 'Account Takeover Detector',
    description: 'Detector de intentos de apropiacion de cuentas basado en patrones de comportamiento',
    industry: 'cat_fraud',
    model_type: 'decision_tree',
    version: '1.5.0',
    accuracy: 0.923,
    training_samples: 250000,
    features: ['login_frequency', 'device_fingerprint', 'ip_reputation', 'session_duration'],
    use_cases: ['Bancos', 'E-commerce', 'Plataformas digitales'],
    pricing_type: 'premium',
    price: 299,
    is_featured: true,
    downloads: 450,
    rating: 4.5,
    rating_count: 34,
  },
  {
    id: 'model_credit_001',
    name: 'Credit Default Predictor',
    description: 'Prediccion de probabilidad de default en creditos personales y empresariales',
    industry: 'cat_credit',
    model_type: 'logistic_regression',
    version: '3.0.0',
    accuracy: 0.891,
    training_samples: 750000,
    features: ['income_ratio', 'credit_history', 'employment_status', 'debt_to_income'],
    use_cases: ['Bancos', 'Cooperativas', 'Fintechs de credito'],
    pricing_type: 'free',
    price: 0,
    is_featured: true,
    downloads: 2100,
    rating: 4.8,
    rating_count: 156,
  },
  {
    id: 'model_credit_002',
    name: 'Alternative Credit Scorer',
    description: 'Scoring crediticio basado en datos alternativos para poblacion no bancarizada',
    industry: 'cat_credit',
    model_type: 'decision_tree',
    version: '1.2.0',
    accuracy: 0.834,
    training_samples: 180000,
    features: ['utility_payments', 'mobile_usage', 'social_connections', 'transaction_patterns'],
    use_cases: ['Microfinanzas', 'Fintechs', 'Bancos rurales'],
    pricing_type: 'premium',
    price: 499,
    is_featured: false,
    downloads: 320,
    rating: 4.3,
    rating_count: 28,
  },
  {
    id: 'model_health_001',
    name: 'Hospital Readmission Risk',
    description: 'Prediccion de riesgo de readmision hospitalaria en 30 dias',
    industry: 'cat_health',
    model_type: 'logistic_regression',
    version: '2.0.0',
    accuracy: 0.867,
    training_samples: 420000,
    features: ['diagnosis_codes', 'length_of_stay', 'comorbidities', 'prior_admissions'],
    use_cases: ['Hospitales', 'Sistemas de salud', 'Aseguradoras'],
    pricing_type: 'premium',
    price: 799,
    is_featured: true,
    downloads: 680,
    rating: 4.6,
    rating_count: 45,
  },
  {
    id: 'model_health_002',
    name: 'Diagnostic Support Model',
    description: 'Modelo de apoyo diagnostico basado en sintomas y resultados de laboratorio',
    industry: 'cat_health',
    model_type: 'decision_tree',
    version: '1.8.0',
    accuracy: 0.912,
    training_samples: 350000,
    features: ['symptoms', 'lab_results', 'patient_history', 'vital_signs'],
    use_cases: ['Clinicas', 'Hospitales', 'Telemedicina'],
    pricing_type: 'enterprise',
    price: 1999,
    is_featured: false,
    downloads: 180,
    rating: 4.9,
    rating_count: 12,
  },
  {
    id: 'model_retail_001',
    name: 'Customer Churn Predictor',
    description: 'Prediccion de probabilidad de abandono de clientes',
    industry: 'cat_retail',
    model_type: 'logistic_regression',
    version: '2.5.0',
    accuracy: 0.878,
    training_samples: 620000,
    features: ['purchase_frequency', 'recency', 'monetary_value', 'engagement_score'],
    use_cases: ['E-commerce', 'Retail', 'Suscripciones'],
    pricing_type: 'free',
    price: 0,
    is_featured: true,
    downloads: 1890,
    rating: 4.4,
    rating_count: 112,
  },
  {
    id: 'model_retail_002',
    name: 'Product Recommender',
    description: 'Sistema de recomendacion de productos basado en clustering de usuarios',
    industry: 'cat_retail',
    model_type: 'kmeans',
    version: '1.3.0',
    accuracy: null,
    training_samples: 890000,
    features: ['purchase_history', 'browsing_behavior', 'demographics', 'preferences'],
    use_cases: ['E-commerce', 'Marketplaces', 'Apps de retail'],
    pricing_type: 'premium',
    price: 399,
    is_featured: false,
    downloads: 560,
    rating: 4.2,
    rating_count: 67,
  },
  {
    id: 'model_insurance_001',
    name: 'Claim Fraud Detector',
    description: 'Deteccion de reclamos fraudulentos en seguros de auto y hogar',
    industry: 'cat_insurance',
    model_type: 'logistic_regression',
    version: '2.2.0',
    accuracy: 0.934,
    training_samples: 380000,
    features: ['claim_amount', 'claim_frequency', 'policy_age', 'claimant_history'],
    use_cases: ['Aseguradoras', 'Reaseguradoras', 'Brokers'],
    pricing_type: 'premium',
    price: 599,
    is_featured: true,
    downloads: 890,
    rating: 4.7,
    rating_count: 78,
  },
  {
    id: 'model_insurance_002',
    name: 'Underwriting Risk Model',
    description: 'Evaluacion de riesgo para suscripcion de polizas de vida y salud',
    industry: 'cat_insurance',
    model_type: 'decision_tree',
    version: '1.9.0',
    accuracy: 0.856,
    training_samples: 290000,
    features: ['age', 'health_indicators', 'lifestyle_factors', 'family_history'],
    use_cases: ['Aseguradoras de vida', 'Salud', 'Brokers'],
    pricing_type: 'enterprise',
    price: 1499,
    is_featured: false,
    downloads: 240,
    rating: 4.5,
    rating_count: 23,
  },
]

// Mock stats
const MOCK_STATS = {
  total_models: 10,
  total_downloads: 8560,
  active_consortiums: 45,
  total_reviews: 644,
  average_rating: 4.56,
}

// Mock reviews for a model
const MOCK_REVIEWS = [
  {
    id: 'rev_1',
    reviewer_name: 'Banco Nacional',
    rating: 5,
    title: 'Excelente precision',
    comment: 'Implementamos este modelo y redujo nuestros falsos positivos en un 40%. Muy recomendado.',
    created_at: '2024-12-01T10:00:00Z',
    helpful_count: 12,
  },
  {
    id: 'rev_2',
    reviewer_name: 'Fintech Alpha',
    rating: 4,
    title: 'Buen modelo, facil de integrar',
    comment: 'La integracion fue sencilla y los resultados son consistentes. Mejoraria la documentacion.',
    created_at: '2024-11-28T14:30:00Z',
    helpful_count: 8,
  },
  {
    id: 'rev_3',
    reviewer_name: 'Cooperativa Central',
    rating: 5,
    title: 'Superó nuestras expectativas',
    comment: 'El modelo funciona muy bien con nuestros datos. El soporte del equipo fue excelente.',
    created_at: '2024-11-25T09:15:00Z',
    helpful_count: 15,
  },
]

function StarRating({ rating, size = 'md' }) {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'
  const stars = []
  for (let i = 1; i <= 5; i++) {
    stars.push(
      i <= Math.floor(rating) ? (
        <StarIconSolid key={i} className={`${sizeClass} text-yellow-400`} />
      ) : i - 0.5 <= rating ? (
        <StarIconSolid key={i} className={`${sizeClass} text-yellow-400 opacity-50`} />
      ) : (
        <StarIcon key={i} className={`${sizeClass} text-gray-300`} />
      )
    )
  }
  return <div className="flex items-center gap-0.5">{stars}</div>
}

function PricingBadge({ type, price }) {
  const config = {
    free: { label: 'Gratis', bgColor: 'bg-green-100', textColor: 'text-green-700' },
    premium: { label: `$${price}/mes`, bgColor: 'bg-purple-100', textColor: 'text-purple-700' },
    enterprise: { label: 'Enterprise', bgColor: 'bg-gray-100', textColor: 'text-gray-700' },
  }
  const c = config[type] || config.premium
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.bgColor} ${c.textColor}`}>
      {c.label}
    </span>
  )
}

function CategoryCard({ category, onClick }) {
  const config = IndustryConfig[category.id] || {
    icon: ShoppingBagIcon,
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-200',
  }
  const Icon = config.icon

  return (
    <button
      onClick={() => onClick(category.id)}
      className={`w-full bg-white rounded-xl border ${config.borderColor} p-6 hover:shadow-lg transition text-left group`}
    >
      <div className={`w-12 h-12 rounded-lg ${config.bgColor} flex items-center justify-center mb-4 group-hover:scale-110 transition`}>
        <Icon className={`w-6 h-6 ${config.textColor}`} />
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{category.name}</h3>
      <p className="text-sm text-gray-500 mb-3">{category.description}</p>
      <div className="flex items-center justify-between">
        <span className="text-sm text-brand-600 font-medium">{category.model_count} modelos</span>
        <ArrowRightIcon className="w-4 h-4 text-brand-600 group-hover:translate-x-1 transition" />
      </div>
    </button>
  )
}

function ModelCard({ model, onClick, onDeploy }) {
  const industryConfig = IndustryConfig[model.industry] || {}
  const IndustryIcon = industryConfig.icon || ShoppingBagIcon

  return (
    <div className="bg-white rounded-xl border shadow-sm hover:shadow-lg transition overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg ${industryConfig.bgColor || 'bg-gray-50'} flex items-center justify-center`}>
              <IndustryIcon className={`w-5 h-5 ${industryConfig.textColor || 'text-gray-600'}`} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{model.name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full ${industryConfig.bgColor || 'bg-gray-100'} ${industryConfig.textColor || 'text-gray-600'}`}>
                {industryConfig.name || model.industry}
              </span>
            </div>
          </div>
          {model.is_featured && (
            <span className="flex items-center gap-1 px-2 py-1 bg-yellow-50 text-yellow-700 rounded-full text-xs font-medium">
              <SparklesIcon className="w-3 h-3" />
              Featured
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 line-clamp-2">{model.description}</p>
      </div>

      {/* Stats */}
      <div className="px-5 py-3 bg-gray-50 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-bold text-gray-900">
            {model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}
          </div>
          <div className="text-xs text-gray-500">Accuracy</div>
        </div>
        <div>
          <div className="text-lg font-bold text-gray-900">{model.downloads.toLocaleString()}</div>
          <div className="text-xs text-gray-500">Downloads</div>
        </div>
        <div>
          <div className="flex items-center justify-center gap-1">
            <StarIconSolid className="w-4 h-4 text-yellow-400" />
            <span className="text-lg font-bold text-gray-900">{model.rating.toFixed(1)}</span>
          </div>
          <div className="text-xs text-gray-500">({model.rating_count})</div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-5 flex items-center justify-between">
        <PricingBadge type={model.pricing_type} price={model.price} />
        <div className="flex gap-2">
          <button
            onClick={() => onClick(model)}
            className="px-3 py-2 text-sm text-brand-600 hover:bg-brand-50 rounded-lg transition"
          >
            Ver detalles
          </button>
          <button
            onClick={() => onDeploy(model)}
            className="px-3 py-2 text-sm bg-brand-600 text-white hover:bg-brand-700 rounded-lg transition flex items-center gap-1"
          >
            <RocketLaunchIcon className="w-4 h-4" />
            Deploy
          </button>
        </div>
      </div>
    </div>
  )
}

function ModelDetailModal({ model, onClose, onDeploy }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [reviews, setReviews] = useState(MOCK_REVIEWS)

  const industryConfig = IndustryConfig[model.industry] || {}
  const modelTypeConfig = ModelTypeConfig[model.model_type] || {}
  const IndustryIcon = industryConfig.icon || ShoppingBagIcon
  const ModelTypeIcon = modelTypeConfig.icon || CpuChipIcon

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className={`w-16 h-16 rounded-xl ${industryConfig.bgColor || 'bg-gray-50'} flex items-center justify-center`}>
              <IndustryIcon className={`w-8 h-8 ${industryConfig.textColor || 'text-gray-600'}`} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold text-gray-900">{model.name}</h2>
                {model.is_featured && (
                  <span className="flex items-center gap-1 px-2 py-1 bg-yellow-50 text-yellow-700 rounded-full text-xs font-medium">
                    <SparklesIcon className="w-3 h-3" />
                    Featured
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded-full ${industryConfig.bgColor || 'bg-gray-100'} ${industryConfig.textColor || 'text-gray-600'}`}>
                  {industryConfig.name || model.industry}
                </span>
                <span className="text-gray-500">v{model.version}</span>
                <StarRating rating={model.rating} size="sm" />
                <span className="text-gray-500">({model.rating_count} reviews)</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition">
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          {['overview', 'features', 'reviews'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                activeTab === tab
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'overview' ? 'General' : tab === 'features' ? 'Caracteristicas' : 'Reviews'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Descripcion</h3>
                <p className="text-gray-600">{model.description}</p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-xl p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Metricas</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Accuracy</span>
                      <span className="font-medium">{model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Training Samples</span>
                      <span className="font-medium">{model.training_samples?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Downloads</span>
                      <span className="font-medium">{model.downloads.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Version</span>
                      <span className="font-medium">{model.version}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Especificaciones</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Tipo de Modelo</span>
                      <span className="font-medium flex items-center gap-1">
                        <ModelTypeIcon className="w-4 h-4" />
                        {modelTypeConfig.name || model.model_type}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Industria</span>
                      <span className="font-medium">{industryConfig.name || model.industry}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Pricing</span>
                      <PricingBadge type={model.pricing_type} price={model.price} />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Casos de Uso</h4>
                <div className="flex flex-wrap gap-2">
                  {model.use_cases?.map((useCase, i) => (
                    <span key={i} className="px-3 py-1 bg-brand-50 text-brand-700 rounded-full text-sm">
                      {useCase}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'features' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Features del Modelo</h3>
                <div className="grid md:grid-cols-2 gap-3">
                  {model.features?.map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                      <CheckBadgeIcon className="w-5 h-5 text-green-500" />
                      <span className="text-gray-700">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-blue-50 rounded-xl p-4">
                <h4 className="font-medium text-blue-900 mb-2">Compatibilidad FHE</h4>
                <p className="text-blue-800 text-sm">
                  Este modelo esta optimizado para funcionar con Fully Homomorphic Encryption (FHE),
                  permitiendo realizar inferencias sobre datos encriptados sin revelar el contenido original.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'reviews' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-3xl font-bold text-gray-900">{model.rating.toFixed(1)}</div>
                  <div>
                    <StarRating rating={model.rating} />
                    <div className="text-sm text-gray-500">{model.rating_count} reviews</div>
                  </div>
                </div>
                <button className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition flex items-center gap-2">
                  <ChatBubbleLeftRightIcon className="w-5 h-5" />
                  Escribir Review
                </button>
              </div>

              {reviews.map((review) => (
                <div key={review.id} className="border rounded-xl p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900">{review.reviewer_name}</span>
                        <StarRating rating={review.rating} size="sm" />
                      </div>
                      <span className="text-sm text-gray-500 flex items-center gap-1">
                        <ClockIcon className="w-4 h-4" />
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <h4 className="font-medium text-gray-900 mb-1">{review.title}</h4>
                  <p className="text-gray-600 text-sm mb-2">{review.comment}</p>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <button className="flex items-center gap-1 hover:text-brand-600 transition">
                      <ArrowDownTrayIcon className="w-4 h-4" />
                      Util ({review.helpful_count})
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex items-center justify-between">
          <div>
            <PricingBadge type={model.pricing_type} price={model.price} />
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition">
              Cerrar
            </button>
            <button
              onClick={() => onDeploy(model)}
              className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2"
            >
              <RocketLaunchIcon className="w-5 h-5" />
              Deploy al Consorcio
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function DeployModal({ model, onClose, onConfirm }) {
  const [selectedConsortium, setSelectedConsortium] = useState('')
  const [deploying, setDeploying] = useState(false)

  // Mock consortiums
  const consortiums = [
    { id: 'cons_1', name: 'Consorcio Bancario Alpha' },
    { id: 'cons_2', name: 'Fintech Coalition' },
    { id: 'cons_3', name: 'Insurance Network' },
  ]

  const handleDeploy = async () => {
    if (!selectedConsortium) return
    setDeploying(true)
    // Simulate deployment
    await new Promise(resolve => setTimeout(resolve, 1500))
    onConfirm(model, selectedConsortium)
    setDeploying(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">Deploy Modelo</h2>
          <p className="text-gray-600 text-sm mt-1">Selecciona el consorcio donde deseas desplegar este modelo</p>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
            <RocketLaunchIcon className="w-10 h-10 text-brand-600" />
            <div>
              <div className="font-medium text-gray-900">{model.name}</div>
              <div className="text-sm text-gray-500">v{model.version}</div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seleccionar Consorcio
            </label>
            <select
              value={selectedConsortium}
              onChange={(e) => setSelectedConsortium(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            >
              <option value="">Elegir consorcio...</option>
              {consortiums.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Al desplegar este modelo, todos los miembros del consorcio podran utilizarlo para inferencias sobre datos encriptados.
            </p>
          </div>
        </div>

        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition">
            Cancelar
          </button>
          <button
            onClick={handleDeploy}
            disabled={!selectedConsortium || deploying}
            className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {deploying ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Desplegando...
              </>
            ) : (
              <>
                <RocketLaunchIcon className="w-5 h-5" />
                Confirmar Deploy
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Marketplace() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('browse')
  const [categories, setCategories] = useState(MOCK_CATEGORIES)
  const [models, setModels] = useState(MOCK_MODELS)
  const [stats, setStats] = useState(MOCK_STATS)
  const [loading, setLoading] = useState(false)

  // Filters
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('downloads')
  const [showFeaturedOnly, setShowFeaturedOnly] = useState(false)

  // Modals
  const [selectedModel, setSelectedModel] = useState(null)
  const [deployingModel, setDeployingModel] = useState(null)

  // Filter models
  const filteredModels = models.filter((model) => {
    if (selectedCategory && model.industry !== selectedCategory) return false
    if (showFeaturedOnly && !model.is_featured) return false
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        model.name.toLowerCase().includes(query) ||
        model.description.toLowerCase().includes(query)
      )
    }
    return true
  }).sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating
      case 'newest':
        return 0 // Would sort by created_at
      case 'accuracy':
        return (b.accuracy || 0) - (a.accuracy || 0)
      default: // downloads
        return b.downloads - a.downloads
    }
  })

  const featuredModels = models.filter((m) => m.is_featured).slice(0, 4)

  const handleDeploy = (model, consortiumId) => {
    setDeployingModel(null)
    // Show success message
    alert(`Modelo "${model.name}" desplegado exitosamente al consorcio!`)
  }

  const tabs = [
    { id: 'browse', label: 'Explorar', icon: MagnifyingGlassIcon },
    { id: 'featured', label: 'Destacados', icon: SparklesIcon },
    { id: 'categories', label: 'Categorias', icon: FunnelIcon },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-100 rounded-lg">
            <ShoppingBagIcon className="w-8 h-8 text-brand-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Model Marketplace</h1>
            <p className="text-gray-600">Modelos pre-entrenados por industria, listos para FHE</p>
          </div>
        </div>
      </div>

      {/* Stats Banner */}
      <div className="bg-gradient-to-r from-brand-600 to-purple-600 rounded-xl p-6 mb-6 text-white">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <div>
            <div className="text-3xl font-bold">{stats.total_models}</div>
            <div className="text-sm text-white/80">Modelos</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.total_downloads.toLocaleString()}</div>
            <div className="text-sm text-white/80">Downloads</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.active_consortiums}</div>
            <div className="text-sm text-white/80">Consorcios Activos</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats.total_reviews}</div>
            <div className="text-sm text-white/80">Reviews</div>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1">
              <StarIconSolid className="w-6 h-6 text-yellow-300" />
              <span className="text-3xl font-bold">{stats.average_rating.toFixed(1)}</span>
            </div>
            <div className="text-sm text-white/80">Rating Promedio</div>
          </div>
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
          </button>
        ))}
      </div>

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div>
          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar modelos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedCategory || ''}
                onChange={(e) => setSelectedCategory(e.target.value || null)}
                className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500"
              >
                <option value="">Todas las industrias</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500"
              >
                <option value="downloads">Mas descargados</option>
                <option value="rating">Mejor valorados</option>
                <option value="accuracy">Mayor accuracy</option>
                <option value="newest">Mas recientes</option>
              </select>
              <button
                onClick={() => setShowFeaturedOnly(!showFeaturedOnly)}
                className={`px-4 py-2 border rounded-lg flex items-center gap-2 transition ${
                  showFeaturedOnly ? 'bg-yellow-50 border-yellow-300 text-yellow-700' : 'hover:bg-gray-50'
                }`}
              >
                <SparklesIcon className="w-5 h-5" />
                Featured
              </button>
            </div>
          </div>

          {/* Active Filters */}
          {(selectedCategory || showFeaturedOnly || searchQuery) && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-gray-500">Filtros activos:</span>
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="flex items-center gap-1 px-2 py-1 bg-brand-50 text-brand-700 rounded-full text-sm"
                >
                  {IndustryConfig[selectedCategory]?.name || selectedCategory}
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
              {showFeaturedOnly && (
                <button
                  onClick={() => setShowFeaturedOnly(false)}
                  className="flex items-center gap-1 px-2 py-1 bg-yellow-50 text-yellow-700 rounded-full text-sm"
                >
                  Featured
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  "{searchQuery}"
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => {
                  setSelectedCategory(null)
                  setShowFeaturedOnly(false)
                  setSearchQuery('')
                }}
                className="text-sm text-brand-600 hover:underline"
              >
                Limpiar todo
              </button>
            </div>
          )}

          {/* Models Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModels.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onClick={setSelectedModel}
                onDeploy={setDeployingModel}
              />
            ))}
          </div>

          {filteredModels.length === 0 && (
            <div className="text-center py-12">
              <MagnifyingGlassIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No se encontraron modelos con los filtros seleccionados</p>
            </div>
          )}
        </div>
      )}

      {/* Featured Tab */}
      {activeTab === 'featured' && (
        <div>
          <div className="flex items-center gap-2 mb-6">
            <SparklesIcon className="w-6 h-6 text-yellow-500" />
            <h2 className="text-lg font-semibold text-gray-900">Modelos Destacados</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {featuredModels.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onClick={setSelectedModel}
                onDeploy={setDeployingModel}
              />
            ))}
          </div>
        </div>
      )}

      {/* Categories Tab */}
      {activeTab === 'categories' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Explorar por Industria</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category) => (
              <CategoryCard
                key={category.id}
                category={category}
                onClick={(id) => {
                  setSelectedCategory(id)
                  setActiveTab('browse')
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">Sobre el Marketplace</h3>
        <p className="text-blue-800 text-sm">
          Todos los modelos en el marketplace estan pre-entrenados y optimizados para funcionar con Fully Homomorphic Encryption (FHE).
          Al desplegar un modelo en tu consorcio, podras realizar inferencias sobre datos encriptados sin revelar informacion sensible.
        </p>
      </div>

      {/* Modals */}
      {selectedModel && (
        <ModelDetailModal
          model={selectedModel}
          onClose={() => setSelectedModel(null)}
          onDeploy={(model) => {
            setSelectedModel(null)
            setDeployingModel(model)
          }}
        />
      )}

      {deployingModel && (
        <DeployModal
          model={deployingModel}
          onClose={() => setDeployingModel(null)}
          onConfirm={handleDeploy}
        />
      )}
    </div>
  )
}

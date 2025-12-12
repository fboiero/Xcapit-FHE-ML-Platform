import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createConsortium } from '../api/client'

const modelTypes = [
  {
    id: 'linear_regression',
    name: 'Regresion Lineal',
    description: 'Prediccion de valores continuos basado en variables independientes.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
  {
    id: 'logistic_regression',
    name: 'Regresion Logistica',
    description: 'Clasificacion binaria para predecir categorias.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    id: 'neural_network',
    name: 'Red Neuronal',
    description: 'Modelos profundos para patrones complejos.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
]

export default function ConsortiumCreate() {
  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [modelType, setModelType] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const consortium = await createConsortium(name, description, modelType)
      navigate(`/consortiums/${consortium.id}`)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="pt-16 max-w-2xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link to="/dashboard" className="hover:text-brand-600">Dashboard</Link>
        <span>/</span>
        <span className="text-slate-900">Crear Consorcio</span>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-4 mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step >= s
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-100 text-slate-400'
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div
                className={`w-16 h-1 mx-2 rounded ${
                  step > s ? 'bg-brand-600' : 'bg-slate-100'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Informacion basica</h2>
            <p className="text-slate-600 mb-6">Define el nombre y proposito de tu consorcio.</p>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Nombre del consorcio
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
                  placeholder="Ej: Analisis de Fraude Bancario"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Descripcion
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition resize-none"
                  placeholder="Describe el objetivo del consorcio y que tipo de datos se compartiran..."
                />
              </div>
            </div>

            <div className="flex justify-end mt-8">
              <button
                onClick={() => setStep(2)}
                disabled={!name || !description}
                className="bg-brand-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Model Type */}
        {step === 2 && (
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Tipo de modelo</h2>
            <p className="text-slate-600 mb-6">Selecciona el algoritmo de ML que se entrenara.</p>

            <div className="space-y-4">
              {modelTypes.map((model) => (
                <button
                  key={model.id}
                  onClick={() => setModelType(model.id)}
                  className={`w-full p-4 rounded-xl border-2 text-left transition ${
                    modelType === model.id
                      ? 'border-brand-600 bg-brand-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        modelType === model.id
                          ? 'bg-brand-600 text-white'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {model.icon}
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{model.name}</h3>
                      <p className="text-sm text-slate-600">{model.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-between mt-8">
              <button
                onClick={() => setStep(1)}
                className="text-slate-600 px-6 py-3 rounded-xl font-medium hover:bg-slate-100 transition"
              >
                Atras
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!modelType}
                className="bg-brand-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Confirmar creacion</h2>
            <p className="text-slate-600 mb-6">Revisa la informacion antes de crear el consorcio.</p>

            <div className="bg-slate-50 rounded-xl p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-500">Nombre</p>
                <p className="font-medium text-slate-900">{name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Descripcion</p>
                <p className="text-slate-900">{description}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Tipo de modelo</p>
                <p className="font-medium text-slate-900">
                  {modelTypes.find((m) => m.id === modelType)?.name}
                </p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mt-6">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-blue-900">Siguiente paso</p>
                  <p className="text-sm text-blue-700">
                    Despues de crear el consorcio, podras invitar participantes y subir datos encriptados.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-8">
              <button
                onClick={() => setStep(2)}
                className="text-slate-600 px-6 py-3 rounded-xl font-medium hover:bg-slate-100 transition"
              >
                Atras
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="bg-brand-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creando...' : 'Crear Consorcio'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

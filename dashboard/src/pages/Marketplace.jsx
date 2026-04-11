import { useState } from 'react'

const COLORS = {
  primary: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f8fafc',
  card: '#ffffff',
  text: '#1e293b',
  muted: '#64748b',
  border: '#e5e7eb',
  accent: '#06d6a0',
}

const CATEGORIES = ['Todos', 'Regresion', 'Clasificacion', 'NLP', 'Vision']

const MODELS = [
  {
    id: 1,
    name: 'Predictor de Riesgo Crediticio',
    owner: 'FinML Labs',
    category: 'Clasificacion',
    accuracy: 96.4,
    price: null,
    priceLabel: 'Gratis',
    tags: ['finanzas', 'riesgo', 'FHE'],
    downloads: 2340,
    verified: true,
    description: 'Modelo de clasificacion binaria para evaluar riesgo crediticio sobre datos encriptados con CKKS.',
  },
  {
    id: 2,
    name: 'Estimador de Costos Medicos',
    owner: 'HealthAI Corp',
    category: 'Regresion',
    accuracy: 92.1,
    price: 49,
    priceLabel: '$49/mes',
    tags: ['salud', 'costos', 'regresion'],
    downloads: 1856,
    verified: true,
    description: 'Regresion lineal para estimar costos de tratamiento preservando la privacidad del paciente.',
  },
  {
    id: 3,
    name: 'Clasificador de Sentimiento',
    owner: 'NLP Factory',
    category: 'NLP',
    accuracy: 89.7,
    price: 29,
    priceLabel: '$29/mes',
    tags: ['NLP', 'sentimiento', 'texto'],
    downloads: 3120,
    verified: false,
    description: 'Analisis de sentimiento en textos encriptados. Soporta espanol e ingles.',
  },
  {
    id: 4,
    name: 'Detector de Fraude Transaccional',
    owner: 'SecureBank AI',
    category: 'Clasificacion',
    accuracy: 98.2,
    price: 199,
    priceLabel: '$199/mes',
    tags: ['fraude', 'finanzas', 'tiempo real'],
    downloads: 945,
    verified: true,
    description: 'Deteccion de transacciones fraudulentas en tiempo real con encriptacion homomorfica completa.',
  },
  {
    id: 5,
    name: 'Predictor de Abandono (Churn)',
    owner: 'RetailML',
    category: 'Clasificacion',
    accuracy: 91.3,
    price: null,
    priceLabel: 'Gratis',
    tags: ['retail', 'churn', 'clientes'],
    downloads: 4210,
    verified: true,
    description: 'Modelo federado para predecir abandono de clientes sin exponer datos sensibles entre retailers.',
  },
  {
    id: 6,
    name: 'Regresion de Precios Inmobiliarios',
    owner: 'PropTech Analytics',
    category: 'Regresion',
    accuracy: 88.5,
    price: 79,
    priceLabel: '$79/mes',
    tags: ['inmobiliario', 'precios', 'regresion'],
    downloads: 1230,
    verified: false,
    description: 'Estimacion de precios inmobiliarios usando datos federados de multiples inmobiliarias.',
  },
  {
    id: 7,
    name: 'Clasificador de Imagenes Medicas',
    owner: 'MedVision AI',
    category: 'Vision',
    accuracy: 94.8,
    price: 299,
    priceLabel: '$299/mes',
    tags: ['vision', 'medico', 'imagenes'],
    downloads: 678,
    verified: true,
    description: 'Clasificacion de radiografias con privacidad del paciente garantizada mediante FHE.',
  },
  {
    id: 8,
    name: 'Extractor de Entidades Clinicas',
    owner: 'BioNLP',
    category: 'NLP',
    accuracy: 86.9,
    price: null,
    priceLabel: 'Gratis',
    tags: ['NLP', 'clinico', 'entidades'],
    downloads: 1560,
    verified: false,
    description: 'Extraccion de entidades nombradas en historias clinicas encriptadas.',
  },
]

export default function Marketplace() {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState('Todos')

  const filtered = MODELS.filter((m) => {
    const matchCategory = activeCategory === 'Todos' || m.category === activeCategory
    const matchSearch = search === '' ||
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.tags.some(t => t.toLowerCase().includes(search.toLowerCase())) ||
      m.owner.toLowerCase().includes(search.toLowerCase())
    return matchCategory && matchSearch
  })

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Marketplace de Modelos
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Explora y adquiere modelos de ML con privacidad garantizada
        </p>
      </div>

      {/* Search + Filter bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, flexWrap: 'wrap',
      }}>
        <div style={{ flex: '1 1 300px', position: 'relative' }}>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar modelos, tags o propietario..."
            style={{
              width: '100%', padding: '10px 14px 10px 38px', borderRadius: 8,
              border: `1px solid ${COLORS.border}`, fontSize: 14, outline: 'none',
              boxSizing: 'border-box', background: COLORS.card,
            }}
          />
          <svg width="16" height="16" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={2}
            style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}
          >
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '8px 16px', borderRadius: 20, border: 'none',
                background: activeCategory === cat ? COLORS.primary : COLORS.bg,
                color: activeCategory === cat ? '#fff' : COLORS.muted,
                fontSize: 13, fontWeight: 600, cursor: 'pointer',
                transition: 'background 0.2s, color 0.2s',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p style={{ fontSize: 14, color: COLORS.muted, margin: '0 0 16px' }}>
        {filtered.length} modelo{filtered.length !== 1 ? 's' : ''} encontrado{filtered.length !== 1 ? 's' : ''}
      </p>

      {/* Models grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 20 }}>
        {filtered.map((model) => (
          <div key={model.id} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            transition: 'box-shadow 0.2s',
          }}
            onMouseOver={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)' }}
            onMouseOut={(e) => { e.currentTarget.style.boxShadow = 'none' }}
          >
            <div>
              {/* Title + verified */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: 0, lineHeight: 1.3 }}>
                  {model.name}
                </h3>
                {model.verified && (
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: COLORS.successLight, color: COLORS.success, whiteSpace: 'nowrap',
                  }}>
                    Verificado
                  </span>
                )}
              </div>

              <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 12px' }}>{model.owner}</p>

              <p style={{ fontSize: 13, color: COLORS.text, margin: '0 0 14px', lineHeight: 1.5 }}>
                {model.description}
              </p>

              {/* Tags */}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                {model.tags.map((tag) => (
                  <span key={tag} style={{
                    padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 500,
                    background: COLORS.bg, color: COLORS.muted, border: `1px solid ${COLORS.border}`,
                  }}>
                    {tag}
                  </span>
                ))}
              </div>

              {/* Stats row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 16 }}>
                  <div>
                    <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 2px' }}>Precision</p>
                    <p style={{ fontSize: 16, fontWeight: 700, color: COLORS.success, margin: 0 }}>{model.accuracy}%</p>
                  </div>
                  <div>
                    <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 2px' }}>Descargas</p>
                    <p style={{ fontSize: 16, fontWeight: 700, color: COLORS.text, margin: 0 }}>{model.downloads.toLocaleString()}</p>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{
                    fontSize: 18, fontWeight: 700, margin: 0,
                    color: model.price ? COLORS.primary : COLORS.accent,
                  }}>
                    {model.priceLabel}
                  </p>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8,
                border: `1px solid ${COLORS.border}`, background: COLORS.card,
                color: COLORS.text, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              }}>
                Ver Detalles
              </button>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8, border: 'none',
                background: COLORS.primary, color: '#fff', fontSize: 13,
                fontWeight: 600, cursor: 'pointer',
              }}>
                Adquirir
              </button>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 48, textAlign: 'center',
        }}>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 8px' }}>
            No se encontraron modelos
          </p>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
            Intenta ajustar los filtros o el termino de busqueda
          </p>
        </div>
      )}
    </div>
  )
}

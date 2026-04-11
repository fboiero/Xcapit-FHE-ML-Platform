import { useState, useEffect, useRef } from 'react'

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

const STEPS = [
  { num: 1, title: 'Registrate', desc: 'Crea tu cuenta en menos de 2 minutos. Sin tarjeta de credito.', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { num: 2, title: 'Subi tus datos', desc: 'Carga tu dataset CSV. Se cifra automaticamente con FHE antes de salir de tu navegador.', icon: 'M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5' },
  { num: 3, title: 'Entrena con FHE', desc: 'Ejecuta modelos de ML sobre datos cifrados. Nunca se expone la informacion original.', icon: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3' },
]

const PRIVACY_LAYERS = [
  { key: 'fhe', title: 'FHE', subtitle: 'Encriptacion Homomorfica', desc: 'Computo sobre datos cifrados sin descifrar. Esquema CKKS con seguridad de 128/192/256 bits.', color: COLORS.primary, bg: COLORS.primaryLight },
  { key: 'zkp', title: 'ZKP', subtitle: 'Pruebas de Conocimiento Cero', desc: 'Verifica la integridad de contribuciones sin revelar el contenido de los datos originales.', color: '#8b5cf6', bg: '#f5f3ff' },
  { key: 'mpc', title: 'MPC', subtitle: 'Computacion Multipartita', desc: 'Divide el calculo entre multiples nodos. Ningun participante individual puede reconstruir los datos.', color: COLORS.accent, bg: '#ecfdf5' },
  { key: 'dp', title: 'DP', subtitle: 'Privacidad Diferencial', desc: 'Agrega ruido calibrado a los resultados para prevenir la re-identificacion de registros individuales.', color: COLORS.warning, bg: COLORS.warningLight },
]

const TERMINAL_LINES = [
  '$ python manage.py demo_trial',
  'Xcapit FHE-ML Platform v0.7.0',
  'Inicializando entorno de prueba...',
  '[OK] Conexion a servidor establecida',
  '[OK] Generando claves CKKS (128-bit)...',
  '[OK] Claves publicas/privadas generadas',
  'Cargando dataset de ejemplo (500 registros)...',
  '[OK] Dataset cargado: 500 filas x 12 features',
  'Cifrando datos con TenSEAL...',
  '[OK] Datos cifrados en 1.23s (tamanio: 4.2 MB)',
  'Entrenando modelo: linear_regression (FHE)',
  '  Epoch 1/10 - loss: 0.4521 - R2: 0.72',
  '  Epoch 5/10 - loss: 0.1203 - R2: 0.89',
  '  Epoch 10/10 - loss: 0.0341 - R2: 0.94',
  '[OK] Entrenamiento completado en 8.7s',
  '[OK] Modelo guardado: demo_model_fhe_v1.pkl',
  'Verificacion ZKP del resultado: VALIDA',
  '',
  'Trial listo. Ejecuta `xcapit predict` para inferencia.',
]

export default function Demo() {
  const [terminalText, setTerminalText] = useState([])
  const [lineIndex, setLineIndex] = useState(0)
  const [charIndex, setCharIndex] = useState(0)
  const termRef = useRef(null)

  useEffect(() => {
    if (lineIndex >= TERMINAL_LINES.length) return
    const line = TERMINAL_LINES[lineIndex]
    if (charIndex <= line.length) {
      const timer = setTimeout(() => {
        setTerminalText(prev => {
          const next = [...prev]
          next[lineIndex] = line.slice(0, charIndex)
          return next
        })
        setCharIndex(c => c + 1)
      }, line.startsWith('$') ? 40 : 18)
      return () => clearTimeout(timer)
    }
    const pause = setTimeout(() => {
      setLineIndex(i => i + 1)
      setCharIndex(0)
    }, line.startsWith('[OK]') ? 300 : 150)
    return () => clearTimeout(pause)
  }, [lineIndex, charIndex])

  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
  }, [terminalText])

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #4f46e5, #7c3aed, #06d6a0)',
        borderRadius: 16, padding: '48px 40px', marginBottom: 32, textAlign: 'center',
      }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, color: '#fff', margin: '0 0 12px' }}>
          Prueba la Plataforma
        </h1>
        <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.85)', margin: 0, maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
          Experimenta el poder del Machine Learning sobre datos cifrados con Encriptacion Homomorfica Completa
        </p>
      </div>

      {/* 3 Step Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 32 }}>
        {STEPS.map((step) => (
          <div key={step.num} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 28, position: 'relative',
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: 10, background: COLORS.primaryLight,
              display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
            }}>
              <svg width="20" height="20" fill="none" stroke={COLORS.primary} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d={step.icon} />
              </svg>
            </div>
            <div style={{
              position: 'absolute', top: 16, right: 16, width: 28, height: 28, borderRadius: '50%',
              background: COLORS.primary, color: '#fff', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 14, fontWeight: 700,
            }}>
              {step.num}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>{step.title}</h3>
            <p style={{ fontSize: 14, color: COLORS.muted, margin: 0, lineHeight: 1.6 }}>{step.desc}</p>
          </div>
        ))}
      </div>

      {/* Live Demo Terminal */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginBottom: 32,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
          Demo en vivo
        </h2>
        <div ref={termRef} style={{
          background: '#0f172a', borderRadius: 10, padding: 20, fontFamily: 'monospace',
          fontSize: 13, color: '#a5f3fc', maxHeight: 340, overflowY: 'auto', lineHeight: 1.8,
        }}>
          {terminalText.map((line, i) => (
            <div key={i} style={{
              color: line.startsWith('$') ? '#fbbf24'
                : line.startsWith('[OK]') ? '#34d399'
                : line.startsWith('  Epoch') ? '#c4b5fd'
                : '#a5f3fc',
            }}>
              {line}
              {i === lineIndex && <span style={{ animation: 'blink 1s step-end infinite' }}>|</span>}
            </div>
          ))}
          {lineIndex < TERMINAL_LINES.length && terminalText.length === 0 && (
            <span style={{ color: '#fbbf24', animation: 'blink 1s step-end infinite' }}>|</span>
          )}
        </div>
        <style>{`@keyframes blink { 50% { opacity: 0 } }`}</style>
      </div>

      {/* 4 Capas de Privacidad */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: COLORS.text, margin: '0 0 8px', textAlign: 'center' }}>
          4 Capas de Privacidad
        </h2>
        <p style={{ fontSize: 15, color: COLORS.muted, margin: '0 0 24px', textAlign: 'center' }}>
          Proteccion integral desde la recoleccion hasta la inferencia
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {PRIVACY_LAYERS.map((layer) => (
            <div key={layer.key} style={{
              background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
              padding: 24, borderTop: `3px solid ${layer.color}`,
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: 10, background: layer.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, fontWeight: 800, color: layer.color, marginBottom: 12,
              }}>
                {layer.title}
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 4px' }}>
                {layer.subtitle}
              </h3>
              <p style={{ fontSize: 13, color: COLORS.muted, margin: 0, lineHeight: 1.6 }}>{layer.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <button style={{
          padding: '14px 36px', borderRadius: 10, border: 'none',
          background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', color: '#fff',
          fontSize: 16, fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 14px rgba(79,70,229,0.4)',
        }}>
          Iniciar Trial Gratis — 14 dias
        </button>
        <p style={{ fontSize: 13, color: COLORS.muted, marginTop: 10 }}>
          Sin tarjeta de credito. Configuracion en 2 minutos.
        </p>
      </div>
    </div>
  )
}

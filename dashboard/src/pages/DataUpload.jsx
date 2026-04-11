import { useState, useEffect } from 'react'

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

const MOCK_PREVIEW = [
  { paciente: 'P-1001', edad: 45, presion: 130, colesterol: 220, glucosa: 110, riesgo: 0.72 },
  { paciente: 'P-1002', edad: 32, presion: 118, colesterol: 185, glucosa: 92, riesgo: 0.31 },
  { paciente: 'P-1003', edad: 58, presion: 145, colesterol: 260, glucosa: 138, riesgo: 0.89 },
  { paciente: 'P-1004', edad: 41, presion: 125, colesterol: 198, glucosa: 105, riesgo: 0.55 },
  { paciente: 'P-1005', edad: 67, presion: 152, colesterol: 275, glucosa: 145, riesgo: 0.93 },
]

const QUALITY_CHECKS = [
  { label: 'Completitud', value: '98.4%', status: 'ok' },
  { label: 'Valores faltantes', value: '8 de 3000', status: 'ok' },
  { label: 'Tipos de datos', value: 'Validados', status: 'ok' },
  { label: 'Duplicados', value: '0 encontrados', status: 'ok' },
  { label: 'Outliers', value: '3 detectados', status: 'warn' },
]

export default function DataUpload() {
  const [phase, setPhase] = useState('idle') // idle | uploading | uploaded | encrypting | done
  const [dragOver, setDragOver] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [encryptProgress, setEncryptProgress] = useState(0)
  const [proofHash, setProofHash] = useState('')

  const usedMB = 42.7
  const totalMB = 100

  const startUpload = () => {
    setPhase('uploading')
    setUploadProgress(0)
  }

  useEffect(() => {
    if (phase !== 'uploading') return
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) { clearInterval(interval); setPhase('uploaded'); return 100 }
        return prev + 5
      })
    }, 80)
    return () => clearInterval(interval)
  }, [phase])

  const startEncrypt = () => {
    setPhase('encrypting')
    setEncryptProgress(0)
  }

  useEffect(() => {
    if (phase !== 'encrypting') return
    const interval = setInterval(() => {
      setEncryptProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setProofHash('0x7a3f...e2b1c4d8f905a6712bcde3401fab890c')
          setPhase('done')
          return 100
        }
        return prev + 4
      })
    }, 100)
    return () => clearInterval(interval)
  }, [phase])

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Subir Datos
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Sube, valida y cifra datasets para entrenamiento FHE
          </p>
        </div>
        {/* Tier usage */}
        <div style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '12px 20px', minWidth: 200 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.text }}>Almacenamiento</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.primary }}>{usedMB} MB / {totalMB} MB</span>
          </div>
          <div style={{ width: '100%', height: 6, background: COLORS.bg, borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ height: '100%', background: usedMB / totalMB > 0.8 ? COLORS.warning : COLORS.primary, width: `${(usedMB / totalMB) * 100}%`, borderRadius: 3 }} />
          </div>
        </div>
      </div>

      {/* Upload zone */}
      {phase === 'idle' && (
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); startUpload() }}
          onClick={startUpload}
          style={{
            background: dragOver ? COLORS.primaryLight : COLORS.card,
            borderRadius: 12, border: `2px dashed ${dragOver ? COLORS.primary : COLORS.border}`,
            padding: '64px 20px', textAlign: 'center', cursor: 'pointer',
            marginBottom: 24, transition: 'all 0.2s',
          }}
        >
          <svg width="56" height="56" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.5} style={{ margin: '0 auto 16px', display: 'block' }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 8px' }}>
            Arrastra tu archivo CSV aqui
          </p>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
            o haz click para seleccionar. Maximo 100 MB por archivo.
          </p>
        </div>
      )}

      {/* Upload progress */}
      {phase === 'uploading' && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28, marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>Subiendo healthcare_data.csv...</span>
            <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.primary }}>{uploadProgress}%</span>
          </div>
          <div style={{ width: '100%', height: 10, background: COLORS.bg, borderRadius: 5, overflow: 'hidden' }}>
            <div style={{ height: '100%', background: COLORS.primary, width: `${uploadProgress}%`, borderRadius: 5, transition: 'width 0.2s' }} />
          </div>
        </div>
      )}

      {/* Post-upload: file info + preview + quality */}
      {(phase === 'uploaded' || phase === 'encrypting' || phase === 'done') && (
        <>
          {/* File info card */}
          <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <svg width="20" height="20" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.success }}>Archivo subido correctamente</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 16 }}>
              {[
                { label: 'Nombre', value: 'healthcare_data.csv' },
                { label: 'Tamanio', value: '2.4 MB' },
                { label: 'Registros', value: '3,000' },
                { label: 'Features', value: '6 columnas' },
              ].map(info => (
                <div key={info.label} style={{ background: COLORS.bg, borderRadius: 8, padding: 14 }}>
                  <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 2px', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>{info.label}</p>
                  <p style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, margin: 0 }}>{info.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Data preview */}
          <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>Vista previa de datos</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                    {['Paciente', 'Edad', 'Presion', 'Colesterol', 'Glucosa', 'Riesgo'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', fontSize: 11, letterSpacing: 0.5 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {MOCK_PREVIEW.map(row => (
                    <tr key={row.paciente} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                      <td style={{ padding: '8px 12px', fontWeight: 500, color: COLORS.primary }}>{row.paciente}</td>
                      <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.edad}</td>
                      <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.presion}</td>
                      <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.colesterol}</td>
                      <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.glucosa}</td>
                      <td style={{ padding: '8px 12px', fontWeight: 600, color: row.riesgo > 0.7 ? COLORS.danger : row.riesgo > 0.5 ? COLORS.warning : COLORS.success }}>{row.riesgo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Quality checks */}
          <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>Control de calidad</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {QUALITY_CHECKS.map(qc => (
                <div key={qc.label} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 0', borderBottom: `1px solid ${COLORS.border}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: qc.status === 'ok' ? COLORS.success : COLORS.warning,
                    }} />
                    <span style={{ fontSize: 14, color: COLORS.text }}>{qc.label}</span>
                  </div>
                  <span style={{
                    fontSize: 13, fontWeight: 600,
                    color: qc.status === 'ok' ? COLORS.success : COLORS.warning,
                  }}>{qc.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Encrypt action */}
          {phase === 'uploaded' && (
            <div style={{ textAlign: 'center', padding: '8px 0' }}>
              <button onClick={startEncrypt} style={{
                padding: '12px 28px', borderRadius: 8, border: 'none',
                background: COLORS.primary, color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer',
              }}>
                Confirmar y Cifrar
              </button>
            </div>
          )}

          {/* Encryption progress */}
          {phase === 'encrypting' && (
            <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>Cifrando con FHE (CKKS 128-bit)...</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.primary }}>{encryptProgress}%</span>
              </div>
              <div style={{ width: '100%', height: 10, background: COLORS.bg, borderRadius: 5, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: `linear-gradient(90deg, ${COLORS.primary}, ${COLORS.accent})`, width: `${encryptProgress}%`, borderRadius: 5, transition: 'width 0.2s' }} />
              </div>
            </div>
          )}

          {/* Success state */}
          {phase === 'done' && (
            <div style={{
              background: COLORS.successLight, borderRadius: 12, border: `1px solid #86efac`,
              padding: 24, textAlign: 'center',
            }}>
              <svg width="40" height="40" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2} style={{ margin: '0 auto 12px', display: 'block' }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: COLORS.success, margin: '0 0 8px' }}>
                Datos cifrados exitosamente
              </h3>
              <p style={{ fontSize: 13, color: COLORS.text, margin: '0 0 4px' }}>Prueba ZKP de integridad generada</p>
              <p style={{
                fontSize: 12, fontFamily: 'monospace', color: COLORS.muted,
                background: '#fff', padding: '8px 16px', borderRadius: 6, display: 'inline-block', marginTop: 8,
              }}>
                Hash: {proofHash}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

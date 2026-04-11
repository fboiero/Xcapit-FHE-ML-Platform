import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { listConsortiums, uploadEncryptedData } from '../api/client'
import { uploadTrialData } from '../api/trial'

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
}

const ALLOWED_TYPES = ['.csv', '.json', '.xlsx']
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50 MB

export default function UploadData() {
  const { id: paramId } = useParams()
  const fileInputRef = useRef(null)

  const [consortiums, setConsortiums] = useState([])
  const [selectedConsortium, setSelectedConsortium] = useState(paramId || '')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [validationResults, setValidationResults] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchConsortiums = async () => {
      try {
        const data = await listConsortiums()
        const list = Array.isArray(data) ? data : data.results || []
        setConsortiums(list)
      } catch (_) { /* fallback */ }
      setLoading(false)
    }
    fetchConsortiums()
  }, [])

  const validateFile = (f) => {
    const errors = []
    const ext = '.' + f.name.split('.').pop().toLowerCase()

    if (!ALLOWED_TYPES.includes(ext)) {
      errors.push(`Formato no soportado: ${ext}. Usa CSV, JSON o XLSX.`)
    }
    if (f.size > MAX_FILE_SIZE) {
      errors.push(`El archivo excede el limite de 50 MB (${(f.size / 1024 / 1024).toFixed(1)} MB).`)
    }
    if (f.size === 0) {
      errors.push('El archivo esta vacio.')
    }

    return {
      valid: errors.length === 0,
      errors,
      fileName: f.name,
      fileSize: f.size,
      fileType: ext,
    }
  }

  const handleFileSelect = (f) => {
    setError('')
    setSuccess(null)
    setValidationResults(null)

    if (!f) return

    const validation = validateFile(f)
    setValidationResults(validation)

    if (validation.valid) {
      setFile(f)
    } else {
      setFile(null)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) handleFileSelect(droppedFile)
  }

  const handleUpload = async () => {
    if (!file || !selectedConsortium) {
      setError('Selecciona un consorcio y un archivo para subir.')
      return
    }

    setUploading(true)
    setError('')
    setProgress(0)

    // Simulate progress since fetch doesn't provide upload progress
    const progressInterval = setInterval(() => {
      setProgress((p) => {
        if (p >= 90) { clearInterval(progressInterval); return 90 }
        return p + Math.random() * 15
      })
    }, 300)

    try {
      let result
      try {
        result = await uploadTrialData(selectedConsortium, file)
      } catch (_) {
        result = await uploadEncryptedData(selectedConsortium, file)
      }

      clearInterval(progressInterval)
      setProgress(100)

      setSuccess({
        message: 'Datos subidos exitosamente',
        details: result,
      })
      setFile(null)
      setValidationResults(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      clearInterval(progressInterval)
      setError(err.message)
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  return (
    <div style={{ padding: 32, maxWidth: 720, margin: '0 auto' }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
        <Link to="/dashboard" style={{ color: COLORS.muted, textDecoration: 'none', fontSize: 14 }}>Dashboard</Link>
        <span style={{ color: COLORS.muted, fontSize: 14 }}>/</span>
        <span style={{ color: COLORS.text, fontSize: 14, fontWeight: 500 }}>Subir datos</span>
      </div>

      <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
        Subir datos
      </h1>
      <p style={{ fontSize: 16, color: COLORS.muted, margin: '0 0 32px' }}>
        Sube tus datos encriptados a un consorcio para entrenamiento colaborativo.
      </p>

      {error && (
        <div style={{
          background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          background: COLORS.successLight, border: '1px solid #bbf7d0', borderRadius: 12,
          padding: 20, marginBottom: 20,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <svg width="20" height="20" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <span style={{ fontSize: 16, fontWeight: 600, color: COLORS.success }}>{success.message}</span>
          </div>
          {success.details && (
            <div style={{ fontSize: 14, color: '#166534' }}>
              {success.details.records && <p style={{ margin: '4px 0' }}>Registros procesados: {success.details.records}</p>}
              {success.details.size && <p style={{ margin: '4px 0' }}>Tamano: {success.details.size}</p>}
              {success.details.status && <p style={{ margin: '4px 0' }}>Estado: {success.details.status}</p>}
            </div>
          )}
        </div>
      )}

      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28,
      }}>
        {/* Consortium selector */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
            Consorcio destino
          </label>
          <select
            value={selectedConsortium}
            onChange={(e) => setSelectedConsortium(e.target.value)}
            disabled={!!paramId}
            style={{
              width: '100%', padding: '12px 16px', border: `1px solid ${COLORS.border}`,
              borderRadius: 10, fontSize: 15, color: selectedConsortium ? COLORS.text : COLORS.muted,
              outline: 'none', boxSizing: 'border-box', background: COLORS.card, cursor: 'pointer',
            }}
          >
            <option value="">Selecciona un consorcio</option>
            {consortiums.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        {/* File drop zone */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 6 }}>
            Archivo de datos
          </label>
          <div
            style={{
              border: `2px dashed ${dragOver ? COLORS.primary : COLORS.border}`,
              borderRadius: 12, padding: '40px 24px', textAlign: 'center',
              background: dragOver ? COLORS.primaryLight : COLORS.bg,
              transition: 'border-color 0.2s, background 0.2s', cursor: 'pointer',
            }}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <svg width="40" height="40" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.5}
              style={{ margin: '0 auto 12px', display: 'block' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p style={{ fontSize: 16, fontWeight: 500, color: COLORS.text, margin: '0 0 6px' }}>
              Arrastra tu archivo aqui o haz clic para seleccionar
            </p>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: 0 }}>
              Formatos soportados: CSV, JSON, XLSX. Maximo 50 MB.
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json,.xlsx"
              onChange={(e) => handleFileSelect(e.target.files[0])}
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {/* Validation results */}
        {validationResults && (
          <div style={{
            background: validationResults.valid ? COLORS.successLight : COLORS.dangerLight,
            borderRadius: 10, padding: 16, marginBottom: 24,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              {validationResults.valid ? (
                <svg width="18" height="18" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg width="18" height="18" fill="none" stroke={COLORS.danger} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              <span style={{
                fontSize: 14, fontWeight: 600,
                color: validationResults.valid ? COLORS.success : COLORS.danger,
              }}>
                {validationResults.valid ? 'Archivo valido' : 'Archivo invalido'}
              </span>
            </div>
            <div style={{ fontSize: 14, color: validationResults.valid ? '#166534' : '#991b1b' }}>
              <p style={{ margin: '2px 0' }}>Nombre: {validationResults.fileName}</p>
              <p style={{ margin: '2px 0' }}>Tamano: {formatSize(validationResults.fileSize)}</p>
              <p style={{ margin: '2px 0' }}>Formato: {validationResults.fileType}</p>
              {validationResults.errors.map((err, idx) => (
                <p key={idx} style={{ margin: '4px 0', fontWeight: 500 }}>{err}</p>
              ))}
            </div>
          </div>
        )}

        {/* Upload progress */}
        {uploading && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>Subiendo...</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.primary }}>{Math.round(progress)}%</span>
            </div>
            <div style={{
              width: '100%', height: 10, background: COLORS.border, borderRadius: 5, overflow: 'hidden',
            }}>
              <div style={{
                height: '100%', background: progress === 100
                  ? COLORS.success
                  : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                borderRadius: 5, width: `${progress}%`, transition: 'width 0.3s ease',
              }} />
            </div>
            <p style={{ fontSize: 13, color: COLORS.muted, marginTop: 6 }}>
              Encriptando y subiendo datos al consorcio...
            </p>
          </div>
        )}

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={uploading || !file || !selectedConsortium}
          style={{
            width: '100%', padding: '14px 0', borderRadius: 10, border: 'none',
            background: (uploading || !file || !selectedConsortium) ? '#a5b4fc' : COLORS.primary,
            color: '#fff', fontSize: 16, fontWeight: 600,
            cursor: (uploading || !file || !selectedConsortium) ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s',
          }}
          onMouseOver={(e) => { if (!uploading && file && selectedConsortium) e.target.style.background = COLORS.primaryHover }}
          onMouseOut={(e) => { if (!uploading && file && selectedConsortium) e.target.style.background = COLORS.primary }}
        >
          {uploading ? 'Subiendo...' : 'Subir datos encriptados'}
        </button>
      </div>

      {/* Info card */}
      <div style={{
        background: COLORS.primaryLight, borderRadius: 12, padding: 20, marginTop: 24,
        border: `1px solid ${COLORS.primary}33`,
      }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 8px' }}>
          Sobre la privacidad de tus datos
        </h3>
        <p style={{ fontSize: 14, color: COLORS.muted, margin: 0, lineHeight: 1.6 }}>
          Tus datos son encriptados con encriptacion homomorfica (FHE) antes de ser enviados al servidor.
          Nunca tenemos acceso a tus datos en texto plano. Solo los parametros del modelo son compartidos
          durante el entrenamiento federado.
        </p>
      </div>
    </div>
  )
}

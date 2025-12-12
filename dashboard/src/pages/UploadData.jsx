import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getConsortium, uploadEncryptedData } from '../api/client'

export default function UploadData() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [consortium, setConsortium] = useState(null)
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    loadConsortium()
  }, [id])

  const loadConsortium = async () => {
    try {
      const data = await getConsortium(id)
      setConsortium(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file) => {
    // Validate file type
    const validTypes = ['text/csv', 'application/json', 'application/octet-stream']
    const validExtensions = ['.csv', '.json', '.enc']

    const hasValidExtension = validExtensions.some(ext =>
      file.name.toLowerCase().endsWith(ext)
    )

    if (!validTypes.includes(file.type) && !hasValidExtension) {
      setError('Formato de archivo no soportado. Usa CSV, JSON o archivos encriptados (.enc)')
      return
    }

    setFile(file)
    setError('')
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadProgress(0)
    setError('')

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      await uploadEncryptedData(id, file, {
        filename: file.name,
        size: file.size,
        uploaded_at: new Date().toISOString(),
      })

      clearInterval(progressInterval)
      setUploadProgress(100)
      setSuccess(true)

      setTimeout(() => {
        navigate(`/consortiums/${id}`)
      }, 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (success) {
    return (
      <div className="pt-16 max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Datos subidos exitosamente!</h2>
          <p className="text-slate-600 mb-6">
            Tu contribucion ha sido agregada al consorcio.
          </p>
          <p className="text-sm text-slate-500">Redirigiendo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pt-16 max-w-2xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link to="/dashboard" className="hover:text-brand-600">Dashboard</Link>
        <span>/</span>
        <Link to={`/consortiums/${id}`} className="hover:text-brand-600">
          {consortium?.name || 'Consorcio'}
        </Link>
        <span>/</span>
        <span className="text-slate-900">Subir Datos</span>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Subir datos encriptados</h1>
        <p className="text-slate-600 mb-8">
          Tus datos seran procesados de forma segura usando encriptacion homomorfica.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Info box */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-blue-900">Encriptacion end-to-end</p>
              <p className="text-sm text-blue-700">
                Tus datos son encriptados localmente antes de subirse. Ningun participante puede ver los datos originales.
              </p>
            </div>
          </div>
        </div>

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
            dragActive
              ? 'border-brand-500 bg-brand-50'
              : file
              ? 'border-green-500 bg-green-50'
              : 'border-slate-300 hover:border-brand-500'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="font-medium text-slate-900">{file.name}</p>
              <p className="text-sm text-slate-500">{formatFileSize(file.size)}</p>
              <button
                onClick={() => setFile(null)}
                className="text-red-600 text-sm hover:text-red-700 mt-2"
              >
                Eliminar
              </button>
            </div>
          ) : (
            <div>
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="font-medium text-slate-900 mb-1">
                Arrastra tu archivo aqui
              </p>
              <p className="text-sm text-slate-500 mb-4">
                o haz clic para seleccionar
              </p>
              <label className="inline-block bg-slate-100 text-slate-700 px-4 py-2 rounded-lg cursor-pointer hover:bg-slate-200 transition">
                <span>Seleccionar archivo</span>
                <input
                  type="file"
                  className="hidden"
                  accept=".csv,.json,.enc"
                  onChange={handleChange}
                />
              </label>
              <p className="text-xs text-slate-400 mt-4">
                Formatos soportados: CSV, JSON, .enc (pre-encriptado)
              </p>
            </div>
          )}
        </div>

        {/* Upload progress */}
        {uploading && (
          <div className="mt-6">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-600">Subiendo y encriptando...</span>
              <span className="text-slate-900 font-medium">{uploadProgress}%</span>
            </div>
            <div className="bg-slate-200 rounded-full h-2">
              <div
                className="bg-brand-600 rounded-full h-2 transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 mt-8">
          <Link
            to={`/consortiums/${id}`}
            className="flex-1 text-center px-4 py-3 border border-slate-300 rounded-xl font-medium hover:bg-slate-50 transition"
          >
            Cancelar
          </Link>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="flex-1 bg-brand-600 text-white px-4 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'Subiendo...' : 'Subir Datos'}
          </button>
        </div>
      </div>
    </div>
  )
}

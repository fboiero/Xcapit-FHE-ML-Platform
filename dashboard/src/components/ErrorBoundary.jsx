import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    import('../lib/sentry.js')
      .then(({ Sentry }) => {
        if (Sentry?.captureException) {
          Sentry.captureException(error, { extra: errorInfo })
        }
      })
      .catch(() => {})
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return typeof this.props.fallback === 'function'
          ? this.props.fallback({ error: this.state.error, reset: this.handleReset })
          : this.props.fallback
      }

      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: '#f8fafc',
          padding: '24px',
        }}>
          <div style={{ textAlign: 'center', maxWidth: '440px' }}>
            <div style={{ fontSize: '3.5rem', marginBottom: '16px' }}>&#9888;</div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1e293b', marginBottom: '8px' }}>
              Algo salio mal
            </h1>
            <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '0.95rem' }}>
              Ocurrio un error inesperado. Intenta de nuevo o vuelve al dashboard.
            </p>
            {this.state.error && (
              <pre style={{
                background: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                padding: '12px',
                fontSize: '0.8rem',
                color: '#991b1b',
                textAlign: 'left',
                overflow: 'auto',
                maxHeight: '120px',
                marginBottom: '24px',
              }}>
                {this.state.error.toString()}
              </pre>
            )}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '12px 24px',
                  background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Reintentar
              </button>
              <button
                onClick={() => { window.location.href = '/dashboard' }}
                style={{
                  padding: '12px 24px',
                  background: '#fff',
                  color: '#4f46e5',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Ir al Dashboard
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

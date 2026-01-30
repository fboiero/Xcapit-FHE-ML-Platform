import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    import('../lib/sentry.js')
      .then(({ Sentry }) => {
        if (Sentry?.captureException) {
          Sentry.captureException(error, { extra: errorInfo })
        }
      })
      .catch(() => {})
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
          <div className="text-center max-w-md">
            <div className="text-5xl mb-4">&#9888;</div>
            <h1 className="text-2xl font-bold text-slate-800 mb-2">
              Something went wrong
            </h1>
            <p className="text-slate-600 mb-6">
              An unexpected error occurred. Please try again or return to the dashboard.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => { window.location.href = '/dashboard' }}
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors"
              >
                Go to Dashboard
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

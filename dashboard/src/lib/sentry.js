import * as Sentry from '@sentry/react'

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
    enabled: import.meta.env.PROD,
    beforeSend(event) {
      if (event.exception?.values?.[0]?.value?.includes('ResizeObserver loop')) {
        return null
      }
      return event
    },
  })
}

export { Sentry }

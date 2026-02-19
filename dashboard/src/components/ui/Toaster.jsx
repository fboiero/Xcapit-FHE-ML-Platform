import { Toaster } from 'sonner'

export default function AppToaster() {
  return (
    <Toaster
      position="top-right"
      duration={4000}
      closeButton
      toastOptions={{
        style: {
          fontFamily: 'Inter, system-ui, sans-serif',
          borderRadius: '0.75rem',
          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
          border: '1px solid',
          padding: '12px 16px',
        },
        classNames: {
          success: 'bg-green-50 border-green-200 text-green-800',
          error: 'bg-red-50 border-red-200 text-red-800',
          warning: 'bg-amber-50 border-amber-200 text-amber-800',
          info: 'bg-blue-50 border-blue-200 text-blue-800',
        },
      }}
    />
  )
}

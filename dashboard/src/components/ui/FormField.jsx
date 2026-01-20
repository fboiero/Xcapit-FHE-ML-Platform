import { forwardRef, useId } from 'react'

/**
 * FormField Component
 *
 * Input con label, error state, y helper text integrados.
 * Accesibilidad incluida: htmlFor, aria-describedby, aria-invalid
 *
 * Props:
 * - label: Texto del label
 * - error: Mensaje de error (muestra estado de error)
 * - helperText: Texto de ayuda
 * - required: Muestra asterisco
 * - type: text, email, password, number, etc.
 */

const baseInputStyles = `
  w-full px-4 py-3
  border rounded-xl
  transition-all duration-200
  focus:outline-none focus:ring-2 focus:ring-offset-0
  disabled:bg-slate-100 disabled:cursor-not-allowed
  placeholder:text-slate-400
`

const inputStates = {
  default: 'border-slate-300 focus:border-brand-500 focus:ring-brand-500',
  error: 'border-red-500 focus:border-red-500 focus:ring-red-500 bg-red-50',
}

const FormField = forwardRef(({
  label,
  error,
  helperText,
  required = false,
  type = 'text',
  className = '',
  ...props
}, ref) => {
  const id = useId()
  const errorId = `${id}-error`
  const helperId = `${id}-helper`

  const hasError = Boolean(error)
  const describedBy = [
    hasError ? errorId : null,
    helperText ? helperId : null,
  ].filter(Boolean).join(' ') || undefined

  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-700 mb-2"
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}

      <input
        ref={ref}
        id={id}
        type={type}
        aria-invalid={hasError}
        aria-describedby={describedBy}
        aria-required={required}
        className={`
          ${baseInputStyles}
          ${hasError ? inputStates.error : inputStates.default}
        `.trim().replace(/\s+/g, ' ')}
        {...props}
      />

      {hasError && (
        <p id={errorId} className="mt-2 text-sm text-red-600 flex items-center gap-1" role="alert">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}

      {helperText && !hasError && (
        <p id={helperId} className="mt-2 text-sm text-slate-500">
          {helperText}
        </p>
      )}
    </div>
  )
})

FormField.displayName = 'FormField'

export default FormField

/**
 * Select Component - Similar styling
 */
export const SelectField = forwardRef(({
  label,
  error,
  helperText,
  required = false,
  options = [],
  placeholder = 'Seleccionar...',
  className = '',
  ...props
}, ref) => {
  const id = useId()
  const errorId = `${id}-error`
  const hasError = Boolean(error)

  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-700 mb-2"
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}

      <select
        ref={ref}
        id={id}
        aria-invalid={hasError}
        aria-describedby={hasError ? errorId : undefined}
        className={`
          ${baseInputStyles}
          ${hasError ? inputStates.error : inputStates.default}
          appearance-none cursor-pointer
          bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')]
          bg-[length:1.5rem_1.5rem]
          bg-[right_0.5rem_center]
          bg-no-repeat
          pr-10
        `.trim().replace(/\s+/g, ' ')}
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {hasError && (
        <p id={errorId} className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {helperText && !hasError && (
        <p className="mt-2 text-sm text-slate-500">
          {helperText}
        </p>
      )}
    </div>
  )
})

SelectField.displayName = 'SelectField'

/**
 * Textarea Component
 */
export const TextareaField = forwardRef(({
  label,
  error,
  helperText,
  required = false,
  rows = 4,
  className = '',
  ...props
}, ref) => {
  const id = useId()
  const errorId = `${id}-error`
  const hasError = Boolean(error)

  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-700 mb-2"
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}

      <textarea
        ref={ref}
        id={id}
        rows={rows}
        aria-invalid={hasError}
        aria-describedby={hasError ? errorId : undefined}
        className={`
          ${baseInputStyles}
          ${hasError ? inputStates.error : inputStates.default}
          resize-none
        `.trim().replace(/\s+/g, ' ')}
        {...props}
      />

      {hasError && (
        <p id={errorId} className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {helperText && !hasError && (
        <p className="mt-2 text-sm text-slate-500">
          {helperText}
        </p>
      )}
    </div>
  )
})

TextareaField.displayName = 'TextareaField'

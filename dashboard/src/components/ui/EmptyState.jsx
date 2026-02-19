import { Link } from 'react-router-dom'

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
      {Icon && (
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Icon className="w-8 h-8 text-slate-400" />
        </div>
      )}
      <h3 className="text-lg font-medium text-slate-900 mb-2">{title}</h3>
      {description && (
        <p className="text-slate-600 mb-6">{description}</p>
      )}
      {action && action.to && (
        <Link
          to={action.to}
          className="inline-flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-brand-700 transition"
        >
          {action.icon && <action.icon className="w-5 h-5" />}
          {action.label}
        </Link>
      )}
      {action && action.onClick && !action.to && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-brand-700 transition"
        >
          {action.icon && <action.icon className="w-5 h-5" />}
          {action.label}
        </button>
      )}
    </div>
  )
}

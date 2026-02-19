const variants = {
  default: (
    <>
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-slate-200 rounded-xl"></div>
        <div className="w-20 h-6 bg-slate-200 rounded-full"></div>
      </div>
      <div className="h-5 bg-slate-200 rounded w-3/4 mb-3"></div>
      <div className="h-4 bg-slate-200 rounded w-full mb-2"></div>
      <div className="h-4 bg-slate-200 rounded w-2/3 mb-4"></div>
      <div className="flex gap-4">
        <div className="h-4 bg-slate-200 rounded w-20"></div>
        <div className="h-4 bg-slate-200 rounded w-24"></div>
      </div>
    </>
  ),
  stat: (
    <>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-4 h-4 bg-slate-200 rounded"></div>
        <div className="h-3 bg-slate-200 rounded w-20"></div>
      </div>
      <div className="h-8 bg-slate-200 rounded w-16"></div>
    </>
  ),
  'list-item': (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 bg-slate-200 rounded-lg"></div>
      <div className="flex-1">
        <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-slate-200 rounded w-1/2"></div>
      </div>
    </div>
  ),
}

export default function SkeletonCard({ variant = 'default', className = '' }) {
  return (
    <div className={`bg-white rounded-2xl border border-slate-200 p-6 animate-pulse ${className}`}>
      {variants[variant] || variants.default}
    </div>
  )
}

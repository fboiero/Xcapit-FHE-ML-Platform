import { useState, useEffect, useRef } from 'react'

function useAnimatedCounter(end, duration = 2000, isVisible = true) {
  const [count, setCount] = useState(0)
  const [hasStarted, setHasStarted] = useState(false)

  useEffect(() => {
    if (!isVisible || hasStarted) return
    setHasStarted(true)
    const startTime = Date.now()
    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const numericValue = parseFloat(end.replace(/[^0-9.-]/g, ''))
      setCount(Math.floor(progress * numericValue))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [end, duration, isVisible, hasStarted])

  const suffix = end.replace(/[0-9.-]/g, '')
  const prefix = end.startsWith('$') ? '$' : ''
  return prefix + count + suffix.replace('$', '')
}

function MetricCard({ value, label, color = 'red', delay = 0, isVisible = true }) {
  const animatedValue = useAnimatedCounter(value, 2000, isVisible)
  const colorClasses = {
    red: 'from-red-500/20 to-red-600/20 border-red-500/30 text-red-400',
    amber: 'from-amber-500/20 to-amber-600/20 border-amber-500/30 text-amber-400',
    orange: 'from-orange-500/20 to-orange-600/20 border-orange-500/30 text-orange-400'
  }

  return (
    <div
      className={`bg-gradient-to-br ${colorClasses[color]} border rounded-2xl p-6 text-center transform transition-all duration-500`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.95)',
        transitionDelay: `${delay}ms`
      }}
    >
      <div className="text-4xl md:text-5xl font-bold mb-2">{animatedValue}</div>
      <p className="text-slate-300 text-sm">{label}</p>
    </div>
  )
}

export default function CostOfInactionCard({ title, subtitle, metrics = [], lang = 'es' }) {
  const ref = useRef(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.unobserve(entry.target)
        }
      },
      { threshold: 0.2 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  const defaultContent = {
    es: { title: 'El costo de no actuar', subtitle: 'Lo que pierdes cada día sin colaboración segura' },
    en: { title: 'The cost of inaction', subtitle: 'What you lose every day without secure collaboration' },
    de: { title: 'Die Kosten des Nichthandelns', subtitle: 'Was Sie jeden Tag ohne sichere Zusammenarbeit verlieren' }
  }
  const t = defaultContent[lang] || defaultContent.es

  return (
    <div ref={ref} className="py-8">
      <div className="text-center mb-10" style={{ opacity: isVisible ? 1 : 0, transform: isVisible ? 'translateY(0)' : 'translateY(20px)', transition: 'all 0.6s ease' }}>
        <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">{title || t.title}</h3>
        <p className="text-slate-400">{subtitle || t.subtitle}</p>
      </div>
      <div className="grid md:grid-cols-3 gap-6">
        {metrics.map((metric, index) => (
          <MetricCard key={index} value={metric.value} label={metric.label} color={metric.color || 'red'} delay={index * 150} isVisible={isVisible} />
        ))}
      </div>
    </div>
  )
}

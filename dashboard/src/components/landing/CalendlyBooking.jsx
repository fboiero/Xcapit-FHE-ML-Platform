import { useState } from 'react'

export function CalendlyButton({ text, color = 'blue', className = '' }) {
  const handleClick = () => {
    if (window.Calendly) {
      window.Calendly.initPopupWidget({ url: 'https://calendly.com/xcapit-privacy/demo' })
    } else {
      window.open('https://calendly.com/xcapit-privacy/demo', '_blank')
    }
  }

  const colorClasses = {
    blue: 'bg-blue-600 hover:bg-blue-700',
    emerald: 'bg-emerald-600 hover:bg-emerald-700',
    slate: 'bg-slate-600 hover:bg-slate-700',
    purple: 'bg-purple-600 hover:bg-purple-700',
    brand: 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700'
  }

  return (
    <>
      <link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet" />
      <script src="https://assets.calendly.com/assets/external/widget.js" type="text/javascript" async></script>
      <button
        onClick={handleClick}
        className={`${colorClasses[color]} text-white font-semibold px-8 py-4 rounded-xl transition-all hover:scale-105 shadow-lg ${className}`}
      >
        {text}
      </button>
    </>
  )
}

export default function CalendlyBooking({ lang = 'es', color = 'blue', title, subtitle }) {
  const [showFallback, setShowFallback] = useState(false)
  const [formData, setFormData] = useState({ name: '', email: '', company: '', message: '' })
  const [status, setStatus] = useState('idle')

  const content = {
    es: { title: 'Agenda tu demo personalizada', subtitle: 'Reserva 30 minutos con nuestro equipo', button: 'Agendar Demo', fallbackTitle: '¿Preferís que te contactemos?', fallbackButton: 'Enviar solicitud', name: 'Nombre', email: 'Email', company: 'Empresa', message: 'Mensaje (opcional)', sending: 'Enviando...', success: '¡Enviado! Te contactamos pronto.' },
    en: { title: 'Schedule your personalized demo', subtitle: 'Book 30 minutes with our team', button: 'Schedule Demo', fallbackTitle: 'Prefer us to contact you?', fallbackButton: 'Send request', name: 'Name', email: 'Email', company: 'Company', message: 'Message (optional)', sending: 'Sending...', success: 'Sent! We will contact you soon.' },
    de: { title: 'Vereinbaren Sie Ihre persönliche Demo', subtitle: 'Buchen Sie 30 Minuten mit unserem Team', button: 'Demo vereinbaren', fallbackTitle: 'Möchten Sie, dass wir Sie kontaktieren?', fallbackButton: 'Anfrage senden', name: 'Name', email: 'E-Mail', company: 'Unternehmen', message: 'Nachricht (optional)', sending: 'Senden...', success: 'Gesendet! Wir melden uns bald.' }
  }
  const t = content[lang] || content.es

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')
    try {
      await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'd7f419bc-95cf-498d-8d8b-5f4830622bf4',
          subject: `Demo Request - ${formData.company} - Xcapit Privacy`,
          from_name: formData.name,
          ...formData
        }),
      })
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  const colorClasses = {
    blue: 'from-blue-600 to-indigo-600',
    emerald: 'from-emerald-600 to-teal-600',
    slate: 'from-slate-600 to-slate-700',
    purple: 'from-purple-600 to-indigo-600',
    brand: 'from-blue-600 to-indigo-600'
  }

  return (
    <div className="text-center">
      <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{title || t.title}</h2>
      <p className="text-xl text-slate-300 mb-8">{subtitle || t.subtitle}</p>
      
      <div className="flex flex-col items-center gap-6">
        <CalendlyButton text={t.button} color={color} className="text-lg" />
        
        <button onClick={() => setShowFallback(!showFallback)} className="text-slate-400 hover:text-white text-sm underline">
          {t.fallbackTitle}
        </button>

        {showFallback && (
          <form onSubmit={handleSubmit} className="w-full max-w-md bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 mt-4">
            <div className="space-y-4">
              <input type="text" placeholder={t.name} value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-white/40" />
              <input type="email" placeholder={t.email} value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-white/40" />
              <input type="text" placeholder={t.company} value={formData.company} onChange={(e) => setFormData({...formData, company: e.target.value})} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-white/40" />
              <textarea placeholder={t.message} value={formData.message} onChange={(e) => setFormData({...formData, message: e.target.value})} rows={3} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-white/40 resize-none" />
              <button type="submit" disabled={status === 'sending'} className={`w-full py-3 bg-gradient-to-r ${colorClasses[color]} text-white font-semibold rounded-lg hover:opacity-90 transition disabled:opacity-50`}>
                {status === 'sending' ? t.sending : status === 'success' ? t.success : t.fallbackButton}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

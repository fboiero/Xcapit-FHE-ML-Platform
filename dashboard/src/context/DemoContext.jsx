import { createContext, useContext, useState } from 'react'

// Re-export demo constants so SandboxDemo can import from a single source
export { DEMO_API_KEY } from '../config/demo'

// Sample company for demo scenarios
export const ACME_CORP = {
  name: 'Acme Corp',
  industry: 'banking',
  employees: 5000,
  country: 'AR',
}

// Industry scenario definitions used by SandboxDemo
export const INDUSTRY_SCENARIOS = {
  finance: {
    name: 'Banca y Finanzas',
    nameEn: 'Banking & Finance',
    icon: 'BuildingOffice2Icon',
    color: 'blue',
    description: 'Deteccion de fraude cross-banco sin compartir datos de clientes',
    descriptionEn: 'Cross-bank fraud detection without sharing customer data',
    demoPath: '/demo-consorcio',
    metrics: { accuracy: '94.7%', latency: '< 2s', members: 3 },
  },
  healthcare: {
    name: 'Salud',
    nameEn: 'Healthcare',
    icon: 'HeartIcon',
    color: 'red',
    description: 'Diagnostico cross-hospital preservando privacidad de pacientes',
    descriptionEn: 'Cross-hospital diagnostics preserving patient privacy',
    demoPath: '/demo-consorcio',
    metrics: { accuracy: '91.2%', latency: '< 3s', members: 4 },
  },
  retail: {
    name: 'Retail',
    nameEn: 'Retail',
    icon: 'ShoppingBagIcon',
    color: 'green',
    description: 'Prediccion de churn combinando datos de multiples cadenas',
    descriptionEn: 'Churn prediction combining data from multiple retail chains',
    demoPath: '/demo-consorcio',
    metrics: { accuracy: '89.5%', latency: '< 1s', members: 5 },
  },
  insurance: {
    name: 'Seguros',
    nameEn: 'Insurance',
    icon: 'ShieldCheckIcon',
    color: 'purple',
    description: 'Deteccion de fraude en siniestros cross-aseguradora',
    descriptionEn: 'Cross-insurer claims fraud detection',
    demoPath: '/demo-consorcio',
    metrics: { accuracy: '92.1%', latency: '< 2s', members: 3 },
  },
}

const DemoContext = createContext({
  isDemoMode: false,
  setDemoMode: () => {},
  demoEmail: null,
  setDemoEmail: () => {},
})

export function DemoProvider({ children }) {
  const [isDemoMode, setDemoMode] = useState(false)
  const [demoEmail, setDemoEmail] = useState(null)

  return (
    <DemoContext.Provider value={{ isDemoMode, setDemoMode, demoEmail, setDemoEmail }}>
      {children}
    </DemoContext.Provider>
  )
}

export function useDemo() {
  return useContext(DemoContext)
}

export default DemoContext

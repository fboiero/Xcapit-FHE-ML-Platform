import { createContext, useContext, useState, useEffect } from 'react'

import { DEMO_API_KEY, DEMO_EMAIL } from '../config/demo'
export { DEMO_API_KEY, DEMO_EMAIL }

// Industry scenarios with complete mock data
export const INDUSTRY_SCENARIOS = {
  finance: {
    id: 'finance',
    name: 'Servicios Financieros',
    nameEn: 'Financial Services',
    icon: 'BuildingOffice2Icon',
    color: 'indigo',
    description: 'Deteccion de fraude y scoring crediticio colaborativo',
    descriptionEn: 'Collaborative fraud detection and credit scoring',
    client: {
      name: 'FinBank Corp',
      logo: 'FB',
      industry: 'Banking & Finance',
      employees: '2,500+',
      region: 'Latin America'
    },
    consortiums: [
      {
        id: 'cons_fraud_detection',
        name: 'Consorcio Anti-Fraude LATAM',
        description: 'Deteccion colaborativa de fraude entre 5 bancos',
        model_type: 'logistic_regression',
        status: 'training',
        members: 5,
        data_contributions: 12,
        accuracy: 94.2,
        created_at: '2024-11-15T10:00:00Z'
      },
      {
        id: 'cons_credit_scoring',
        name: 'Credit Scoring Colaborativo',
        description: 'Modelo de scoring usando datos de multiples instituciones',
        model_type: 'neural_network',
        status: 'active',
        members: 3,
        data_contributions: 8,
        accuracy: 91.5,
        created_at: '2024-10-20T10:00:00Z'
      }
    ],
    stats: {
      totalTransactions: '4.2M',
      fraudDetected: '$12.4M',
      fraudRate: '0.02%',
      modelAccuracy: '94.2%',
      partnersActive: 5,
      dataPointsEncrypted: '150M+'
    },
    recentActivity: [
      { action: 'Model retrained', time: '2 hours ago', type: 'success' },
      { action: 'New data contribution from Banco Beta', time: '5 hours ago', type: 'data' },
      { action: 'Fraud alert: 23 suspicious transactions', time: '1 day ago', type: 'alert' }
    ]
  },
  healthcare: {
    id: 'healthcare',
    name: 'Salud',
    nameEn: 'Healthcare',
    icon: 'HeartIcon',
    color: 'rose',
    description: 'Investigacion medica y prediccion de riesgos',
    descriptionEn: 'Medical research and risk prediction',
    client: {
      name: 'MedResearch Institute',
      logo: 'MR',
      industry: 'Healthcare & Research',
      employees: '800+',
      region: 'Global'
    },
    consortiums: [
      {
        id: 'cons_diabetes_prediction',
        name: 'Prediccion Diabetes T2',
        description: 'Modelo predictivo usando datos de 3 hospitales',
        model_type: 'neural_network',
        status: 'active',
        members: 3,
        data_contributions: 6,
        accuracy: 89.3,
        created_at: '2024-09-10T10:00:00Z'
      },
      {
        id: 'cons_cancer_research',
        name: 'Investigacion Oncologica',
        description: 'Analisis colaborativo de datos de cancer',
        model_type: 'decision_tree',
        status: 'pending',
        members: 4,
        data_contributions: 0,
        accuracy: null,
        created_at: '2024-12-01T10:00:00Z'
      }
    ],
    stats: {
      totalPatients: '125K',
      conditionsTracked: 156,
      predictionAccuracy: '89.3%',
      hospitalsParticipating: 3,
      recordsEncrypted: '2.1M',
      researchProjects: 12
    },
    recentActivity: [
      { action: 'New diabetes prediction model deployed', time: '1 day ago', type: 'success' },
      { action: 'Hospital Norte joined consortium', time: '3 days ago', type: 'member' },
      { action: 'Data quality check passed', time: '1 week ago', type: 'data' }
    ]
  },
  retail: {
    id: 'retail',
    name: 'Retail',
    nameEn: 'Retail',
    icon: 'ShoppingBagIcon',
    color: 'purple',
    description: 'Analisis de clientes y prediccion de comportamiento',
    descriptionEn: 'Customer analytics and behavior prediction',
    client: {
      name: 'RetailGroup LATAM',
      logo: 'RG',
      industry: 'Retail & E-commerce',
      employees: '5,000+',
      region: 'South America'
    },
    consortiums: [
      {
        id: 'cons_churn_prediction',
        name: 'Prediccion de Churn',
        description: 'Modelo colaborativo para predecir abandono de clientes',
        model_type: 'logistic_regression',
        status: 'active',
        members: 4,
        data_contributions: 10,
        accuracy: 87.6,
        created_at: '2024-08-15T10:00:00Z'
      }
    ],
    stats: {
      totalCustomers: '2.5M',
      transactionsAnalyzed: '45M',
      churnReduction: '23%',
      partnersActive: 4,
      revenueProtected: '$8.2M',
      segmentsIdentified: 12
    },
    recentActivity: [
      { action: 'Q4 model update completed', time: '12 hours ago', type: 'success' },
      { action: 'New customer segment identified', time: '2 days ago', type: 'data' }
    ]
  },
  insurance: {
    id: 'insurance',
    name: 'Seguros',
    nameEn: 'Insurance',
    icon: 'ShieldCheckIcon',
    color: 'emerald',
    description: 'Evaluacion de riesgos y deteccion de fraude',
    descriptionEn: 'Risk assessment and fraud detection',
    client: {
      name: 'SecureLife Insurance',
      logo: 'SL',
      industry: 'Insurance',
      employees: '1,200+',
      region: 'Americas'
    },
    consortiums: [
      {
        id: 'cons_claims_fraud',
        name: 'Deteccion Fraude en Reclamos',
        description: 'Identificacion de reclamos fraudulentos',
        model_type: 'neural_network',
        status: 'active',
        members: 6,
        data_contributions: 15,
        accuracy: 92.1,
        created_at: '2024-07-01T10:00:00Z'
      }
    ],
    stats: {
      claimsProcessed: '890K',
      fraudPrevented: '$15.2M',
      processingTime: '-45%',
      partnersActive: 6,
      accuracyRate: '92.1%',
      falsePositives: '2.3%'
    },
    recentActivity: [
      { action: 'Monthly fraud report generated', time: '6 hours ago', type: 'success' },
      { action: 'New insurer joined network', time: '4 days ago', type: 'member' }
    ]
  }
}

// Acme Corp - Complete fictional client for demos
export const ACME_CORP = {
  id: 'company_acme_demo',
  name: 'Acme Corporation',
  email: 'demo@acme-corp.com',
  logo: 'AC',
  industry: 'Technology & Finance',
  description: 'Leading fintech company exploring privacy-preserving ML',
  employees: '500+',
  region: 'Global',
  plan: 'Enterprise',
  joined: '2024-06-01T00:00:00Z',
  stats: {
    consortiumsActive: 3,
    dataContributions: 15,
    modelsTraining: 2,
    totalEncryptedRecords: '5.2M'
  },
  consortiums: [
    INDUSTRY_SCENARIOS.finance.consortiums[0],
    INDUSTRY_SCENARIOS.finance.consortiums[1],
    INDUSTRY_SCENARIOS.healthcare.consortiums[0]
  ]
}

const DemoContext = createContext(null)

export function DemoProvider({ children }) {
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [currentScenario, setCurrentScenario] = useState('finance')
  const [demoClient, setDemoClient] = useState(ACME_CORP)

  // Check if using demo credentials
  useEffect(() => {
    const apiKey = localStorage.getItem('xcapit_api_key')
    if (apiKey === DEMO_API_KEY) {
      setIsDemoMode(true)
    }
  }, [])

  const enableDemoMode = (scenario = 'finance') => {
    localStorage.setItem('xcapit_api_key', DEMO_API_KEY)
    localStorage.setItem('xcapit_demo_scenario', scenario)
    setIsDemoMode(true)
    setCurrentScenario(scenario)
  }

  const disableDemoMode = () => {
    localStorage.removeItem('xcapit_api_key')
    localStorage.removeItem('xcapit_demo_scenario')
    setIsDemoMode(false)
  }

  const switchScenario = (scenarioId) => {
    if (INDUSTRY_SCENARIOS[scenarioId]) {
      setCurrentScenario(scenarioId)
      localStorage.setItem('xcapit_demo_scenario', scenarioId)
      // Update demo client based on scenario
      setDemoClient({
        ...INDUSTRY_SCENARIOS[scenarioId].client,
        id: `company_${scenarioId}_demo`,
        email: `demo@${scenarioId}.xcapit.com`,
        consortiums: INDUSTRY_SCENARIOS[scenarioId].consortiums
      })
    }
  }

  const getScenarioData = () => {
    return INDUSTRY_SCENARIOS[currentScenario]
  }

  const value = {
    isDemoMode,
    currentScenario,
    demoClient,
    scenarios: INDUSTRY_SCENARIOS,
    enableDemoMode,
    disableDemoMode,
    switchScenario,
    getScenarioData,
    DEMO_API_KEY,
    DEMO_EMAIL,
    ACME_CORP
  }

  return (
    <DemoContext.Provider value={value}>
      {children}
    </DemoContext.Provider>
  )
}

export function useDemo() {
  const context = useContext(DemoContext)
  if (!context) {
    throw new Error('useDemo must be used within a DemoProvider')
  }
  return context
}

export default DemoContext

/**
 * Test data factories — datos sinteticos para flows E2E.
 *
 * IMPORTANTE: Nunca usar datos reales ni copiar de produccion.
 * Cada test genera sus propios datos via estas factories.
 */

export function uniqueSuffix() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function newConsortium(overrides = {}) {
  const suffix = uniqueSuffix()
  return {
    name: `E2E Consortium ${suffix}`,
    description: 'Automated E2E test consortium',
    industry: 'banking',
    min_members: 2,
    max_members: 10,
    ...overrides,
  }
}

export function newCompany(overrides = {}) {
  const suffix = uniqueSuffix()
  return {
    name: `E2E Company ${suffix}`,
    email: `company-${suffix}@xcapit.test`,
    industry: 'banking',
    ...overrides,
  }
}

/**
 * Datos sinteticos para upload de dataset (CSV).
 * Pequeno, para no saturar el backend durante E2E.
 */
export function sampleBankingCSV() {
  const header = 'amount,hour,distance_km,is_online,is_fraud'
  const rows = [
    '523.45,14,25.3,false,false',
    '1850.00,03,1200.5,true,true',
    '42.10,18,3.2,false,false',
    '99.99,02,800.0,true,true',
    '250.00,12,10.0,false,false',
  ]
  return [header, ...rows].join('\n')
}

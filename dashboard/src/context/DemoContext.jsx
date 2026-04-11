import { createContext, useContext, useState } from 'react'

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

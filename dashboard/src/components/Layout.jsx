import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import Breadcrumbs from './Breadcrumbs'
import { AppToaster } from './ui'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)
  const closeSidebar = () => setSidebarOpen(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar onMenuClick={toggleSidebar} />
      <AppToaster />

      <div className="flex">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-slate-900/50 z-30 md:hidden"
            onClick={closeSidebar}
            aria-hidden="true"
          />
        )}

        <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />

        {/* Main content - responsive margin */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 md:ml-64 min-h-[calc(100vh-4rem)]">
          <Breadcrumbs />
          <Outlet />
        </main>
      </div>
    </div>
  )
}

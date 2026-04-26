import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0b0e14]">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(o => !o)} />
      <div
        className="flex-1 flex flex-col min-w-0 sidebar-transition"
        style={{ marginLeft: sidebarOpen ? '18rem' : '5rem' }}
      >
        <Header />
        <main className="flex-1 overflow-auto custom-scrollbar p-6 bg-[radial-gradient(circle_at_top_right,_#1a1f2b,_#0b0e14)]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
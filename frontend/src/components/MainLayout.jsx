import { Outlet, useNavigate } from 'react-router-dom'
import { LogOut, Bell } from 'lucide-react'
import MediLogo from './MediLogo'

export default function MainLayout() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-[#0b0e14]">
      <header className="h-16 bg-[#0B0E14]/90 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <MediLogo size={36} />
          <div>
            <span className="font-bold text-lg tracking-wider text-white">MEDICORE</span>
            <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold leading-none">AI 정밀 진단 시스템</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="text-slate-400 hover:text-blue-400 transition-colors">
            <Bell size={20} />
          </button>
          <div className="flex items-center gap-3 border-l border-slate-700 pl-4">
            <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center text-blue-400 text-sm font-bold">
              {user.name ? user.name[0] : 'M'}
            </div>
            {user.name && (
              <div className="hidden sm:block">
                <p className="text-sm font-semibold text-slate-200">{user.name}</p>
                <p className="text-[10px] text-slate-500">{user.email || '의료진'}</p>
              </div>
            )}
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all text-sm font-medium border border-slate-700 hover:border-red-500/30"
          >
            <LogOut size={16} />
            로그아웃
          </button>
        </div>
      </header>

      <main className="p-6 bg-[radial-gradient(circle_at_top_right,_#1a1f2b,_#0b0e14)] min-h-[calc(100vh-4rem)]">
        <Outlet />
      </main>
    </div>
  )
}
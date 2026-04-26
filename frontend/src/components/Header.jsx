import { Bell } from 'lucide-react'

export default function Header() {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const initial = user.name ? user.name[0] : 'M'

  return (
    <header className="h-16 flex-shrink-0 bg-[#0B0E14]/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-40">
      <div>
        <span className="text-[10px] text-blue-500 font-bold tracking-[0.2em] uppercase">AI Diagnostics System</span>
        <h2 className="text-sm font-medium text-slate-400">MediCore 통합 진단 플랫폼</h2>
      </div>

      <div className="flex items-center gap-4">
        <button className="text-slate-400 hover:text-blue-400 transition-colors relative">
          <Bell size={20} />
        </button>

        <div className="flex items-center gap-3 border-l border-slate-700 pl-4">
          <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center text-blue-400 text-sm font-bold">
            {initial}
          </div>
          {user.name && (
            <div className="hidden sm:block">
              <p className="text-sm font-semibold text-slate-200">{user.name}</p>
              <p className="text-[10px] text-slate-500">{user.email || '의료진'}</p>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
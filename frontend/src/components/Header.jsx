import { Bell, UserPlus } from 'lucide-react'

export default function Header({ title = 'MediCore 통합 분석 플랫폼', patientName, patientStatus }) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  return (
    <header className="h-20 flex-shrink-0 bg-[#0B0E14]/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-40 shadow-lg shadow-blue-900/10">
      <div className="flex items-center gap-4">
        <div>
          <span className="text-[10px] text-blue-500 font-bold tracking-[0.2em] uppercase">AI Diagnostics System</span>
          <h2 className="text-lg font-medium text-slate-200">{title}</h2>
        </div>
        {patientName && (
          <>
            <div className="h-6 w-px bg-slate-700" />
            <div className="flex items-center gap-3">
              <span className="text-slate-200 font-medium">{patientName}</span>
              {patientStatus && (
                <span className="px-2 py-0.5 rounded-full border border-emerald-500/50 text-emerald-400 text-[10px] font-bold bg-emerald-500/5 flex items-center gap-1 uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                  {patientStatus}
                </span>
              )}
            </div>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        <button className="px-4 py-2 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 glow-blue">
          <UserPlus size={16} />
          환자 등록
        </button>
        <div className="flex items-center gap-3 border-l border-slate-700 pl-4">
          <button className="text-slate-400 hover:text-blue-400 transition-colors">
            <Bell size={20} />
          </button>
          <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center text-blue-400 text-sm font-bold">
            {user.name ? user.name[0] : 'M'}
          </div>
        </div>
      </div>
    </header>
  )
}
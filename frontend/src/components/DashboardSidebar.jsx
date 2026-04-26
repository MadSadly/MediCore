import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Settings, LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import MediLogo from './MediLogo'

const NAV_ITEMS = [
  { path: '/dashboard', label: '통합 대시보드', icon: LayoutDashboard },
]

export default function DashboardSidebar({ open, onToggle }) {
  const location = useLocation()
  const navigate = useNavigate()

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <aside
      className={`sidebar-transition ${open ? 'w-72' : 'w-20'} h-screen fixed left-0 top-0 bg-[#151921] border-r border-slate-800 flex flex-col z-50`}
    >
      {/* Logo */}
      <div className="h-20 flex-shrink-0 flex items-center px-5 border-b border-slate-800 overflow-hidden">
        <div className="flex-shrink-0">
          <MediLogo size={open ? 40 : 36} />
        </div>
        {open && (
          <div className="ml-3">
            <span className="font-bold text-xl tracking-wider text-white">MEDICORE</span>
            <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold">정밀 진단 시스템</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const active = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              title={!open ? item.label : undefined}
              className={`flex items-center p-3 rounded-xl transition-all ${
                active
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              <Icon size={20} className="flex-shrink-0" />
              {open && (
                <div className="ml-4 min-w-0">
                  <p className="text-sm font-semibold whitespace-nowrap">{item.label}</p>
                </div>
              )}
            </Link>
          )
        })}

        {/* 구분선 + 안내 */}
        {open && (
          <div className="pt-4 px-1">
            <p className="text-[10px] text-slate-600 uppercase font-bold tracking-widest mb-3">질환별 분석</p>
            <div className="p-3 rounded-lg border border-dashed border-slate-800 text-center">
              <p className="text-xs text-slate-600">환자를 선택하면</p>
              <p className="text-xs text-slate-600">질환 분석 메뉴가 열립니다</p>
            </div>
          </div>
        )}
      </nav>

      {/* Bottom */}
      <div className="flex-shrink-0 border-t border-slate-800 p-3 space-y-1">
        <Link
          to="/settings"
          title={!open ? '설정' : undefined}
          className="flex items-center p-3 rounded-xl text-slate-400 hover:bg-slate-800 transition-all"
        >
          <Settings size={20} className="flex-shrink-0" />
          {open && <span className="ml-4 text-sm font-semibold">설정</span>}
        </Link>
        <button
          onClick={logout}
          title={!open ? '로그아웃' : undefined}
          className="w-full flex items-center p-3 rounded-xl text-slate-400 hover:bg-slate-800 transition-all"
        >
          <LogOut size={20} className="flex-shrink-0" />
          {open && <span className="ml-4 text-sm font-semibold">로그아웃</span>}
        </button>
      </div>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-24 bg-blue-600 rounded-full p-1 border-2 border-[#0B0E14] text-white hover:scale-110 transition-transform shadow-lg z-30"
      >
        {open ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
      </button>
    </aside>
  )
}

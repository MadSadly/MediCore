import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Brain, Columns2, Circle, Shield, Eye, LayoutDashboard,
  Settings, LogOut, ChevronLeft, ChevronRight, Activity,
} from 'lucide-react'
import MediLogo from './MediLogo'

const DISEASE_TABS = [
  { key: 'overview',       label: '통합 대시보드',  sub: '환자 종합 정보', icon: LayoutDashboard },
  { key: 'brain-tumor',    label: '뇌종양 진단',    sub: '변운조',          icon: Brain           },
  { key: 'spine-disk',     label: '허리디스크',     sub: '김담현',          icon: Columns2        },
  { key: 'colon-cancer',   label: '대장암 예측',    sub: '박기완',          icon: Circle          },
  { key: 'kidney-failure', label: '신부전 관리',    sub: '김남준',          icon: Shield          },
  { key: 'skin-disease',   label: '피부질환 분류',  sub: '김민수',          icon: Activity        },
  { key: 'eye-disease',    label: '안과 질환',      sub: '홍승현',          icon: Eye             },
]

export default function PatientSidebar({ patientId, patientName, open, onToggle }) {
  const location = useLocation()
  const navigate = useNavigate()

  const getPath = (key) =>
    key === 'overview' ? `/patients/${patientId}` : `/patients/${patientId}/${key}`

  const isActive = (key) => {
    const path = getPath(key)
    if (key === 'overview') {
      return location.pathname === path
    }
    return location.pathname.startsWith(path)
  }

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
      <div className="h-16 flex-shrink-0 flex items-center px-5 border-b border-slate-800 overflow-hidden">
        <div className="flex-shrink-0">
          <MediLogo size={open ? 36 : 32} />
        </div>
        {open && (
          <div className="ml-3">
            <span className="font-bold text-lg tracking-wider text-white">MEDICORE</span>
            <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold">정밀 진단 시스템</p>
          </div>
        )}
      </div>

      {/* 환자 컨텍스트 배너 */}
      {open && (
        <div className="mx-3 mt-3 px-3 py-2.5 bg-blue-600/10 border border-blue-600/20 rounded-lg">
          <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest mb-0.5">현재 환자</p>
          <p className="text-sm text-slate-200 font-semibold truncate">{patientName || patientId}</p>
          <p className="text-[10px] text-slate-500 truncate">{patientId}</p>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        {!open && (
          <div className="mx-auto w-8 h-8 mb-3 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center">
            <span className="text-blue-400 text-xs font-bold">
              {(patientName || patientId || '?')[0]}
            </span>
          </div>
        )}
        {DISEASE_TABS.map(({ key, label, sub, icon: Icon }) => {
          const active = isActive(key)
          return (
            <Link
              key={key}
              to={getPath(key)}
              title={!open ? label : undefined}
              className={`flex items-center p-3 rounded-xl transition-all ${
                active
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              <Icon size={20} className="flex-shrink-0" />
              {open && (
                <div className="ml-4 min-w-0">
                  <p className="text-sm font-semibold whitespace-nowrap">{label}</p>
                  <p className="text-[10px] text-slate-500 whitespace-nowrap">{sub}</p>
                </div>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="flex-shrink-0 border-t border-slate-800 p-3 space-y-1">
        <Link
          to="/dashboard"
          title={!open ? '환자 목록' : undefined}
          className="flex items-center p-3 rounded-xl text-slate-400 hover:bg-slate-800 transition-all"
        >
          <LayoutDashboard size={20} className="flex-shrink-0" />
          {open && <span className="ml-4 text-sm font-semibold">← 환자 목록</span>}
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

      {/* Toggle */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-20 bg-blue-600 rounded-full p-1 border-2 border-[#0B0E14] text-white hover:scale-110 transition-transform shadow-lg z-30"
      >
        {open ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
      </button>
    </aside>
  )
}
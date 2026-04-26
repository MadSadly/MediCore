import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Brain, Columns2, Circle, Shield, Eye, LayoutDashboard,
  Settings, LogOut, ChevronLeft, ChevronRight, Activity,
} from 'lucide-react'
import MediLogo from './MediLogo'

const NAV_ITEMS = [
  { path: '/dashboard',      label: '통합 대시보드',  sub: '김용',  icon: LayoutDashboard, diseaseKey: null },
  { path: '/brain-tumor',    label: '뇌종양 진단',    sub: '변운조', icon: Brain,           diseaseKey: 'brain-tumor' },
  { path: '/spine-disk',     label: '허리디스크',     sub: '김담현', icon: Columns2,        diseaseKey: 'spine-disk' },
  { path: '/colon-cancer',   label: '대장암 예측',    sub: '박기완', icon: Circle,          diseaseKey: 'colon-cancer' },
  { path: '/kidney-failure', label: '신부전 관리',    sub: '김남준', icon: Shield,          diseaseKey: 'kidney-failure' },
  { path: '/skin-disease',   label: '피부질환 분류',  sub: '김민수', icon: Activity,        diseaseKey: 'skin-disease' },
  { path: '/eye-disease',    label: '안과 질환',      sub: '홍승현', icon: Eye,             diseaseKey: 'eye-disease' },
]

const RECENT = [
  { id: '#9928_UNJO', time: '14:22', desc: 'Brain Scan: Positive', color: 'text-blue-400' },
  { id: '#9927_DAM',  time: '13:05', desc: 'Spine MRI: Normal',    color: 'text-slate-400' },
]

export default function Sidebar({ open, onToggle }) {
  const location = useLocation()
  const navigate = useNavigate()

  // 환자 상세 페이지 여부 감지
  const patientMatch = location.pathname.match(/^\/patients\/([^/]+)/)
  const currentPatientId = patientMatch ? patientMatch[1] : null

  const getLinkProps = (item) => {
    if (currentPatientId && item.diseaseKey) {
      // 환자 페이지에서 질환 탭 클릭 → 해당 환자의 질환 탭으로 전환
      return {
        to: `/patients/${currentPatientId}?disease=${item.diseaseKey}`,
      }
    }
    return { to: item.path }
  }

  const isActive = (item) => {
    if (currentPatientId && item.diseaseKey) {
      const params = new URLSearchParams(location.search)
      return params.get('disease') === item.diseaseKey
    }
    return location.pathname === item.path
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

      {/* 환자 컨텍스트 배너 */}
      {open && currentPatientId && (
        <div className="mx-3 mt-3 px-3 py-2 bg-blue-600/10 border border-blue-600/20 rounded-lg">
          <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">현재 환자</p>
          <p className="text-xs text-slate-300 font-semibold truncate">{currentPatientId}</p>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        {NAV_ITEMS.map((item) => {
          const { icon: Icon } = item
          const active = isActive(item)
          const linkProps = getLinkProps(item)
          return (
            <Link
              key={item.path}
              {...linkProps}
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
                  <p className="text-[10px] text-slate-500 whitespace-nowrap">{item.sub}</p>
                </div>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Recent Analysis */}
      {open && (
        <div className="flex-shrink-0 border-t border-slate-800 p-4 bg-[#0d1117]/80">
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">최근 분석 기록</span>
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
          </div>
          <div className="space-y-2">
            {RECENT.map(r => (
              <div key={r.id} className="p-2 rounded bg-slate-800/30 border border-slate-700/50 hover:border-blue-500/50 transition-all cursor-pointer">
                <div className="flex justify-between text-[10px] mb-1">
                  <span className={`font-bold ${r.color}`}>{r.id}</span>
                  <span className="text-slate-500">{r.time}</span>
                </div>
                <p className="text-[9px] text-slate-400 truncate">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom */}
      <div className="flex-shrink-0 border-t border-slate-800 p-3 space-y-1">
        <Link to="/settings" title={!open ? '설정' : undefined} className="flex items-center p-3 rounded-xl text-slate-400 hover:bg-slate-800 transition-all">
          <Settings size={20} className="flex-shrink-0" />
          {open && <span className="ml-4 text-sm font-semibold">설정</span>}
        </Link>
        <button onClick={logout} title={!open ? '로그아웃' : undefined} className="w-full flex items-center p-3 rounded-xl text-slate-400 hover:bg-slate-800 transition-all">
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

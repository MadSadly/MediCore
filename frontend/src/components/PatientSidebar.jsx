import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import MediLogo from './MediLogo'

const DISEASE_TABS = [
  {
    key: 'overview',
    label: '통합 대시보드',
    sub: '환자 종합 정보',
    color: 'from-slate-500 to-slate-600',
    path: 'M520-600v-240h320v240H520ZM120-440v-400h320v400H120Zm400 320v-400h320v400H520Zm-400 0v-240h320v240H120Zm80-400h160v-240H200v240Zm400 320h160v-240H600v240Zm0-480h160v-80H600v80ZM200-200h160v-80H200v80Zm160-320Zm240-160Zm0 240Zm-240 160Z',
  },
  {
    key: 'brain-tumor',
    label: '뇌종양 진단',
    sub: '변운조',
    color: 'from-blue-500 to-blue-600',
    path: 'M360-120q-100 0-170-70T120-360q0-75 40.5-136T267-587q11-94 80.5-153.5T508-800q90 0 158 53t90 140q66 11 105 61t39 113q0 78-54.5 130.5T720-250v130H360v-120Zm0-80h280v-80h80q45 0 72.5-28.5T820-382q0-45-27.5-76.5T720-490h-40v-60q0-66-47-113t-113-47q-62 0-107.5 39T360-567h-40q-58 0-99 41t-41 99q0 58 41 99t99 41h40v144Zm200-160Zm-160-40h80v-120l80-80 80 80v120h80v-157l-160-160-160 160v157Z',
  },
  {
    key: 'spine-disk',
    label: '허리디스크',
    sub: '김담현',
    color: 'from-violet-500 to-violet-600',
    path: 'M440-80v-160H200v-80h240v-160H200v-80h240v-160H200v-80h240V-880h80v120h240v80H520v160h240v80H520v160h240v80H520v160h-80Zm80-360Zm0-240Zm0 240h80-80Zm0-240h80-80Z',
  },
  {
    key: 'colon-cancer',
    label: '대장암 예측',
    sub: '박기완',
    color: 'from-amber-500 to-orange-500',
    path: 'M480-80q-83 0-141.5-58.5T280-280q0-48 20.5-90.5T360-442v-38q-50-11-85-49t-35-91q0-58 41-99t99-41q11 0 21 1.5t19 4.5q10-29 34.5-47.5T508-820q33 0 57.5 18.5T600-754q9-3 18.5-4.5T640-760q58 0 99 41t41 99q0 53-35 91t-85 49v38q39 27 59.5 69.5T740-280q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35Zm-160-440q25 0 42.5-17.5T380-660q0-25-17.5-42.5T320-720q-25 0-42.5 17.5T260-660q0 25 17.5 42.5T320-600Zm320 0q25 0 42.5-17.5T700-660q0-25-17.5-42.5T640-720q-25 0-42.5 17.5T580-660q0 25 17.5 42.5T640-600ZM480-280Zm0-120Z',
  },
  {
    key: 'kidney-failure',
    label: '신부전 관리',
    sub: '김남준',
    color: 'from-cyan-500 to-cyan-600',
    path: 'M480-80q-51 0-98-19.5T296-158q-78-72-117-166.5T140-540q0-100 44-186t116-142q14-11 31-8.5t25 16.5q20 39 49.5 70T472-742q-12-27-18-56t-6-58q0-92 58-159t150-85q17-4 30.5 4.5T704-872q29 91 15 184T660-524q-17 26-38 48t-46 37q4 9 6.5 19t2.5 20q0 42-29.5 71T484-300q-8 0-15.5-1T454-304q-9 27-13.5 55T436-192q0 41 15.5 78T495-51q-7 1-7.5 1T480-80Zm20-300q8 0 14-6t6-14q0-8-6-14t-14-6q-8 0-14 6t-6 14q0 8 6 14t14 6Z',
  },
  {
    key: 'skin-disease',
    label: '피부질환 분류',
    sub: '김민수',
    color: 'from-rose-500 to-pink-500',
    path: 'M480-80q-83 0-141.5-58.5T280-280v-360l-80-80v-120h80v-40h80v40h240v-40h80v40h80v120l-80 80v360q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85v-360l80-80v-40H320v40l80 80v360q0 50 35 85t45 35Zm-80-320h-80v80h80v-80Zm160 0h-80v80h80v-80Zm-80 0Zm0 200q33 0 56.5-23.5T560-360h-160q0 33 23.5 56.5T480-280Z',
  },
  {
    key: 'eye-disease',
    label: '안과 질환',
    sub: '홍승현',
    color: 'from-teal-500 to-emerald-500',
    path: 'M607.5-372.5Q660-425 660-500t-52.5-127.5Q555-680 480-680t-127.5 52.5Q300-575 300-500t52.5 127.5Q405-320 480-320t127.5-52.5Zm-204-51Q372-455 372-500t31.5-76.5Q435-608 480-608t76.5 31.5Q588-545 588-500t-31.5 76.5Q525-392 480-392t-76.5-31.5ZM214-281.5Q94-363 40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200q-146 0-266-81.5ZM480-500Zm207.5 160.5Q782-399 832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280q113 0 207.5-59.5Z',
  },
]

function TabIcon({ tab, active }) {
  return (
    <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-gradient-to-br ${tab.color} shadow-lg`}>
      <svg viewBox="0 -960 960 960" width={18} height={18} fill="white">
        <path d={tab.path} />
      </svg>
    </div>
  )
}

export default function PatientSidebar({ patientId, patientName, open, onToggle }) {
  const location = useLocation()
  const navigate = useNavigate()

  const getPath = (key) =>
    key === 'overview' ? `/patients/${patientId}` : `/patients/${patientId}/${key}`

  const isActive = (key) => {
    const path = getPath(key)
    if (key === 'overview') return location.pathname === path
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
      <Link
        to="/dashboard"
        className="h-16 flex-shrink-0 flex items-center px-5 border-b border-slate-800 overflow-hidden hover:opacity-80 transition-opacity"
      >
        <div className="flex-shrink-0">
          <MediLogo size={open ? 36 : 32} />
        </div>
        {open && (
          <div className="ml-3">
            <span className="font-bold text-lg tracking-wider text-white">MEDICORE</span>
            <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold">정밀 진단 시스템</p>
          </div>
        )}
      </Link>

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
        {DISEASE_TABS.map((tab) => {
          const active = isActive(tab.key)
          return (
            <Link
              key={tab.key}
              to={getPath(tab.key)}
              title={!open ? tab.label : undefined}
              className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                active
                  ? 'bg-slate-800/80 border border-slate-700/60'
                  : 'hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <TabIcon tab={tab} active={active} />
              {open && (
                <div className="min-w-0">
                  <p className={`text-sm font-semibold whitespace-nowrap ${active ? 'text-slate-100' : 'text-slate-300'}`}>
                    {tab.label}
                  </p>
                  <p className="text-[10px] text-slate-500 whitespace-nowrap">{tab.sub}</p>
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
          className="flex items-center gap-3 p-2.5 rounded-xl text-slate-400 hover:bg-slate-800/50 transition-all border border-transparent"
        >
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-slate-700/60 border border-slate-600/40">
            <svg viewBox="0 -960 960 960" width={18} height={18} fill="currentColor" className="text-slate-400">
              <path d="M240-200h120v-240h240v240h120v-360L480-740 240-560v360Zm-80 80v-480l320-240 320 240v480H520v-240h-80v240H160Zm320-350Z" />
            </svg>
          </div>
          {open && <span className="text-sm font-semibold">← 환자 목록</span>}
        </Link>
        <button
          onClick={logout}
          title={!open ? '로그아웃' : undefined}
          className="w-full flex items-center gap-3 p-2.5 rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all border border-transparent"
        >
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-slate-700/60 border border-slate-600/40">
            <LogOut size={16} />
          </div>
          {open && <span className="text-sm font-semibold">로그아웃</span>}
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
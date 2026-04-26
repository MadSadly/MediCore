import { useNavigate } from 'react-router-dom'
import { Brain, Columns2, Circle, Shield, Activity, Eye, LayoutDashboard, TrendingUp, Users, CheckCircle } from 'lucide-react'

const MODULES = [
  { path: '/brain-tumor', label: '뇌종양 진단', sub: '변운조', icon: Brain, count: 12, color: 'from-blue-600/20 to-blue-800/10', border: 'border-blue-600/30', iconColor: 'text-blue-400', badge: '활성', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { path: '/spine-disk', label: '허리디스크', sub: '김담현', icon: Columns2, count: 8, color: 'from-violet-600/20 to-violet-800/10', border: 'border-violet-600/30', iconColor: 'text-violet-400', badge: '활성', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { path: '/colon-cancer', label: '대장암 예측', sub: '박기완', icon: Circle, count: 5, color: 'from-amber-600/20 to-amber-800/10', border: 'border-amber-600/30', iconColor: 'text-amber-400', badge: '준비중', badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  { path: '/kidney-failure', label: '신부전 관리', sub: '김남준', icon: Shield, count: 15, color: 'from-cyan-600/20 to-cyan-800/10', border: 'border-cyan-600/30', iconColor: 'text-cyan-400', badge: '활성', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { path: '/skin-disease', label: '피부질환 분류', sub: '김민수', icon: Activity, count: 20, color: 'from-rose-600/20 to-rose-800/10', border: 'border-rose-600/30', iconColor: 'text-rose-400', badge: '활성', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { path: '/eye-disease', label: '안과 질환', sub: '홍승현', icon: Eye, count: 7, color: 'from-teal-600/20 to-teal-800/10', border: 'border-teal-600/30', iconColor: 'text-teal-400', badge: '준비중', badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
]

const STATS = [
  { label: '총 분석 건수', value: '1,284', icon: LayoutDashboard, color: 'text-blue-400', bg: 'bg-blue-600/10' },
  { label: '오늘 진단', value: '47', icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-600/10' },
  { label: '등록 환자', value: '392', icon: Users, color: 'text-violet-400', bg: 'bg-violet-600/10' },
  { label: '평균 정확도', value: '96.7%', icon: CheckCircle, color: 'text-amber-400', bg: 'bg-amber-600/10' },
]

export default function MainPage() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-50">
            안녕하세요, {user.name || '의사'}님 👋
          </h1>
          <p className="text-slate-500 text-sm mt-1">MediCore AI 통합 진단 플랫폼에 오신 것을 환영합니다.</p>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>{new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
          <p className="text-blue-400 font-bold">시스템 정상 운영 중</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="glass-card rounded-xl p-5 flex items-center gap-4">
            <div className={`w-12 h-12 ${bg} rounded-full flex items-center justify-center flex-shrink-0`}>
              <Icon size={22} className={color} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">{label}</p>
              <p className="text-xl font-black text-slate-50">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Module cards */}
      <div>
        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">진단 모듈</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {MODULES.map(({ path, label, sub, icon: Icon, count, color, border, iconColor, badge, badgeColor }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`glass-card rounded-xl p-6 text-left hover:scale-[1.02] transition-all cursor-pointer border ${border} bg-gradient-to-br ${color}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 bg-slate-900/60 rounded-xl flex items-center justify-center ${iconColor}`}>
                  <Icon size={24} />
                </div>
                <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${badgeColor}`}>
                  {badge}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-1">{label}</h3>
              <p className="text-xs text-slate-500 mb-4">담당: {sub}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">오늘 분석</span>
                <span className={`text-lg font-black ${iconColor}`}>{count}건</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent patients */}
      <div>
        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">최근 진단 환자</h2>
        <div className="glass-card rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4 text-left font-bold">환자 ID</th>
                <th className="px-6 py-4 text-left font-bold">이름</th>
                <th className="px-6 py-4 text-left font-bold">진단 항목</th>
                <th className="px-6 py-4 text-left font-bold">상태</th>
                <th className="px-6 py-4 text-left font-bold">날짜</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {[
                { id: 'MED-9928', name: '아서 모건', type: '뇌종양 진단', status: '분석 완료', date: '2025.04.26' },
                { id: 'MED-9927', name: '김담현', type: '허리디스크', status: '검토 중', date: '2025.04.26' },
                { id: 'MED-9921', name: '박민서', type: '피부질환', status: '분석 완료', date: '2025.04.25' },
              ].map(p => (
                <tr key={p.id} className="hover:bg-white/5 transition-colors cursor-pointer" onClick={() => navigate(`/patients/${p.id}`)}>
                  <td className="px-6 py-4 text-blue-400 font-bold">{p.id}</td>
                  <td className="px-6 py-4 text-slate-200">{p.name}</td>
                  <td className="px-6 py-4 text-slate-400">{p.type}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                      p.status === '분석 완료'
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                        : 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                    }`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500">{p.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
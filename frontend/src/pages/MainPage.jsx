import { useNavigate } from 'react-router-dom'
import { Users, Clock, CheckCircle, FileText, Filter, Download, ChevronLeft, ChevronRight } from 'lucide-react'

const STATS = [
  { label: '전체 환자', value: '1,248', icon: Users, iconColor: 'text-blue-500', bg: 'bg-blue-600/10' },
  { label: '진료 대기', value: '12', icon: Clock, iconColor: 'text-amber-500', bg: 'bg-amber-600/10' },
  { label: '진료 완료', value: '48', icon: CheckCircle, iconColor: 'text-emerald-500', bg: 'bg-emerald-600/10' },
  { label: 'AI 분석 리포트', value: '8건', icon: FileText, iconColor: 'text-blue-400', bg: 'bg-primary/10', glow: true },
]

const PATIENTS = [
  { id: '#2024-00125', name: '김철수', initial: '김', age: '45세', gender: '남성', target: 'Brain (뇌)', targetColor: 'blue', status: '대기 중', statusColor: 'blue' },
  { id: '#2024-00124', name: '이영희', initial: '이', age: '62세', gender: '여성', target: 'Spine (척추)', targetColor: 'purple', status: '진료 완료', statusColor: 'emerald' },
  { id: '#2024-00123', name: '박지성', initial: '박', age: '28세', gender: '남성', target: 'Brain (뇌)', targetColor: 'blue', status: '대기 중', statusColor: 'blue' },
  { id: '#2024-00122', name: '최수지', initial: '최', age: '35세', gender: '여성', target: 'Chest (흉부)', targetColor: 'emerald', status: '진료 완료', statusColor: 'emerald' },
  { id: '#2024-00121', name: '정민호', initial: '정', age: '51세', gender: '남성', target: 'Spine (척추)', targetColor: 'amber', status: '대기 중', statusColor: 'blue' },
]

const COLOR = {
  blue:    { dot: 'bg-blue-500',    bg: 'bg-blue-900/20',    border: 'border-blue-800/30',    avatar: 'bg-blue-600/10 text-blue-400 border-blue-600/20',    badge: 'bg-blue-600/10 text-blue-500 border-blue-600/20' },
  purple:  { dot: 'bg-purple-500',  bg: 'bg-purple-900/20',  border: 'border-purple-800/30',  avatar: 'bg-purple-600/10 text-purple-400 border-purple-600/20', badge: 'bg-purple-600/10 text-purple-500 border-purple-600/20' },
  emerald: { dot: 'bg-emerald-500', bg: 'bg-emerald-900/20', border: 'border-emerald-800/30', avatar: 'bg-emerald-600/10 text-emerald-400 border-emerald-600/20', badge: 'bg-emerald-600/10 text-emerald-500 border-emerald-600/20' },
  amber:   { dot: 'bg-amber-500',   bg: 'bg-amber-900/20',   border: 'border-amber-800/30',   avatar: 'bg-amber-600/10 text-amber-400 border-amber-600/20',   badge: 'bg-amber-600/10 text-amber-500 border-amber-600/20' },
}

const SCHEDULE = [
  { time: '오후 2:30', title: '전문의 세미나', loc: '본관 3층 컨퍼런스룸 B', color: 'bg-blue-500', done: false },
  { time: '오전 10:00', title: '정기 회진', loc: '병동 A구역 201호~208호', color: 'bg-emerald-500', done: false },
  { time: '오전 08:30', title: '케이스 리뷰', loc: '완료됨', color: 'bg-slate-600', done: true },
]

export default function MainPage() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  return (
    <div className="max-w-[1600px] mx-auto space-y-8">
      {/* Page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h2 className="text-3xl md:text-4xl font-black text-slate-50 tracking-tight">환자 관리 대시보드</h2>
          <p className="text-slate-500 text-sm mt-1">
            안녕하세요 <span className="text-blue-400 font-semibold">{user.name || '의사'}님</span> — 오늘의 진료 현황 및 환자 목록입니다.
          </p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all active:scale-95 glow-blue text-sm">
          <Users size={18} />
          환자 등록
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {STATS.map(({ label, value, icon: Icon, iconColor, bg, glow }) => (
          <div key={label} className={`bg-[#0F172A] border border-[#1E293B] p-5 rounded-2xl flex items-center gap-5 hover:-translate-y-0.5 transition-transform ${glow ? 'ai-glow' : ''}`}>
            <div className={`w-14 h-14 rounded-2xl ${bg} flex items-center justify-center flex-shrink-0`}>
              <Icon size={28} className={iconColor} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{label}</p>
              <p className="text-2xl font-black text-slate-50">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Patient table */}
      <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-8 py-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <div className="flex items-center gap-4">
            <h3 className="text-xl font-bold text-slate-100">실시간 환자 목록</h3>
            <span className="px-2 py-0.5 bg-red-600/10 text-red-500 text-[10px] font-black rounded-md border border-red-600/20">LIVE</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-700 transition-colors">
              <Filter size={16} /> 필터링
            </button>
            <button className="p-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors">
              <Download size={16} />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-900/30 text-slate-500 text-[11px] uppercase tracking-widest font-black">
                {['환자번호', '환자이름', '나이', '성별', '진단 타겟', '진료 상태', '관리'].map((h, i) => (
                  <th key={h} className={`px-8 py-5 ${i === 6 ? 'text-right' : ''}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {PATIENTS.map((p) => {
                const c = COLOR[p.targetColor]
                const sc = COLOR[p.statusColor]
                return (
                  <tr
                    key={p.id}
                    className="hover:bg-blue-600/5 transition-colors group cursor-pointer"
                    onDoubleClick={() => navigate(`/patients/${p.id.replace('#', '')}`)}
                  >
                    <td className="px-8 py-5 text-slate-400 font-mono text-sm">{p.id}</td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border ${c.avatar}`}>
                          {p.initial}
                        </div>
                        <span className="font-bold text-slate-100 text-base">{p.name}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-slate-300">{p.age}</td>
                    <td className="px-8 py-5 text-slate-300">{p.gender}</td>
                    <td className="px-8 py-5">
                      <span className={`flex items-center gap-2 text-slate-300 ${c.bg} px-3 py-1 rounded-full w-fit border ${c.border} text-sm`}>
                        <span className={`w-2 h-2 rounded-full ${c.dot}`} />
                        {p.target}
                      </span>
                    </td>
                    <td className="px-8 py-5">
                      <span className={`inline-flex items-center px-4 py-1 rounded-full text-xs font-black border uppercase tracking-tighter ${sc.badge}`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button
                        onClick={() => navigate(`/patients/${p.id.replace('#', '')}`)}
                        className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold opacity-0 group-hover:opacity-100 hover:bg-blue-600 hover:text-white transition-all"
                      >
                        상세보기
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-8 py-5 border-t border-slate-800 flex justify-between items-center bg-slate-900/20">
          <p className="text-sm text-slate-500 font-medium">100명 중 1-5명 표시 중</p>
          <div className="flex items-center gap-2">
            <button className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition-all"><ChevronLeft size={18} /></button>
            {[1, 2, 3].map(n => (
              <button key={n} className={`w-9 h-9 rounded-lg text-sm font-bold transition-all ${n === 1 ? 'bg-blue-600 text-white glow-blue' : 'hover:bg-slate-800 text-slate-400'}`}>{n}</button>
            ))}
            <span className="text-slate-600 px-2 font-black">···</span>
            <button className="w-9 h-9 rounded-lg hover:bg-slate-800 text-slate-400 text-sm font-medium transition-all">20</button>
            <button className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition-all"><ChevronRight size={18} /></button>
          </div>
        </div>
      </div>

      {/* Bottom: AI insight + Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* AI insight */}
        <div className="lg:col-span-2 bg-[#0F172A] border border-blue-500/20 p-8 rounded-2xl ai-glow">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-600/10 flex items-center justify-center text-blue-500">
              ✨
            </div>
            <h4 className="text-2xl font-bold text-slate-100">AI 정밀 분석 제안</h4>
          </div>
          <div className="flex flex-col md:flex-row gap-8">
            <div className="w-24 h-24 shrink-0 rounded-2xl bg-slate-800 flex items-center justify-center border border-blue-500/20 text-5xl">
              🧠
            </div>
            <div className="flex-1 space-y-4">
              <div>
                <p className="text-slate-100 text-xl font-bold">신규 뇌 MRI 데이터 분석 필요</p>
                <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                  오늘 등록된 환자 #2024-00125 (김철수) 님의 MRI 영상에서 해마 부근의 미세한 수축 징후가 감지되었습니다.
                  초기 치매 위험도가 평소보다 15% 높게 측정되었으므로 정밀 진단을 권장합니다.
                </p>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/patients/2024-00125')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all active:scale-95 glow-blue"
                >
                  상세 분석 리포트 확인
                </button>
                <button className="text-slate-400 hover:text-white text-sm font-bold transition-colors">
                  분석 기준 보기 ›
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Schedule */}
        <div className="bg-[#0F172A] border border-[#1E293B] p-8 rounded-2xl">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xl font-bold text-slate-100">오늘의 진료 일정</h4>
            <span className="text-blue-500 text-xs font-black uppercase">
              {new Date().toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' })}
            </span>
          </div>
          <ul className="space-y-6 relative before:absolute before:left-[3px] before:top-2 before:bottom-2 before:w-px before:bg-slate-800">
            {SCHEDULE.map((s) => (
              <li key={s.title} className={`flex items-start gap-4 relative ${s.done ? 'opacity-50' : ''}`}>
                <div className={`w-2 h-2 rounded-full ${s.color} mt-1.5 z-10 outline outline-4 outline-[#0F172A] flex-shrink-0`} />
                <div className="space-y-0.5">
                  <p className="text-sm font-bold text-slate-100">{s.time} — {s.title}</p>
                  <p className="text-xs text-slate-500">{s.loc}</p>
                </div>
              </li>
            ))}
          </ul>
          <button className="w-full mt-8 py-3 bg-slate-900 border border-slate-800 text-slate-400 rounded-xl text-xs font-bold hover:text-white transition-colors">
            전체 일정 보기
          </button>
        </div>
      </div>
    </div>
  )
}

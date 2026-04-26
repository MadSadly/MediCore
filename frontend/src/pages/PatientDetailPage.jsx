import { useParams } from 'react-router-dom'
import { AlertCircle, AlertTriangle, CheckCircle, TrendingUp, FileText, Pill, Users, Activity } from 'lucide-react'

const TIMELINE = [
  {
    date: '2023년 10월 24일',
    title: '조영 증강 MRI (두개골)',
    desc: '측두엽 내 비정상적 성장 관찰. 생검 권장.',
    tag: '영상의학과',
    active: true,
  },
  {
    date: '2022년 8월 12일',
    title: '정기 건강 검진',
    desc: '기초 활력 징후 기록. 특이 사항 없음.',
    tag: '일반',
    active: false,
  },
  {
    date: '2021년 1월 5일',
    title: '응급실 입원: 외상',
    desc: '낙상 후 척추 스크리닝. 결과: 골절 없음.',
    tag: '응급',
    active: false,
  },
]

const AI_INSIGHTS = [
  { icon: AlertCircle, color: 'text-red-400', title: '부피 증가', desc: '병변 부피가 이전 스캔 대비 2.4cm³ 증가했습니다.' },
  { icon: AlertTriangle, color: 'text-amber-400', title: '정중선 이동', desc: '좌측 반구에서 미세한 1.2mm 이동이 감지되었습니다.' },
  { icon: CheckCircle, color: 'text-emerald-400', title: '혈관 침범 없음', desc: '주요 동맥은 보조 영역으로부터 안전합니다.' },
]

const SUMMARY_CARDS = [
  { icon: Activity, label: '안정성 점수', value: '하락세', bg: 'bg-blue-600/10', iconColor: 'text-blue-500', border: 'border-l-4 border-l-blue-600' },
  { icon: Pill, label: '복용 약물', value: '덱사메타손', bg: 'bg-slate-800', iconColor: 'text-slate-400', border: '' },
  { icon: Users, label: '담당 의료팀', value: '종양학 유닛 A', bg: 'bg-slate-800', iconColor: 'text-slate-400', border: '' },
]

export default function PatientDetailPage() {
  const { id } = useParams()

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Bento grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Patient Profile */}
        <section className="col-span-12 lg:col-span-4 glass-card p-6 rounded-xl flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-6">
              <h3 className="text-xl font-semibold text-slate-200">환자 프로필</h3>
              <span className="text-slate-500">🪪</span>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700 text-2xl font-black text-slate-400">
                  아
                </div>
                <div>
                  <h4 className="text-lg font-bold text-slate-50">아서 모건</h4>
                  <p className="text-sm text-slate-400">UID: {id || 'MED-9921-X'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                {[
                  ['나이', '42세'],
                  ['성별', '남성'],
                  ['혈액형', 'O형 (Rh+)'],
                  ['최근 검사', '2023.10.24'],
                ].map(([label, value]) => (
                  <div key={label}>
                    <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">{label}</p>
                    <p className="text-slate-200 font-medium">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <button className="mt-8 w-full py-2 border border-slate-700 text-slate-300 text-sm font-medium rounded-lg hover:bg-white/5 transition-colors">
            프로필 수정
          </button>
        </section>

        {/* Medical History Timeline */}
        <section className="col-span-12 lg:col-span-8 glass-card p-6 rounded-xl">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold text-slate-200">진료 이력 타임라인</h3>
            <div className="flex gap-2">
              <button className="text-xs px-3 py-1 bg-slate-800 text-slate-400 rounded-full border border-slate-700">전체</button>
              <button className="text-xs px-3 py-1 text-slate-500 rounded-full hover:bg-slate-800 transition-colors">영상 의학</button>
            </div>
          </div>
          <div className="relative space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-slate-800">
            {TIMELINE.map((item, i) => (
              <div key={i} className="relative pl-10">
                <div className={`absolute left-1.5 top-1.5 w-3 h-3 rounded-full ring-4 ${item.active ? 'bg-blue-600 ring-blue-600/10' : 'bg-slate-700 ring-transparent'}`} />
                <div className={`flex flex-col md:flex-row md:items-center justify-between gap-2 p-4 border rounded-lg ${item.active ? 'bg-white/5 border-slate-800' : 'border-slate-800/50 opacity-70'}`}>
                  <div>
                    <span className={`text-[10px] font-bold uppercase tracking-tighter ${item.active ? 'text-blue-400' : 'text-slate-500'}`}>{item.date}</span>
                    <h5 className="text-slate-200 font-bold">{item.title}</h5>
                    <p className="text-sm text-slate-400">{item.desc}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded ${item.active ? 'bg-blue-600/10 text-blue-400' : 'bg-slate-800 text-slate-500'}`}>
                      {item.tag}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* AI Analysis Report */}
        <section className="col-span-12 glass-card rounded-xl overflow-hidden ai-glow">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-blue-600/5">
            <div className="flex items-center gap-3">
              <span className="text-blue-500 text-xl">✨</span>
              <h3 className="text-xl font-semibold text-slate-200">AI 분석 비교 리포트</h3>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-xs">
                <span className="w-2 h-2 bg-blue-600 rounded-full" />
                <span className="text-slate-400">현재 (2023년 11월)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-2 h-2 bg-slate-500 rounded-full" />
                <span className="text-slate-400">이전 (2023년 10월)</span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 p-6 gap-8">
            {/* Scan 1 */}
            <div className="space-y-4">
              <div className="relative aspect-square rounded-lg bg-slate-900 border border-slate-800 overflow-hidden flex items-center justify-center">
                <div className="text-slate-700 text-center">
                  <p className="text-4xl mb-2">🧠</p>
                  <p className="text-xs">MRI 이미지 (가로 단면)</p>
                </div>
                <div className="absolute top-4 left-4 px-2 py-1 bg-black/60 rounded text-[10px] text-slate-300 font-bold border border-white/10 uppercase">
                  가로 단면 (Axial)
                </div>
                <div className="absolute inset-0 border border-blue-500/20 pointer-events-none">
                  <div className="absolute top-1/2 left-0 w-full h-px bg-blue-500/20" />
                  <div className="absolute left-1/2 top-0 w-px h-full bg-blue-500/20" />
                </div>
              </div>
              <div className="p-3 bg-white/5 rounded-lg border border-slate-800">
                <p className="text-xs text-blue-400 font-bold uppercase mb-1">성장 지수</p>
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-black text-slate-50">+12%</span>
                  <span className="text-xs text-red-400 mb-1 flex items-center gap-1">
                    <TrendingUp size={14} /> 유의미함
                  </span>
                </div>
              </div>
            </div>

            {/* Scan 2 */}
            <div className="space-y-4">
              <div className="relative aspect-square rounded-lg bg-slate-900 border border-slate-800 overflow-hidden flex items-center justify-center">
                <div className="text-slate-700 text-center">
                  <p className="text-4xl mb-2">🧠</p>
                  <p className="text-xs">MRI 이미지 (세로 단면)</p>
                </div>
                <div className="absolute top-4 left-4 px-2 py-1 bg-black/60 rounded text-[10px] text-slate-300 font-bold border border-white/10 uppercase">
                  세로 단면 (Sagittal)
                </div>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-16 h-16 border-2 border-dashed border-blue-500/50 rounded-full animate-pulse" />
                </div>
              </div>
              <div className="p-3 bg-white/5 rounded-lg border border-slate-800">
                <p className="text-xs text-blue-400 font-bold uppercase mb-1">분석 신뢰도</p>
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-black text-slate-50">98.4%</span>
                  <span className="text-xs text-emerald-400 mb-1 flex items-center gap-1">
                    <CheckCircle size={14} /> 고정밀도
                  </span>
                </div>
              </div>
            </div>

            {/* AI Insights */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2">AI 주요 분석 결과</h4>
              <ul className="space-y-3">
                {AI_INSIGHTS.map(({ icon: Icon, color, title, desc }) => (
                  <li key={title} className="flex items-start gap-3">
                    <Icon size={20} className={`${color} mt-0.5 flex-shrink-0`} />
                    <div>
                      <p className="text-sm text-slate-200 font-medium">{title}</p>
                      <p className="text-xs text-slate-500">{desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="pt-4">
                <button className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors glow-blue">
                  <FileText size={18} />
                  전체 PDF 리포트 생성
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Case Summary */}
        <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {SUMMARY_CARDS.map(({ icon: Icon, label, value, bg, iconColor, border }) => (
            <div key={label} className={`glass-card p-6 rounded-xl flex items-center gap-4 ${border}`}>
              <div className={`w-12 h-12 ${bg} rounded-full flex items-center justify-center flex-shrink-0`}>
                <Icon size={22} className={iconColor} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">{label}</p>
                <p className="text-xl font-bold text-slate-50">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

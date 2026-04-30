import { useEffect, useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { FileText, Search, ChevronDown } from 'lucide-react'

const DISEASE_META = {
  'brain-tumor':    { label: '뇌종양 진단',   color: 'text-blue-400',   bg: 'bg-blue-600/10',   border: 'border-blue-600/30'   },
  'spine-disk':     { label: '허리디스크',    color: 'text-violet-400', bg: 'bg-violet-600/10', border: 'border-violet-600/30' },
  'colon-cancer':   { label: '대장암 예측',   color: 'text-amber-400',  bg: 'bg-amber-600/10',  border: 'border-amber-600/30'  },
  'kidney-failure': { label: '신부전 관리',   color: 'text-cyan-400',   bg: 'bg-cyan-600/10',   border: 'border-cyan-600/30'   },
  'skin-disease':   { label: '피부질환 분류', color: 'text-rose-400',   bg: 'bg-rose-600/10',   border: 'border-rose-600/30'   },
  'eye-disease':    { label: '안과 질환',     color: 'text-teal-400',   bg: 'bg-teal-600/10',   border: 'border-teal-600/30'   },
}

const DiseaseIcon = ({ type, size = 20, className = '' }) => {
  const paths = {
    'brain-tumor':    'M360-120q-100 0-170-70T120-360q0-75 40.5-136T267-587q11-94 80.5-153.5T508-800q90 0 158 53t90 140q66 11 105 61t39 113q0 78-54.5 130.5T720-250v130H360v-120Zm0-80h280v-80h80q45 0 72.5-28.5T820-382q0-45-27.5-76.5T720-490h-40v-60q0-66-47-113t-113-47q-62 0-107.5 39T360-567h-40q-58 0-99 41t-41 99q0 58 41 99t99 41h40v144Zm200-160Zm-160-40h80v-120l80-80 80 80v120h80v-157l-160-160-160 160v157Z',
    'spine-disk':     'M440-80v-160H200v-80h240v-160H200v-80h240v-160H200v-80h240V-880h80v120h240v80H520v160h240v80H520v160h240v80H520v160h-80Zm80-360Zm0-240Zm0 240h80-80Zm0-240h80-80Z',
    'colon-cancer':   'M480-80q-83 0-141.5-58.5T280-280q0-48 20.5-90.5T360-442v-38q-50-11-85-49t-35-91q0-58 41-99t99-41q11 0 21 1.5t19 4.5q10-29 34.5-47.5T508-820q33 0 57.5 18.5T600-754q9-3 18.5-4.5T640-760q58 0 99 41t41 99q0 53-35 91t-85 49v38q39 27 59.5 69.5T740-280q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35Zm-160-440q25 0 42.5-17.5T380-660q0-25-17.5-42.5T320-720q-25 0-42.5 17.5T260-660q0 25 17.5 42.5T320-600Zm320 0q25 0 42.5-17.5T700-660q0-25-17.5-42.5T640-720q-25 0-42.5 17.5T580-660q0 25 17.5 42.5T640-600ZM480-280Zm0-120Z',
    'kidney-failure': 'M480-80q-51 0-98-19.5T296-158q-78-72-117-166.5T140-540q0-100 44-186t116-142q14-11 31-8.5t25 16.5q20 39 49.5 70T472-742q-12-27-18-56t-6-58q0-92 58-159t150-85q17-4 30.5 4.5T704-872q29 91 15 184T660-524q-17 26-38 48t-46 37q4 9 6.5 19t2.5 20q0 42-29.5 71T484-300q-8 0-15.5-1T454-304q-9 27-13.5 55T436-192q0 41 15.5 78T495-51q-7 1-7.5 1T480-80Zm20-300q8 0 14-6t6-14q0-8-6-14t-14-6q-8 0-14 6t-6 14q0 8 6 14t14 6Z',
    'skin-disease':   'M480-80q-83 0-141.5-58.5T280-280v-360l-80-80v-120h80v-40h80v40h240v-40h80v40h80v120l-80 80v360q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85v-360l80-80v-40H320v40l80 80v360q0 50 35 85t45 35Zm-80-320h-80v80h80v-80Zm160 0h-80v80h80v-80Zm-80 0Zm0 200q33 0 56.5-23.5T560-360h-160q0 33 23.5 56.5T480-280Z',
    'eye-disease':    'M607.5-372.5Q660-425 660-500t-52.5-127.5Q555-680 480-680t-127.5 52.5Q300-575 300-500t52.5 127.5Q405-320 480-320t127.5-52.5Zm-204-51Q372-455 372-500t31.5-76.5Q435-608 480-608t76.5 31.5Q588-545 588-500t-31.5 76.5Q525-392 480-392t-76.5-31.5ZM214-281.5Q94-363 40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200q-146 0-266-81.5ZM480-500Zm207.5 160.5Q782-399 832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280q113 0 207.5-59.5Z',
  }
  return (
    <svg viewBox="0 -960 960 960" width={size} height={size} className={className} fill="currentColor">
      <path d={paths[type] || paths['eye-disease']} />
    </svg>
  )
}

function StatBadge({ label, value, color }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-black ${color}`}>{value}</p>
      <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mt-0.5">{label}</p>
    </div>
  )
}

function DiagnosisCard({ diagnosis }) {
  const meta = DISEASE_META[diagnosis.diseaseType] || {}
  const date = diagnosis.createdAt
    ? new Date(diagnosis.createdAt).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })
    : '-'
  return (
    <div className={`rounded-xl border ${meta.border || 'border-slate-700/60'} bg-slate-900/60 hover:bg-slate-800/60 transition-colors`}>
      <div className="p-5 flex items-start gap-4">
        <div className={`w-11 h-11 rounded-xl ${meta.bg || 'bg-slate-800'} flex items-center justify-center flex-shrink-0 border ${meta.border || 'border-slate-700'}`}>
          <DiseaseIcon type={diagnosis.diseaseType} size={21} className={meta.color || 'text-slate-400'} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className={`text-[11px] font-bold uppercase tracking-widest ${meta.color || 'text-slate-400'}`}>
              {meta.label || diagnosis.diseaseType}
            </span>
            <span className="text-[11px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-md">
              {date}
            </span>
          </div>
          <h4 className="text-slate-100 font-semibold text-sm leading-snug">{diagnosis.title}</h4>
          {diagnosis.summary && (
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-2">{diagnosis.summary}</p>
          )}
          {diagnosis.createdBy && (
            <p className="text-[10px] text-slate-600 mt-2 flex items-center gap-1">
              <span>진단의:</span>
              <span className="text-slate-500">{diagnosis.createdBy}</span>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

const STATUS_STYLE = {
  WAITING: { label: '진료 대기', cls: 'bg-amber-500/10 text-amber-400 border-amber-500/30'   },
  DONE:    { label: '진료 완료', cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
}

export default function PatientDetailPage() {
  const { id } = useParams()
  const [patient, setPatient] = useState(null)
  const [diagnoses, setDiagnoses] = useState([])
  const [status, setStatus] = useState('WAITING')
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')

  useEffect(() => {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      axios.get(`/api/patients/${id}`, { headers }),
      axios.get(`/api/patients/${id}/diagnoses`, { headers }),
      axios.get(`/api/patients/${id}/status`, { headers }),
    ])
      .then(([pRes, dRes, sRes]) => {
        setPatient(pRes.data)
        setDiagnoses(dRes.data)
        setStatus(sRes.data.status || 'WAITING')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const countByDisease = useMemo(() => {
    const c = {}
    diagnoses.forEach(d => { c[d.diseaseType] = (c[d.diseaseType] || 0) + 1 })
    return c
  }, [diagnoses])

  const filtered = useMemo(() => {
    return diagnoses.filter(d => {
      const matchFilter = activeFilter === 'all' || d.diseaseType === activeFilter
      const q = search.trim().toLowerCase()
      const matchSearch = !q ||
        d.title?.toLowerCase().includes(q) ||
        d.summary?.toLowerCase().includes(q) ||
        (DISEASE_META[d.diseaseType]?.label || '').includes(q)
      return matchFilter && matchSearch
    })
  }, [diagnoses, activeFilter, search])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-sm">환자 정보를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <p className="text-4xl mb-4">❌</p>
          <p className="text-slate-300 font-bold">환자를 찾을 수 없습니다</p>
          <p className="text-slate-500 text-sm mt-2">{id}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">

      {/* 환자 프로필 카드 */}
      <section className="rounded-2xl border border-slate-700/60 bg-slate-900/80 overflow-hidden">
        {/* 상단 헤더 바 */}
        <div className="px-6 py-4 border-b border-slate-700/60 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-slate-700 flex items-center justify-center border border-slate-600 text-base font-black text-slate-200">
              {patient.name?.[0] || '?'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">{patient.name}</h2>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_STYLE[status]?.cls}`}>
                  {STATUS_STYLE[status]?.label}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">ID: {patient.uid}</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <StatBadge label="누적 리포트" value={`${diagnoses.length}건`} color="text-blue-400" />
            {diagnoses.length > 0 && (
              <StatBadge
                label="최근 진단"
                value={new Date(diagnoses[0]?.createdAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                color="text-slate-300"
              />
            )}
          </div>
        </div>

        {/* 기본 정보 그리드 */}
        <div className="px-6 py-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-x-8 gap-y-4">
            {[
              { label: '나이',     value: patient.age ? `${patient.age}세` : null },
              { label: '성별',     value: patient.gender },
              { label: '혈액형',   value: patient.bloodType },
              { label: '최근검사', value: patient.lastExamDate },
              { label: '담당의',   value: patient.assignedDoctor },
            ].map(({ label, value }) => value ? (
              <div key={label}>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">{label}</p>
                <p className="text-sm text-slate-200 font-medium">{value}</p>
              </div>
            ) : null)}
          </div>

          {/* 질환별 리포트 현황 */}
          {diagnoses.length > 0 && (
            <div className="mt-5 pt-4 border-t border-slate-700/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">질환별 진단 현황</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(DISEASE_META).map(([key, meta]) => {
                  const cnt = countByDisease[key] || 0
                  if (cnt === 0) return null
                  return (
                    <div key={key} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${meta.border} ${meta.bg}`}>
                      <DiseaseIcon type={key} size={13} className={meta.color} />
                      <span className={`text-xs font-semibold ${meta.color}`}>{meta.label}</span>
                      <span className="text-xs text-slate-400 font-bold">{cnt}건</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* 진단 리포트 섹션 */}
      <section>
        {/* 섹션 헤더 + 검색 + 필터 */}
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="flex items-center gap-3 flex-1">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest whitespace-nowrap flex items-center gap-2">
              <FileText size={14} className="text-slate-500" />
              진단 분석 리포트
            </h3>
            <span className="text-xs text-slate-600 bg-slate-800 px-2 py-0.5 rounded-md">{filtered.length}건</span>
          </div>

          <div className="flex gap-2 sm:w-auto">
            {/* 검색 */}
            <div className="relative flex-1 sm:w-52">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="제목 · 질환명 검색"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-lg pl-8 pr-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500/20"
              />
            </div>

            {/* 질환 필터 select */}
            <div className="relative">
              <select
                value={activeFilter}
                onChange={e => setActiveFilter(e.target.value)}
                className="appearance-none bg-slate-800/80 border border-slate-700 rounded-lg pl-3 pr-8 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-500 cursor-pointer"
              >
                <option value="all">전체 질환</option>
                {Object.entries(DISEASE_META).map(([key, meta]) => (
                  <option key={key} value={key}>{meta.label}</option>
                ))}
              </select>
              <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* 리포트 목록 */}
        {filtered.length === 0 ? (
          <div className="rounded-xl border border-slate-700/40 bg-slate-900/40 p-14 text-center">
            <p className="text-3xl mb-3">📋</p>
            <h4 className="text-base font-bold text-slate-300 mb-1.5">
              {diagnoses.length === 0 ? '진단 리포트가 없습니다' : '검색 결과가 없습니다'}
            </h4>
            <p className="text-slate-500 text-xs">
              {diagnoses.length === 0
                ? '사이드바에서 진단 항목을 선택해 AI 진단을 시작하세요.'
                : '다른 검색어나 필터를 시도해보세요.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(d => <DiagnosisCard key={d.id} diagnosis={d} />)}
          </div>
        )}
      </section>
    </div>
  )
}
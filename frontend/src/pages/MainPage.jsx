import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Users, Clock, CheckCircle, FileText, Filter, ChevronLeft, ChevronRight, Search, X } from 'lucide-react'

const COLOR = {
  blue:    { dot: 'bg-blue-500',    bg: 'bg-blue-900/20',    border: 'border-blue-800/30',    avatar: 'bg-blue-600/10 text-blue-400 border-blue-600/20' },
  purple:  { dot: 'bg-purple-500',  bg: 'bg-purple-900/20',  border: 'border-purple-800/30',  avatar: 'bg-purple-600/10 text-purple-400 border-purple-600/20' },
  emerald: { dot: 'bg-emerald-500', bg: 'bg-emerald-900/20', border: 'border-emerald-800/30', avatar: 'bg-emerald-600/10 text-emerald-400 border-emerald-600/20' },
  amber:   { dot: 'bg-amber-500',   bg: 'bg-amber-900/20',   border: 'border-amber-800/30',   avatar: 'bg-amber-600/10 text-amber-400 border-amber-600/20' },
}

const STATS = [
  { label: '전체 환자', icon: Users,        iconColor: 'text-blue-500',    bg: 'bg-blue-600/10'    },
  { label: '진료 대기', icon: Clock,        iconColor: 'text-amber-500',   bg: 'bg-amber-600/10'   },
  { label: '진료 완료', icon: CheckCircle,  iconColor: 'text-emerald-500', bg: 'bg-emerald-600/10' },
  { label: 'AI 분석',   icon: FileText,     iconColor: 'text-blue-400',    bg: 'bg-blue-600/10'    },
]

const PAGE_SIZE = 10

export default function MainPage() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [patients, setPatients]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [query, setQuery]         = useState('')
  const [page, setPage]           = useState(1)

  useEffect(() => {
    const token = localStorage.getItem('token')
    axios.get('/api/patients', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => setPatients(res.data))
      .catch(() => setPatients([]))
      .finally(() => setLoading(false))
  }, [])

  // 검색 필터 — 이름 또는 환자번호
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return patients
    return patients.filter(p =>
      p.name?.toLowerCase().includes(q) ||
      p.uid?.toLowerCase().includes(q)
    )
  }, [patients, query])

  // 페이지네이션
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paged      = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleSearch = (e) => {
    setQuery(e.target.value)
    setPage(1) // 검색 시 첫 페이지로
  }

  const statValues = [
    patients.length,
    patients.filter(p => p.status === 'WAITING').length || '-',
    patients.filter(p => p.status === 'DONE').length    || '-',
    '-',
  ]

  return (
    <div className="max-w-[1400px] mx-auto space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-black text-slate-50 tracking-tight">환자 관리 대시보드</h2>
        <p className="text-slate-500 text-sm mt-1">
          안녕하세요 <span className="text-blue-400 font-semibold">{user.name || '의사'}님</span> — 환자를 선택하면 상세 분석 리포트를 확인할 수 있습니다.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ label, icon: Icon, iconColor, bg }, i) => (
          <div key={label} className="bg-[#0F172A] border border-[#1E293B] p-5 rounded-2xl flex items-center gap-4">
            <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center flex-shrink-0`}>
              <Icon size={24} className={iconColor} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{label}</p>
              <p className="text-2xl font-black text-slate-50">{statValues[i]}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Patient table */}
      <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl overflow-hidden">
        {/* 테이블 헤더 */}
        <div className="px-8 py-5 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/50">
          <div className="flex items-center gap-4">
            <h3 className="text-xl font-bold text-slate-100">환자 목록</h3>
            <span className="px-2 py-0.5 bg-red-600/10 text-red-500 text-[10px] font-black rounded-md border border-red-600/20">LIVE</span>
            {query && (
              <span className="text-xs text-slate-500">
                {filtered.length}명 검색됨
              </span>
            )}
          </div>

          {/* 검색창 */}
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-72">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={query}
                onChange={handleSearch}
                placeholder="환자 이름 또는 환자번호 검색"
                className="w-full pl-9 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
              {query && (
                <button
                  onClick={() => { setQuery(''); setPage(1) }}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-700 transition-colors whitespace-nowrap">
              <Filter size={15} /> 필터
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-900/30 text-slate-500 text-[11px] uppercase tracking-widest font-black">
                {['환자번호', '환자이름', '나이', '성별', '혈액형', '최근검사일', '관리'].map((h, i) => (
                  <th key={h} className={`px-6 py-4 ${i === 6 ? 'text-right' : ''}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center">
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
                  </td>
                </tr>
              ) : paged.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center text-slate-500">
                    <p className="text-3xl mb-3">{query ? '🔍' : '🏥'}</p>
                    <p>{query ? `'${query}'에 해당하는 환자가 없습니다.` : '등록된 환자가 없습니다.'}</p>
                  </td>
                </tr>
              ) : (
                paged.map((p) => {
                  const c = COLOR.blue
                  return (
                    <tr
                      key={p.uid}
                      className="hover:bg-blue-600/5 transition-colors group cursor-pointer"
                      onDoubleClick={() => navigate(`/patients/${p.uid}`)}
                      title="더블클릭하면 상세 분석 페이지로 이동합니다"
                    >
                      <td className="px-6 py-4 text-slate-400 font-mono text-sm">{p.uid}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border ${c.avatar}`}>
                            {p.name?.[0] || '?'}
                          </div>
                          <span className="font-bold text-slate-100">{p.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-300">{p.age ? `${p.age}세` : '-'}</td>
                      <td className="px-6 py-4 text-slate-300">{p.gender || '-'}</td>
                      <td className="px-6 py-4 text-slate-300">{p.bloodType || '-'}</td>
                      <td className="px-6 py-4 text-slate-300">{p.lastExamDate || '-'}</td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => navigate(`/patients/${p.uid}`)}
                          className="px-4 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold opacity-0 group-hover:opacity-100 hover:bg-blue-600 hover:text-white transition-all"
                        >
                          상세보기
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 페이지네이션 */}
        <div className="px-8 py-4 border-t border-slate-800 flex justify-between items-center bg-slate-900/20">
          <p className="text-sm text-slate-500">
            총 {filtered.length}명
            {query && ` (전체 ${patients.length}명 중)`}
            {' · '}행을 더블클릭하면 상세 분석 페이지로 이동합니다
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition-all disabled:opacity-30"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(n => n === 1 || n === totalPages || Math.abs(n - page) <= 1)
              .reduce((acc, n, idx, arr) => {
                if (idx > 0 && n - arr[idx - 1] > 1) acc.push('...')
                acc.push(n)
                return acc
              }, [])
              .map((n, i) =>
                n === '...' ? (
                  <span key={`dot-${i}`} className="text-slate-600 px-1 text-sm">…</span>
                ) : (
                  <button
                    key={n}
                    onClick={() => setPage(n)}
                    className={`w-8 h-8 rounded-lg text-sm font-bold transition-all ${
                      page === n
                        ? 'bg-blue-600 text-white'
                        : 'hover:bg-slate-800 text-slate-500'
                    }`}
                  >
                    {n}
                  </button>
                )
              )}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition-all disabled:opacity-30"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

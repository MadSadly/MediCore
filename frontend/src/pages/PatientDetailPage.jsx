import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { FileText, Activity, Brain, Columns2, Circle, Shield, Eye } from 'lucide-react'

const DISEASE_LABELS = {
  'brain-tumor':    { label: '뇌종양 진단',   icon: Brain,    color: 'text-blue-400',   bg: 'bg-blue-600/10',   border: 'border-blue-600/20'   },
  'spine-disk':     { label: '허리디스크',    icon: Columns2, color: 'text-violet-400', bg: 'bg-violet-600/10', border: 'border-violet-600/20' },
  'colon-cancer':   { label: '대장암 예측',   icon: Circle,   color: 'text-amber-400',  bg: 'bg-amber-600/10',  border: 'border-amber-600/20'  },
  'kidney-failure': { label: '신부전 관리',   icon: Shield,   color: 'text-cyan-400',   bg: 'bg-cyan-600/10',   border: 'border-cyan-600/20'   },
  'skin-disease':   { label: '피부질환 분류', icon: Activity, color: 'text-rose-400',   bg: 'bg-rose-600/10',   border: 'border-rose-600/20'   },
  'eye-disease':    { label: '안과 질환',     icon: Eye,      color: 'text-teal-400',   bg: 'bg-teal-600/10',   border: 'border-teal-600/20'   },
}

function InfoRow({ label, value }) {
  return (
    <div>
      <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">{label}</p>
      <p className="text-slate-200 font-medium mt-0.5">{value || '-'}</p>
    </div>
  )
}

function DiagnosisCard({ diagnosis }) {
  const meta = DISEASE_LABELS[diagnosis.diseaseType] || {}
  const Icon = meta.icon || FileText
  return (
    <div className={`glass-card p-5 rounded-xl border ${meta.border || 'border-slate-700'}`}>
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-xl ${meta.bg || 'bg-slate-800'} flex items-center justify-center flex-shrink-0`}>
          <Icon size={20} className={meta.color || 'text-slate-400'} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className={`text-xs font-bold uppercase tracking-wider ${meta.color || 'text-slate-400'}`}>
              {meta.label || diagnosis.diseaseType}
            </span>
            <span className="text-[10px] text-slate-500">
              {new Date(diagnosis.createdAt).toLocaleDateString('ko-KR')}
            </span>
          </div>
          <h4 className="text-slate-100 font-bold">{diagnosis.title}</h4>
          {diagnosis.summary && (
            <p className="text-sm text-slate-400 mt-1 leading-relaxed">{diagnosis.summary}</p>
          )}
          {diagnosis.createdBy && (
            <p className="text-[10px] text-slate-600 mt-2">진단: {diagnosis.createdBy}</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function PatientDetailPage() {
  const { id } = useParams()
  const [patient, setPatient] = useState(null)
  const [diagnoses, setDiagnoses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      axios.get(`/api/patients/${id}`, { headers }),
      axios.get(`/api/patients/${id}/diagnoses`, { headers }),
    ])
      .then(([pRes, dRes]) => {
        setPatient(pRes.data)
        setDiagnoses(dRes.data)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">환자 정보를 불러오는 중...</p>
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
    <div className="max-w-5xl mx-auto space-y-6">

      {/* 환자 프로필 + 안내 */}
      <div className="grid grid-cols-12 gap-6">
        {/* 프로필 */}
        <section className="col-span-12 lg:col-span-4 glass-card p-6 rounded-xl">
          <div className="flex justify-between items-start mb-5">
            <h3 className="text-lg font-semibold text-slate-200">환자 프로필</h3>
            <span className="text-slate-500">🪪</span>
          </div>
          <div className="flex items-center gap-4 mb-5">
            <div className="w-14 h-14 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700 text-xl font-black text-slate-400">
              {patient.name?.[0] || '?'}
            </div>
            <div>
              <h4 className="text-lg font-bold text-slate-50">{patient.name}</h4>
              <p className="text-xs text-slate-500">UID: {patient.uid}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
            <InfoRow label="나이"    value={patient.age ? `${patient.age}세` : null} />
            <InfoRow label="성별"    value={patient.gender} />
            <InfoRow label="혈액형"  value={patient.bloodType} />
            <InfoRow label="최근검사" value={patient.lastExamDate} />
          </div>
          {(patient.assignedDoctor || patient.currentMedication || patient.medicalTeam) && (
            <div className="mt-4 pt-4 border-t border-slate-800 space-y-3">
              {patient.assignedDoctor    && <InfoRow label="담당의"   value={patient.assignedDoctor} />}
              {patient.currentMedication && <InfoRow label="복용약물"  value={patient.currentMedication} />}
              {patient.medicalTeam       && <InfoRow label="의료팀"   value={patient.medicalTeam} />}
            </div>
          )}
        </section>

        {/* 우측 패널 */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          {/* 진단 안내 */}
          <div className="glass-card p-6 rounded-xl flex-1">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-blue-500 text-xl">✨</span>
              <h3 className="text-lg font-semibold text-slate-200">진단 분석 안내</h3>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
              왼쪽 사이드바에서 진단 항목을 선택하면 해당 환자에 대한 AI 진단을 수행할 수 있습니다.
              진단 완료 후 리포트가 생성되며, 아래에 자동으로 표시됩니다.
            </p>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(DISEASE_LABELS).map(([key, { label, icon: Icon, color, bg, border }]) => (
                <div key={key} className={`flex items-center gap-2 p-2.5 rounded-lg border ${border} ${bg}`}>
                  <Icon size={14} className={color} />
                  <span className={`text-xs font-semibold ${color}`}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 리포트 현황 */}
          <div className="glass-card p-5 rounded-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600/10 rounded-xl flex items-center justify-center">
                  <FileText size={18} className="text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">누적 리포트</p>
                  <p className="text-2xl font-black text-slate-50">{diagnoses.length}건</p>
                </div>
              </div>
              {diagnoses.length > 0 && (
                <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full font-bold">
                  진단 기록 있음
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 진단 리포트 목록 */}
      <section>
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">
          진단 분석 리포트
        </h3>
        {diagnoses.length === 0 ? (
          <div className="glass-card rounded-xl p-12 text-center">
            <p className="text-4xl mb-4">📋</p>
            <h4 className="text-lg font-bold text-slate-300 mb-2">아직 진단 리포트가 없습니다</h4>
            <p className="text-slate-500 text-sm">
              왼쪽 사이드바에서 진단 항목을 선택해 첫 번째 리포트를 생성하세요.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {diagnoses.map(d => (
              <DiagnosisCard key={d.id} diagnosis={d} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

const AI_URL = import.meta.env.VITE_AI_URL || 'http://localhost:8000'

const CKD_STAGES = [
  { key: 'Normal_Stage1', label: '정상/1단계', gfr: 'GFR ≥ 90',  risk: 'LOW',  min: 90  },
  { key: 'Stage2',        label: '2단계',      gfr: 'GFR 60~89', risk: 'LOW',  min: 60  },
  { key: 'Stage3',        label: '3단계',      gfr: 'GFR 30~59', risk: 'MED',  min: 30  },
  { key: 'Stage4',        label: '4단계',      gfr: 'GFR 15~29', risk: 'HIGH', min: 15  },
  { key: 'Stage5',        label: '5단계',      gfr: 'GFR < 15',  risk: 'CRIT', min: -1  },
]

const STAGE_STYLE = {
  Normal_Stage1: { badge: 'bg-green-500/15 text-green-400 border-green-500/30',   bar: 'bg-green-500/40',  text: 'text-green-400'  },
  Stage2:        { badge: 'bg-green-500/15 text-green-400 border-green-500/30',   bar: 'bg-green-500/40',  text: 'text-green-400'  },
  Stage3:        { badge: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30', bar: 'bg-yellow-500/50', text: 'text-yellow-400' },
  Stage4:        { badge: 'bg-red-500/15 text-red-400 border-red-500/30',         bar: 'bg-red-500',       text: 'text-red-400'   },
  Stage5:        { badge: 'bg-red-500/15 text-red-500 border-red-500/30',         bar: 'bg-red-700',       text: 'text-red-500'   },
}

const RECOMMENDATIONS = {
  Normal_Stage1: ['정기 모니터링 유지 (연 1회 신기능 검사)', '혈압 목표 130/80 mmHg 이하 유지', '단백뇨 모니터링 지속'],
  Stage2:        ['신장내과 6개월 추적 진료', '혈압 목표 130/80 mmHg 이하', '단백뇨 발생 시 즉시 신장내과 의뢰'],
  Stage3:        ['신장내과 정기 진료 (3개월마다)', 'ACE억제제 또는 ARB 약물 치료 고려', '저단백·저칼륨 식이 관리 시작', '빈혈·뼈 합병증 선별 검사'],
  Stage4:        ['신장내과 전문의 즉시 진료', '투석 접근로(동정맥루) 조성 고려', '저단백·저칼륨·저인 식이 철저 준수', '혈압 목표 130/80 mmHg 이하 유지'],
  Stage5:        ['즉각적인 투석 치료 필요', '투석 접근로 즉시 확보', '신장이식 상담 의뢰', '응급 신장내과 의뢰'],
}

const FIELDS = [
  { key: 'sc',   label: '크레아티닌',  unit: 'mg/dL',  normal: '0.7~1.2', min: 0.7, max: 1.2,  placeholder: '예: 4.20', tag: 'Core'   },
  { key: 'bu',   label: 'BUN',        unit: 'mg/dL',  normal: '7~20',    min: 7,   max: 20,   placeholder: '예: 45.0', tag: 'Alert'  },
  { key: 'pot',  label: '칼륨',       unit: 'mEq/L',  normal: '3.5~5.0', min: 3.5, max: 5.0,  placeholder: '예: 5.80', tag: 'Alert'  },
  { key: 'al',   label: '알부민',     unit: 'g/dL',   normal: '3.5~5.0', min: 3.5, max: 5.0,  placeholder: '예: 3.8',  tag: 'Core'   },
  { key: 'bp',   label: '혈압',       unit: 'mmHg',   normal: '< 130',   min: 0,   max: 130,  placeholder: '예: 140',  tag: 'Core'   },
  { key: 'bgr',  label: '혈당',       unit: 'mg/dL',  normal: '70~140',  min: 70,  max: 140,  placeholder: '예: 180',  tag: 'Core'   },
  { key: 'hemo', label: '헤모글로빈', unit: 'g/dL',   normal: '12~17',   min: 12,  max: 17,   placeholder: '예: 10.5', tag: 'Comp'   },
]

// CKD-EPI 2021 (race-free) eGFR 자동 계산
function calcSlope(history) {
  const pts = history
    .map(h => ({ t: new Date(h.createdAt).getTime(), e: parseFloat(h.egfr) }))
    .filter(p => !isNaN(p.e) && p.e > 0)
  if (pts.length < 2) return null
  const t0 = pts[0].t
  const MS_PER_MONTH = 1000 * 60 * 60 * 24 * 30.44
  const normed = pts.map(p => ({ t: (p.t - t0) / MS_PER_MONTH, e: p.e }))
  const n = normed.length
  const sumT  = normed.reduce((s, p) => s + p.t, 0)
  const sumE  = normed.reduce((s, p) => s + p.e, 0)
  const sumTE = normed.reduce((s, p) => s + p.t * p.e, 0)
  const sumT2 = normed.reduce((s, p) => s + p.t * p.t, 0)
  const denom = n * sumT2 - sumT * sumT
  if (Math.abs(denom) < 1e-9) return 0
  return (n * sumTE - sumT * sumE) / denom
}

function getTrendInfo(slope) {
  if (slope === null) return null
  if (slope > 0)   return { label: '호전 중',      color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
  if (slope > -2)  return { label: '안정',          color: 'text-blue-400',    bg: 'bg-blue-500/10 border-blue-500/20' }
  if (slope > -5)  return { label: '완만한 악화',   color: 'text-yellow-400',  bg: 'bg-yellow-500/10 border-yellow-500/20' }
  return               { label: '급격한 악화',   color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/20' }
}

function EgfrSparkline({ history }) {
  const pts = history.filter(h => parseFloat(h.egfr) > 0)
  if (pts.length < 2) return null
  const vals = pts.map(h => parseFloat(h.egfr))
  const minV = Math.min(...vals)
  const maxV = Math.max(...vals)
  const range = maxV - minV || 1
  const W = 160, H = 40, PAD = 4
  const points = vals.map((v, i) => {
    const x = PAD + (i / (vals.length - 1)) * (W - PAD * 2)
    const y = PAD + (1 - (v - minV) / range) * (H - PAD * 2)
    return `${x},${y}`
  }).join(' ')
  return (
    <svg width={W} height={H} className="w-full">
      <polyline points={points} fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeLinejoin="round" />
      {vals.map((v, i) => {
        const x = PAD + (i / (vals.length - 1)) * (W - PAD * 2)
        const y = PAD + (1 - (v - minV) / range) * (H - PAD * 2)
        return <circle key={i} cx={x} cy={y} r="2.5" fill="#3b82f6" />
      })}
    </svg>
  )
}

function calcEgfr(sc, age, sex) {
  const scr = parseFloat(sc)
  const a   = parseFloat(age)
  if (isNaN(scr) || isNaN(a) || scr <= 0 || a <= 0) return null
  const isFemale = sex === 'F'
  const kappa  = isFemale ? 0.7    : 0.9
  const alpha  = isFemale ? -0.241 : -0.302
  const sexFac = isFemale ? 1.012  : 1.0
  const ratio  = scr / kappa
  const egfr   = 142
    * Math.pow(Math.min(ratio, 1), alpha)
    * Math.pow(Math.max(ratio, 1), -1.200)
    * Math.pow(0.9938, a)
    * sexFac
  return Math.round(egfr * 10) / 10
}

function getGfrStage(gfr) {
  const v = parseFloat(gfr)
  if (isNaN(v)) return null
  if (v >= 90) return 'Normal_Stage1'
  if (v >= 60) return 'Stage2'
  if (v >= 30) return 'Stage3'
  if (v >= 15) return 'Stage4'
  return 'Stage5'
}

function isOutOfRange(val, min, max) {
  const v = parseFloat(val)
  return !isNaN(v) && (v < min || v > max)
}

function ToggleSwitch({ label, sub, value, onChange }) {
  return (
    <div className="bg-[#0d1117] border border-slate-700 rounded-xl p-4 flex items-center justify-between">
      <div>
        <p className="text-xs font-semibold text-slate-300">{label}</p>
        <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative w-11 h-6 rounded-full transition-all ${value ? 'bg-blue-600' : 'bg-slate-700'}`}
      >
        <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-all ${value ? 'right-1' : 'left-1'}`} />
      </button>
    </div>
  )
}

function CKDStepList({ activeKey }) {
  return (
    <div className="space-y-2">
      {CKD_STAGES.map(s => {
        const active = s.key === activeKey
        return (
          <div key={s.key} className={`flex items-center gap-3 p-2.5 rounded-xl ${active ? 'bg-red-500/10 border border-red-500/30' : 'bg-slate-800/30'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${active ? 'bg-red-500 text-white' : 'bg-slate-700 text-slate-400'}`}>
              {s.label.replace('정상/', '').replace('단계', '')}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-[10px] ${active ? 'font-bold text-red-400' : 'font-semibold text-slate-400'} truncate`}>
                {s.label}{active ? ' ← 현재' : ''}
              </p>
              <p className={`text-[9px] ${active ? 'text-red-500/70' : 'text-slate-600'}`}>{s.gfr}</p>
            </div>
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 ${
              s.risk === 'LOW'  ? 'text-slate-600 bg-slate-800' :
              s.risk === 'MED'  ? 'text-yellow-600 bg-yellow-900/30' :
                                  'text-red-400 bg-red-900/30'
            }`}>{s.risk}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function KidneyFailurePage() {
  const { id: patientId } = useParams()

  const [screen, setScreen]         = useState('input')
  const [form, setForm]             = useState({ sc: '', bu: '', pot: '', al: '', bp: '', bgr: '', hemo: '', age: '', sex: 'M', htn: false, dm: false, pe: false, query: '' })
  const [result, setResult]         = useState(null)
  const [history, setHistory]       = useState([])
  const [selectedHistory, setSelectedHistory] = useState(null)
  const [error, setError]           = useState(null)
  const [saving, setSaving]         = useState(false)
  const [saved, setSaved]           = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)

  const fetchHistory = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const { data } = await axios.get(
        `/api/patients/${patientId}/diagnoses/kidney/history`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setHistory(data.slice().reverse())
    } catch { /* optional */ }
  }, [patientId])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const token = localStorage.getItem('token')
        const { data } = await axios.get(
          `/api/patients/${patientId}/diagnoses/kidney/history`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        if (!cancelled) setHistory(data.slice().reverse())
      } catch { /* optional */ }
    })()
    return () => { cancelled = true }
  }, [patientId])

  const computedEgfr = calcEgfr(form.sc, form.age, form.sex)
  const previewStage = getGfrStage(computedEgfr)

  const handleSubmit = async () => {
    setError(null)
    setScreen('loading')
    try {
      const { data } = await axios.post(`${AI_URL}/ai/kidney/diagnose`, {
        sc:    form.sc   ? parseFloat(form.sc)   : null,
        egfr:  computedEgfr,
        age:   form.age  ? parseFloat(form.age)  : null,
        bu:    form.bu   ? parseFloat(form.bu)   : null,
        pot:   form.pot  ? parseFloat(form.pot)  : null,
        al:    form.al   ? parseFloat(form.al)   : null,
        bp:    form.bp   ? parseFloat(form.bp)   : null,
        bgr:   form.bgr  ? parseFloat(form.bgr)  : null,
        hemo:  form.hemo ? parseFloat(form.hemo) : null,
        htn:   form.htn  ? 'yes' : 'no',
        dm:    form.dm   ? 'yes' : 'no',
        pe:    form.pe   ? 'yes' : 'no',
        query: form.query || null,
      })
      setResult(data)
      setScreen('result')
      // 이력 갱신
      fetchHistory()
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'AI 서버 연결 실패')
      setScreen('input')
    }
  }

  const handleSave = async () => {
    if (!result || saving || saved) return
    setShowSaveModal(false)
    setSaving(true)
    const token = localStorage.getItem('token')
    try {
      await axios.post(`/api/patients/${patientId}/diagnoses/kidney`, {
        result:           result.prediction,
        confidence:       result.confidence,
        description:      result.description,
        severity:         result.severity,
        dialysisRequired: result.dialysis_required,
        probabilities:    result.probabilities,
        ragAnswer:        result.rag_answer || null,
        egfr:             computedEgfr,
        sc:               form.sc   ? parseFloat(form.sc)   : null,
        bu:               form.bu   ? parseFloat(form.bu)   : null,
        pot:              form.pot  ? parseFloat(form.pot)  : null,
        al:               form.al   ? parseFloat(form.al)   : null,
        bp:               form.bp   ? parseFloat(form.bp)   : null,
        bgr:              form.bgr  ? parseFloat(form.bgr)  : null,
        hemo:             form.hemo ? parseFloat(form.hemo) : null,
        htn:              form.htn  ? 'yes' : 'no',
        dm:               form.dm   ? 'yes' : 'no',
        pe:               form.pe   ? 'yes' : 'no',
        age:              form.age  ? parseFloat(form.age)  : null,
        sex:              form.sex  || null,
      }, { headers: { Authorization: `Bearer ${token}` } })
      setSaved(true)
    } catch {
      /* 저장 실패는 조용히 처리 */
    } finally {
      setSaving(false)
    }
  }

  // ── 입력 화면 ──────────────────────────────────────────────────────
  if (screen === 'input') return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto space-y-6">

        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-blue-500 rounded-full" />
          <div>
            <p className="text-[10px] text-blue-400 font-bold tracking-widest uppercase">Kidney · NJ</p>
            <h3 className="text-xl font-bold text-white">신부전 임상수치 입력</h3>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            {error}
          </div>
        )}

        <div className="grid grid-cols-3 gap-6">
          {/* 왼쪽 2/3 */}
          <div className="col-span-2 space-y-5">

            {/* 환자 기본 정보 + eGFR 자동 계산 */}
            <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-5">환자 기본 정보 (eGFR 자동 계산)</p>
              <div className="grid grid-cols-3 gap-4 items-end">
                {/* 나이 */}
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1.5">나이</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={form.age}
                      placeholder="예: 65"
                      onChange={e => setForm(p => ({ ...p, age: e.target.value }))}
                      className="w-full bg-[#0d1117] border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors pr-10"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-500">세</span>
                  </div>
                </div>
                {/* 성별 */}
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1.5">성별</label>
                  <div className="flex gap-2">
                    {[['M', '남성'], ['F', '여성']].map(([val, label]) => (
                      <button
                        key={val}
                        type="button"
                        onClick={() => setForm(p => ({ ...p, sex: val }))}
                        className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all border ${
                          form.sex === val
                            ? 'bg-blue-600/20 border-blue-500/50 text-blue-300'
                            : 'bg-[#0d1117] border-slate-700 text-slate-500 hover:border-slate-600'
                        }`}
                      >{label}</button>
                    ))}
                  </div>
                </div>
                {/* 자동 계산된 eGFR */}
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-xs font-semibold text-slate-300">eGFR</label>
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-bold text-emerald-400 bg-emerald-500/10">자동계산</span>
                  </div>
                  <div className={`w-full border rounded-xl px-4 py-2.5 flex items-center justify-between ${
                    computedEgfr !== null ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-[#0d1117] border-slate-700'
                  }`}>
                    <span className={`text-sm font-bold ${computedEgfr !== null ? 'text-emerald-400' : 'text-slate-600'}`}>
                      {computedEgfr !== null ? computedEgfr : '—'}
                    </span>
                    <span className="text-[10px] text-slate-500">mL/min</span>
                  </div>
                  {computedEgfr !== null && (
                    <p className="text-[9px] text-slate-600 mt-1">CKD-EPI 2021 공식 적용</p>
                  )}
                </div>
              </div>
            </div>

            {/* 신장 기능 수치 */}
            <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-5">신장 기능 수치</p>
              <div className="grid grid-cols-2 gap-4">
                {FIELDS.map(f => {
                  const warn = form[f.key] !== '' && isOutOfRange(form[f.key], f.min, f.max)
                  const tagColor = f.tag === 'Core' ? 'text-blue-400 bg-blue-500/10' : f.tag === 'Alert' ? 'text-red-400 bg-red-500/10' : 'text-slate-400 bg-slate-700/50'
                  return (
                    <div key={f.key}>
                      <div className="flex justify-between items-center mb-1.5">
                        <div className="flex items-center gap-2">
                          <label className="text-xs font-semibold text-slate-300">{f.label}</label>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${tagColor}`}>{f.tag}</span>
                        </div>
                        <span className="text-[10px] text-slate-500">정상 {f.normal} {f.unit}</span>
                      </div>
                      <div className="relative">
                        <input
                          type="number"
                          value={form[f.key]}
                          placeholder={f.placeholder}
                          onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                          className={`w-full bg-[#0d1117] border rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors pr-16 ${warn ? 'border-amber-500/60' : 'border-slate-700'}`}
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-500">{f.unit}</span>
                      </div>
                      {warn && (
                        <p className="text-[10px] text-amber-400 mt-1 flex items-center gap-1">
                          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                          정상 범위를 벗어났습니다
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* 동반 증상 */}
            <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">동반 증상</p>
              <div className="grid grid-cols-3 gap-3">
                <ToggleSwitch label="고혈압" sub="Hypertension" value={form.htn} onChange={v => setForm(p => ({ ...p, htn: v }))} />
                <ToggleSwitch label="당뇨"   sub="Diabetes"     value={form.dm}  onChange={v => setForm(p => ({ ...p, dm: v }))}  />
                <ToggleSwitch label="부종"   sub="Edema"        value={form.pe}  onChange={v => setForm(p => ({ ...p, pe: v }))}  />
              </div>
            </div>

            {/* 추가 질문 */}
            <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">
                AI에게 추가 질문 <span className="text-slate-600 normal-case font-normal">(선택)</span>
              </p>
              <textarea
                rows={2}
                value={form.query}
                onChange={e => setForm(p => ({ ...p, query: e.target.value }))}
                placeholder="예: 투석 시작 시기, 식이 제한 기준, 약물 조정 여부 등"
                className="w-full bg-[#0d1117] border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors resize-none"
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSubmit}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl text-sm font-bold transition-all flex items-center gap-2"
                style={{ boxShadow: '0 0 15px rgba(37,99,235,0.2)' }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
                AI 진단 요청
              </button>
            </div>

            {/* 과거 진단 이력 */}
            {history.length > 0 && (
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">과거 진단 이력</p>
                <div className="space-y-2">
                  {history.map(h => {
                    const st = STAGE_STYLE[h.result] || STAGE_STYLE['Stage3']
                    const stageInfo = CKD_STAGES.find(s => s.key === h.result)
                    return (
                      <button
                        key={h.id}
                        onClick={() => { setSelectedHistory(h); setScreen('historyDetail') }}
                        className="w-full flex items-center gap-3 bg-[#0d1117] border border-slate-800 hover:border-slate-600 rounded-xl px-4 py-3 text-left transition-all group"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${st.badge}`}>
                              {stageInfo?.label || h.result}
                            </span>
                            {h.dialysisRequired && (
                              <span className="text-[9px] text-red-400 bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 rounded">투석 필요</span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1">
                            {h.egfr != null && (
                              <span className="text-[10px] text-slate-500">eGFR <span className="text-slate-300 font-semibold">{Number(h.egfr).toFixed(1)}</span></span>
                            )}
                            {h.confidence != null && (
                              <span className="text-[10px] text-slate-500">신뢰도 <span className="text-slate-300 font-semibold">{(h.confidence * 100).toFixed(1)}%</span></span>
                            )}
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-[10px] text-slate-500">
                            {new Date(h.createdAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                          </p>
                          <p className="text-[9px] text-slate-600">
                            {new Date(h.createdAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-600 group-hover:text-slate-400 flex-shrink-0"><path d="m9 18 6-6-6-6"/></svg>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* 오른쪽 1/3 — CKD 단계 미리보기 */}
          <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5 self-start sticky top-4">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">CKD 단계 미리보기</p>
            {previewStage
              ? <CKDStepList activeKey={previewStage} />
              : (
                <div className="text-center py-8">
                  <p className="text-slate-600 text-xs">크레아티닌 + 나이/성별 입력 시<br />eGFR이 자동 계산되어<br />단계를 미리 확인할 수 있습니다</p>
                </div>
              )
            }
            {(previewStage === 'Stage4' || previewStage === 'Stage5') && (
              <div className="mt-4 bg-orange-500/10 border border-orange-500/30 rounded-xl p-3 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-orange-400 flex-shrink-0"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
                <p className="text-[10px] text-orange-300 font-semibold">투석 준비 권고 단계</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )

  // ── 로딩 화면 ──────────────────────────────────────────────────────
  if (screen === 'loading') return (
    <div className="p-8 flex items-center justify-center min-h-[70vh]">
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="relative mx-auto w-24 h-24">
          <div className="w-24 h-24 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-blue-400 animate-pulse">
              <path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/>
              <path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>
            </svg>
          </div>
          <div className="absolute inset-0 rounded-full border-2 border-blue-500/30 animate-ping" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white mb-2">AI 진단 중입니다</h3>
          <p className="text-sm text-slate-400">TabNet 모델로 CKD 단계를 분류하고 있습니다</p>
        </div>
        <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6 text-left space-y-3">
          {[
            { label: '임상 수치 전처리 완료',     done: true  },
            { label: 'CKD 단계 분류 중...',       done: false, active: true },
            { label: '의료 가이드라인 검색 중...', done: false },
            { label: '진단 보고서 생성 중...',     done: false },
          ].map((step, i) => (
            <div key={i} className={`flex items-center gap-3 ${step.done || step.active ? 'opacity-100' : 'opacity-40'}`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                step.done   ? 'bg-green-500/20 border border-green-500/40' :
                step.active ? 'bg-blue-500/20 border border-blue-500/40 animate-pulse' :
                              'bg-slate-700 border border-slate-600'
              }`}>
                {step.done
                  ? <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-green-400"><path d="M20 6 9 17l-5-5"/></svg>
                  : <div className={`w-2 h-2 rounded-full ${step.active ? 'bg-blue-400' : 'bg-slate-500'}`} />
                }
              </div>
              <span className={`text-xs font-semibold ${step.done ? 'text-green-400' : step.active ? 'text-blue-400' : 'text-slate-500'}`}>{step.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  // ── 결과 화면 ──────────────────────────────────────────────────────
  if (screen === 'result' && result) {
    const st        = STAGE_STYLE[result.prediction] || STAGE_STYLE['Stage3']
    const recs      = RECOMMENDATIONS[result.prediction] || RECOMMENDATIONS['Stage3']
    const stageInfo = CKD_STAGES.find(s => s.key === result.prediction)
    const recColors = ['red', 'orange', 'yellow', 'blue']

    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto space-y-5">

          {/* 타이틀 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-1 h-8 bg-green-500 rounded-full" />
              <div>
                <p className="text-[10px] text-green-400 font-bold tracking-widest uppercase">진단 완료 · Kidney</p>
                <h3 className="text-xl font-bold text-white">신부전 진단 보고서</h3>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setScreen('input'); setSaved(false) }}
                className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2.5 rounded-xl text-xs font-bold transition-all border border-slate-700"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
                다시 입력
              </button>
              <button
                onClick={() => { if (!saved && !saving) setShowSaveModal(true) }}
                disabled={saving || saved}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${saved ? 'bg-green-600 text-white cursor-default' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
                style={{ boxShadow: '0 0 15px rgba(37,99,235,0.2)' }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                {saved ? '저장 완료' : saving ? '저장 중...' : 'DB에 저장'}
              </button>
            </div>
          </div>


          {/* 위험 알림 */}
          {result.alerts && result.alerts.length > 0 && (
            <div className="space-y-2">
              {result.alerts.map((alert, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 rounded-xl px-4 py-3 border text-sm font-medium ${
                    alert.level === 'critical'
                      ? 'bg-red-500/10 border-red-500/30 text-red-300'
                      : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300'
                  }`}
                >
                  <span className="mt-0.5 shrink-0 text-base">
                    {alert.level === 'critical' ? '🚨' : '⚠️'}
                  </span>
                  <span>{alert.message}</span>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-3 gap-5">
            {/* 왼쪽 2/3 */}
            <div className="col-span-2 space-y-5">

              {/* 입력 수치 요약 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">입력 수치 요약</p>
                <div className="grid grid-cols-4 gap-3">
                  {/* 자동 계산된 eGFR */}
                  {computedEgfr !== null && (
                    <div className="border rounded-xl p-3 text-center bg-emerald-500/5 border-emerald-500/20">
                      <p className="text-[9px] text-slate-500 mb-1">GFR <span className="text-emerald-500/70">자동</span></p>
                      <p className="text-base font-bold text-emerald-400">{computedEgfr}</p>
                      <p className="text-[9px] text-slate-600">mL/min</p>
                    </div>
                  )}
                  {FIELDS.map(f => {
                    if (!form[f.key]) return null
                    const out = isOutOfRange(form[f.key], f.min, f.max)
                    return (
                      <div key={f.key} className={`border rounded-xl p-3 text-center ${out ? 'bg-red-500/8 border-red-500/20' : 'bg-slate-800/30 border-slate-700'}`}>
                        <p className="text-[9px] text-slate-500 mb-1">{f.label}</p>
                        <p className={`text-base font-bold ${out ? 'text-red-400' : 'text-slate-200'}`}>{form[f.key]}</p>
                        <p className="text-[9px] text-slate-600">{f.unit}</p>
                        {out && <p className="text-[9px] text-red-400 mt-1 font-semibold">↑ 주의</p>}
                      </div>
                    )
                  })}
                </div>
                {(form.htn || form.dm || form.pe) && (
                  <div className="flex gap-2 mt-3">
                    {form.htn && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">고혈압</span>}
                    {form.dm  && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">당뇨</span>}
                    {form.pe  && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">부종</span>}
                  </div>
                )}
              </div>

              {/* AI 진단 근거 · 피처 기여도 */}
              {result.feature_importance && Object.keys(result.feature_importance).length > 0 && (() => {
                const entries = Object.entries(result.feature_importance)
                const maxVal = entries[0]?.[1] ?? 1
                return (
                  <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-5 h-5 rounded bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-violet-400"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                      </div>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI 진단 근거 · 피처 기여도</p>
                    </div>
                    <div className="space-y-2">
                      {entries.map(([feat, val], i) => {
                        const pct = maxVal > 0 ? (val / maxVal) * 100 : 0
                        const barColor = i < 3
                          ? 'bg-violet-500'
                          : i < 6
                          ? 'bg-violet-500/60'
                          : 'bg-violet-500/30'
                        return (
                          <div key={feat} className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-400 w-20 flex-shrink-0 text-right truncate">{feat}</span>
                            <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${barColor}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-[10px] text-slate-500 w-10 flex-shrink-0 text-right">
                              {(val * 100).toFixed(1)}%
                            </span>
                          </div>
                        )
                      })}
                    </div>
                    <p className="text-[9px] text-slate-600 mt-3">TabNet Attention 기반 · 해당 예측에서 각 피처가 기여한 상대적 비중</p>
                  </div>
                )
              })()}

              {/* AI 진단 의견 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-5 h-5 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-blue-400"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/></svg>
                  </div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI 진단 의견</p>
                  <span className="text-[9px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full ml-auto">
                    신뢰도 {(result.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-[#0d1117] rounded-xl p-4 border border-slate-800">
                  <pre className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap break-words">{result.rag_answer}</pre>
                </div>
                {result.rag_sources && result.rag_sources.length > 0 && (
                  <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                    <span className="text-[9px] text-slate-600">출처:</span>
                    {result.rag_sources.map((src, i) => (
                      <span key={i} className="text-[9px] bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full">
                        {src}
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-slate-600 mt-2">{result.description}</p>
              </div>

              {/* 치료 권고사항 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">치료 권고사항</p>
                <div className="space-y-2.5">
                  {recs.map((rec, i) => {
                    const c = recColors[Math.min(i, recColors.length - 1)]
                    const colorMap = {
                      red:    'bg-red-500/20 border-red-500/30 text-red-400',
                      orange: 'bg-orange-500/20 border-orange-500/30 text-orange-400',
                      yellow: 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400',
                      blue:   'bg-blue-500/20 border-blue-500/30 text-blue-400',
                    }
                    return (
                      <div key={i} className="flex items-start gap-3 bg-[#0d1117] rounded-xl p-3 border border-slate-800">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 mt-0.5 border ${colorMap[c]}`}>{i + 1}</span>
                        <p className="text-sm text-slate-300">{rec}</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* 면책 */}
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4 flex items-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-amber-400 flex-shrink-0 mt-0.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                <p className="text-[10px] text-amber-300/80 leading-relaxed">본 의견은 AI 보조 의견이며, 최종 진단과 처방은 반드시 의사가 결정합니다.</p>
              </div>
            </div>

            {/* 오른쪽 1/3 */}
            <div className="space-y-4">

              {/* CKD 단계 바 차트 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">CKD 단계</p>
                <div className="flex items-end justify-between gap-1 h-20 mb-3">
                  {CKD_STAGES.map((s, i) => {
                    const active = s.key === result.prediction
                    const heights = ['20%', '35%', '55%', '75%', '100%']
                    const ss = STAGE_STYLE[s.key]
                    return (
                      <div key={s.key} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className={`w-full rounded-t transition-all ${ss.bar} ${active ? 'ring-2 ring-offset-1 ring-offset-[#151921]' : ''}`}
                          style={{ height: heights[i] }}
                        />
                        <p className={`text-[8px] ${active ? ss.text + ' font-bold' : 'text-slate-600'}`}>
                          {s.label.replace('정상/', '').replace('단계', '')}{active ? '↑' : ''}
                        </p>
                      </div>
                    )
                  })}
                </div>
                <div className={`border rounded-xl p-3 text-center ${st.badge}`}>
                  <p className={`text-xs font-bold ${st.text}`}>{stageInfo?.label} / {stageInfo?.risk}</p>
                  {result.dialysis_required && (
                    <p className={`text-[10px] mt-0.5 ${st.text} opacity-80`}>🔴 투석 필요</p>
                  )}
                </div>
              </div>

              {/* eGFR 추세 */}
              {(() => {
                const slope = calcSlope(history)
                const trend = getTrendInfo(slope)
                return (
                  <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">eGFR 추세</p>
                    {history.filter(h => parseFloat(h.egfr) > 0).length < 2 ? (
                      <p className="text-[11px] text-slate-600 text-center py-3">
                        진단 기록이 2회 이상 저장되면<br />추세가 표시됩니다
                      </p>
                    ) : (
                      <div className="space-y-3">
                        <EgfrSparkline history={history} />
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] px-2 py-1 rounded border font-bold ${trend.bg} ${trend.color}`}>
                            {trend.label}
                          </span>
                          <span className={`text-xs font-bold ${trend.color}`}>
                            월 {slope >= 0 ? '+' : ''}{slope.toFixed(1)} mL/min
                          </span>
                        </div>
                        <div className="flex justify-between text-[9px] text-slate-600">
                          <span>{new Date(history[0].createdAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}</span>
                          <span>{new Date(history[history.length - 1].createdAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}

              {/* 단계별 확률 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">단계별 확률</p>
                <div className="space-y-2">
                  {Object.entries(result.probabilities)
                    .sort(([, a], [, b]) => b - a)
                    .map(([stage, prob]) => {
                      const ss  = STAGE_STYLE[stage] || STAGE_STYLE['Stage3']
                      const pct = (prob * 100).toFixed(1)
                      const info = CKD_STAGES.find(c => c.key === stage)
                      return (
                        <div key={stage}>
                          <div className="flex justify-between text-[10px] mb-0.5">
                            <span className="text-slate-400">{info?.label || stage}</span>
                            <span className={`font-bold ${ss.text}`}>{pct}%</span>
                          </div>
                          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${ss.bar}`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      )
                    })
                  }
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 저장 확인 모달 */}
        {showSaveModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
            onClick={() => setShowSaveModal(false)}
          >
            <div
              className="bg-[#0f1623] border border-slate-700 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-blue-400">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-bold text-white">진단 결과 저장</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">아래 결과를 환자 기록에 저장합니다</p>
                </div>
              </div>

              <div className="bg-[#0d1117] rounded-xl p-4 border border-slate-800 space-y-3 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${(STAGE_STYLE[result.prediction] || STAGE_STYLE['Stage3']).badge}`}>
                      {result.prediction?.replace('Normal_', '') ?? '-'}
                    </span>
                    {result.dialysis_required && (
                      <span className="text-[10px] bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full font-bold">투석 필요</span>
                    )}
                  </div>
                  <span className="text-xs text-slate-400">신뢰도 <span className="text-white font-bold">{(result.confidence * 100).toFixed(1)}%</span></span>
                </div>
                <p className="text-[11px] text-slate-400">{result.description}</p>
                <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-800">
                  {computedEgfr !== null && (
                    <div className="text-center">
                      <p className="text-[9px] text-slate-600 mb-0.5">eGFR</p>
                      <p className="text-xs font-bold text-emerald-400">{computedEgfr}</p>
                    </div>
                  )}
                  {form.sc && (
                    <div className="text-center">
                      <p className="text-[9px] text-slate-600 mb-0.5">크레아티닌</p>
                      <p className="text-xs font-bold text-slate-200">{form.sc}</p>
                    </div>
                  )}
                  {form.bu && (
                    <div className="text-center">
                      <p className="text-[9px] text-slate-600 mb-0.5">BUN</p>
                      <p className="text-xs font-bold text-slate-200">{form.bu}</p>
                    </div>
                  )}
                </div>
              </div>

              {result.alerts?.some(a => a.level === 'critical') && (
                <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-3 py-2.5 mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-red-400 flex-shrink-0">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>
                  </svg>
                  <p className="text-[10px] text-red-300">위험 수치가 포함된 결과입니다. 저장 후 즉각 조치가 필요합니다.</p>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2.5 rounded-xl text-xs font-bold transition-all border border-slate-700"
                >
                  취소
                </button>
                <button
                  onClick={handleSave}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-xl text-xs font-bold transition-all"
                >
                  저장 확인
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── 이력 상세 화면 ────────────────────────────────────────────────
  if (screen === 'historyDetail' && selectedHistory) {
    const h       = selectedHistory
    const st      = STAGE_STYLE[h.result] || STAGE_STYLE['Stage3']
    const stageInfo = CKD_STAGES.find(s => s.key === h.result)
    const recs    = RECOMMENDATIONS[h.result] || RECOMMENDATIONS['Stage3']
    const recColors = ['red', 'orange', 'yellow', 'blue']

    const histFields = [
      { key: 'sc',   label: '크레아티닌',  unit: 'mg/dL',  min: 0.7, max: 1.2 },
      { key: 'bu',   label: 'BUN',        unit: 'mg/dL',  min: 7,   max: 20  },
      { key: 'pot',  label: '칼륨',       unit: 'mEq/L',  min: 3.5, max: 5.0 },
      { key: 'al',   label: '알부민',     unit: 'g/dL',   min: 3.5, max: 5.0 },
      { key: 'bp',   label: '혈압',       unit: 'mmHg',   min: 0,   max: 130 },
      { key: 'bgr',  label: '혈당',       unit: 'mg/dL',  min: 70,  max: 140 },
      { key: 'hemo', label: '헤모글로빈', unit: 'g/dL',   min: 12,  max: 17  },
    ]

    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto space-y-5">

          {/* 타이틀 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-1 h-8 bg-slate-500 rounded-full" />
              <div>
                <p className="text-[10px] text-slate-400 font-bold tracking-widest uppercase">
                  과거 기록 · {new Date(h.createdAt).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                  {' '}{new Date(h.createdAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </p>
                <h3 className="text-xl font-bold text-white">신부전 진단 이력</h3>
              </div>
            </div>
            <button
              onClick={() => setScreen('input')}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2.5 rounded-xl text-xs font-bold transition-all border border-slate-700"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
              목록으로
            </button>
          </div>

          <div className="grid grid-cols-3 gap-5">
            {/* 왼쪽 2/3 */}
            <div className="col-span-2 space-y-5">

              {/* 임상 수치 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">기록된 임상 수치</p>
                <div className="grid grid-cols-4 gap-3">
                  {h.egfr != null && (
                    <div className="border rounded-xl p-3 text-center bg-emerald-500/5 border-emerald-500/20">
                      <p className="text-[9px] text-slate-500 mb-1">eGFR <span className="text-emerald-500/70">자동</span></p>
                      <p className="text-base font-bold text-emerald-400">{Number(h.egfr).toFixed(1)}</p>
                      <p className="text-[9px] text-slate-600">mL/min</p>
                    </div>
                  )}
                  {histFields.map(f => {
                    if (h[f.key] == null) return null
                    const out = h[f.key] < f.min || h[f.key] > f.max
                    return (
                      <div key={f.key} className={`border rounded-xl p-3 text-center ${out ? 'bg-red-500/8 border-red-500/20' : 'bg-slate-800/30 border-slate-700'}`}>
                        <p className="text-[9px] text-slate-500 mb-1">{f.label}</p>
                        <p className={`text-base font-bold ${out ? 'text-red-400' : 'text-slate-200'}`}>{h[f.key]}</p>
                        <p className="text-[9px] text-slate-600">{f.unit}</p>
                        {out && <p className="text-[9px] text-red-400 mt-1 font-semibold">↑ 주의</p>}
                      </div>
                    )
                  })}
                </div>
                {(h.htn === 'yes' || h.dm === 'yes' || h.pe === 'yes') && (
                  <div className="flex gap-2 mt-3">
                    {h.htn === 'yes' && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">고혈압</span>}
                    {h.dm  === 'yes' && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">당뇨</span>}
                    {h.pe  === 'yes' && <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-full">부종</span>}
                  </div>
                )}
              </div>

              {/* 진단 소견 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">진단 소견</p>
                  {h.confidence != null && (
                    <span className="text-[9px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full ml-auto">
                      신뢰도 {(h.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <div className="bg-[#0d1117] rounded-xl p-4 text-sm text-slate-300 leading-relaxed border border-slate-800">
                  {h.description || '기록된 소견이 없습니다.'}
                </div>
              </div>

              {/* AI 진단 소견 */}
              {h.ragAnswer && (
                <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-5 h-5 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-blue-400"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/></svg>
                    </div>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">당시 AI 진단 소견</p>
                  </div>
                  <div className="bg-[#0d1117] rounded-xl p-4 border border-slate-800">
                    <pre className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap break-words">{h.ragAnswer}</pre>
                  </div>
                </div>
              )}


              {/* 치료 권고사항 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">당시 치료 권고사항</p>
                <div className="space-y-2.5">
                  {recs.map((rec, i) => {
                    const c = recColors[Math.min(i, recColors.length - 1)]
                    const colorMap = {
                      red:    'bg-red-500/20 border-red-500/30 text-red-400',
                      orange: 'bg-orange-500/20 border-orange-500/30 text-orange-400',
                      yellow: 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400',
                      blue:   'bg-blue-500/20 border-blue-500/30 text-blue-400',
                    }
                    return (
                      <div key={i} className="flex items-start gap-3 bg-[#0d1117] rounded-xl p-3 border border-slate-800">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 mt-0.5 border ${colorMap[c]}`}>{i + 1}</span>
                        <p className="text-sm text-slate-300">{rec}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* 오른쪽 1/3 */}
            <div className="space-y-4">

              {/* CKD 단계 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">CKD 단계</p>
                <div className="flex items-end justify-between gap-1 h-20 mb-3">
                  {CKD_STAGES.map((s, i) => {
                    const active = s.key === h.result
                    const heights = ['20%', '35%', '55%', '75%', '100%']
                    const ss = STAGE_STYLE[s.key]
                    return (
                      <div key={s.key} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className={`w-full rounded-t transition-all ${ss.bar} ${active ? 'ring-2 ring-offset-1 ring-offset-[#151921]' : ''}`}
                          style={{ height: heights[i] }}
                        />
                        <p className={`text-[8px] ${active ? ss.text + ' font-bold' : 'text-slate-600'}`}>
                          {s.label.replace('정상/', '').replace('단계', '')}{active ? '↑' : ''}
                        </p>
                      </div>
                    )
                  })}
                </div>
                <div className={`border rounded-xl p-3 text-center ${st.badge}`}>
                  <p className={`text-xs font-bold ${st.text}`}>{stageInfo?.label} / {stageInfo?.risk}</p>
                  {h.dialysisRequired && (
                    <p className={`text-[10px] mt-0.5 ${st.text} opacity-80`}>🔴 투석 필요</p>
                  )}
                </div>
              </div>

              {/* 단계별 확률 */}
              {h.probabilities && (
                <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">단계별 확률</p>
                  <div className="space-y-2">
                    {Object.entries(h.probabilities)
                      .sort(([, a], [, b]) => b - a)
                      .map(([stage, prob]) => {
                        const ss   = STAGE_STYLE[stage] || STAGE_STYLE['Stage3']
                        const pct  = (prob * 100).toFixed(1)
                        const info = CKD_STAGES.find(c => c.key === stage)
                        return (
                          <div key={stage}>
                            <div className="flex justify-between text-[10px] mb-0.5">
                              <span className="text-slate-400">{info?.label || stage}</span>
                              <span className={`font-bold ${ss.text}`}>{pct}%</span>
                            </div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${ss.bar}`} style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        )
                      })
                    }
                  </div>
                </div>
              )}

              {/* eGFR 추세 */}
              {(() => {
                const slope = calcSlope(history)
                const trend = getTrendInfo(slope)
                return (
                  <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">eGFR 추세</p>
                    {history.filter(h => parseFloat(h.egfr) > 0).length < 2 ? (
                      <p className="text-[11px] text-slate-600 text-center py-3">
                        진단 기록이 2회 이상 저장되면<br />추세가 표시됩니다
                      </p>
                    ) : (
                      <div className="space-y-3">
                        <EgfrSparkline history={history} />
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] px-2 py-1 rounded border font-bold ${trend.bg} ${trend.color}`}>
                            {trend.label}
                          </span>
                          <span className={`text-xs font-bold ${trend.color}`}>
                            월 {slope >= 0 ? '+' : ''}{slope.toFixed(1)} mL/min
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>
          </div>
        </div>
      </div>

    )
  }

  return null
}

import { useState } from 'react'
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
  { key: 'sc',   label: '크레아티닌', unit: 'mg/dL',  normal: '0.7~1.2', min: 0.7, max: 1.2,  placeholder: '예: 4.20' },
  { key: 'egfr', label: 'GFR',       unit: 'mL/min', normal: '≥ 90',    min: 90,  max: 9999, placeholder: '예: 18.0' },
  { key: 'bu',   label: 'BUN',       unit: 'mg/dL',  normal: '7~20',    min: 7,   max: 20,   placeholder: '예: 45.0' },
  { key: 'pot',  label: '칼륨',      unit: 'mEq/L',  normal: '3.5~5.0', min: 3.5, max: 5.0,  placeholder: '예: 5.80' },
  { key: 'al',   label: '알부민',    unit: 'g/dL',   normal: '3.5~5.0', min: 3.5, max: 5.0,  placeholder: '예: 3.8'  },
]

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

  const [screen, setScreen]   = useState('input')
  const [form, setForm]       = useState({ sc: '', egfr: '', bu: '', pot: '', al: '', htn: false, dm: false, pe: false, query: '' })
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const [saving, setSaving]   = useState(false)
  const [saved, setSaved]     = useState(false)

  const previewStage = getGfrStage(form.egfr)

  const handleSubmit = async () => {
    setError(null)
    setScreen('loading')
    try {
      const { data } = await axios.post(`${AI_URL}/ai/kidney/diagnose`, {
        sc:    form.sc   ? parseFloat(form.sc)   : null,
        egfr:  form.egfr ? parseFloat(form.egfr) : null,
        bu:    form.bu   ? parseFloat(form.bu)   : null,
        pot:   form.pot  ? parseFloat(form.pot)  : null,
        al:    form.al   ? parseFloat(form.al)   : null,
        htn:   form.htn  ? 'yes' : 'no',
        dm:    form.dm   ? 'yes' : 'no',
        pe:    form.pe   ? 'yes' : 'no',
        query: form.query || null,
      })
      setResult(data)
      setScreen('result')
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'AI 서버 연결 실패')
      setScreen('input')
    }
  }

  const handleSave = async () => {
    if (!result || saving || saved) return
    setSaving(true)
    try {
      await axios.post(`/api/patients/${patientId}/diagnoses/kidney`, {
        result:           result.prediction,
        confidence:       result.confidence,
        description:      result.description,
        severity:         result.severity,
        dialysisRequired: result.dialysis_required,
        probabilities:    result.probabilities,
      })
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

            {/* 신장 기능 수치 */}
            <div className="bg-[#151921] border border-slate-800 rounded-2xl p-6">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-5">신장 기능 수치</p>
              <div className="grid grid-cols-2 gap-4">
                {FIELDS.map(f => {
                  const warn = form[f.key] !== '' && isOutOfRange(form[f.key], f.min, f.max)
                  return (
                    <div key={f.key} className={f.key === 'al' ? 'col-span-2' : ''}>
                      <div className="flex justify-between items-center mb-1.5">
                        <label className="text-xs font-semibold text-slate-300">{f.label}</label>
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
          </div>

          {/* 오른쪽 1/3 — CKD 단계 미리보기 */}
          <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5 self-start sticky top-4">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">CKD 단계 미리보기</p>
            {previewStage
              ? <CKDStepList activeKey={previewStage} />
              : (
                <div className="text-center py-8">
                  <p className="text-slate-600 text-xs">GFR 값을 입력하면<br />단계를 미리 확인할 수 있습니다</p>
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
                onClick={handleSave}
                disabled={saving || saved}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${saved ? 'bg-green-600 text-white cursor-default' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
                style={{ boxShadow: '0 0 15px rgba(37,99,235,0.2)' }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                {saved ? '저장 완료' : saving ? '저장 중...' : 'DB에 저장'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-5">
            {/* 왼쪽 2/3 */}
            <div className="col-span-2 space-y-5">

              {/* 입력 수치 요약 */}
              <div className="bg-[#151921] border border-slate-800 rounded-2xl p-5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">입력 수치 요약</p>
                <div className="grid grid-cols-5 gap-3">
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
                <div className="bg-[#0d1117] rounded-xl p-4 text-sm text-slate-300 leading-relaxed border border-slate-800">
                  {result.rag_answer}
                </div>
                <p className="text-[10px] text-slate-600 mt-3">{result.description}</p>
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
      </div>
    )
  }

  return null
}

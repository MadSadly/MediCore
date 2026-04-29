// =====================================================================
// 담당자: MS (김민수) - 피부질환 분류
// =====================================================================

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

const TRIAGE_META = {
  RED:    { cls: 'text-red-400 bg-red-500/10 border-red-500/20',         bar: 'from-red-600 to-rose-400' },
  YELLOW: { cls: 'text-amber-400 bg-amber-500/10 border-amber-500/20',   bar: 'from-amber-600 to-yellow-400' },
  GREEN:  { cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', bar: 'from-emerald-600 to-green-400' },
}

export default function SkinDiseasePage() {
  const { id } = useParams()

  const [file, setFile]               = useState(null)
  const [preview, setPreview]         = useState(null)
  const [dragOver, setDragOver]       = useState(false)
  const [analyzing, setAnalyzing]     = useState(false)
  const [result, setResult]           = useState(null)
  const [error, setError]             = useState(null)
  const [saving, setSaving]           = useState(false)
  const [saved, setSaved]             = useState(false)
  const [diagnoses, setDiagnoses]     = useState([])
  const [loadingHist, setLoadingHist] = useState(true)
  const [modalDiagnosis, setModalDiagnosis] = useState(null)

  const fileInputRef = useRef(null)
  const token = localStorage.getItem('token')
  const authHeaders = { Authorization: `Bearer ${token}` }

  // 이 환자의 피부질환 진단 이력 로드
  useEffect(() => {
    const tok = localStorage.getItem('token')
    axios.get(`/api/patients/${id}/diagnoses`, { headers: { Authorization: `Bearer ${tok}` } })
      .then(res => setDiagnoses(res.data.filter(d => d.diseaseType === 'skin-disease')))
      .catch(() => { /* ignore */ })
      .finally(() => setLoadingHist(false))
  }, [id])

  const applyFile = useCallback((f) => {
    if (!f) return
    if (!['image/jpeg', 'image/png'].includes(f.type)) {
      setError('JPG 또는 PNG 파일만 업로드 가능합니다.')
      return
    }
    if (f.size > 5 * 1024 * 1024) {
      setError('파일 크기가 5MB를 초과합니다.')
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setSaved(false)
    setError(null)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    applyFile(e.dataTransfer.files[0])
  }, [applyFile])

  const analyze = async () => {
    if (!file) return
    setAnalyzing(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('image', file)
      form.append('patient_id', id)
      const res = await axios.post('/ai/skin/diagnose', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (!res.data.success) {
        setError(res.data.error || '이미지 품질 불량 또는 분석 실패')
      } else {
        setResult(res.data)
      }
    } catch {
      setError('AI 서버 연결에 실패했습니다. 서버 상태를 확인하세요.')
    } finally {
      setAnalyzing(false)
    }
  }

  const saveResult = async () => {
    if (!result || saved) return
    setSaving(true)
    try {
      const recommendLine = result.report
        .split('\n')
        .find(l => l.trim().startsWith('권고사항') || l.includes('권장'))
      const diagnosis = {
        diseaseType: 'skin-disease',
        title:       `${result.disease_ko} (${result.disease_en})`,
        summary:     `신뢰도 ${result.confidence.toFixed(1)}% | ${recommendLine?.replace(/^\s*\[?권고사항\]?\s*/, '').trim() || '전문의 상담 권장'}`,
        resultJson:  JSON.stringify(result),
        createdBy:   'Dr. Kim Minsu (MS)',
        createdAt:   new Date().toISOString().slice(0, 19),
      }
      await axios.post(`/api/patients/${id}/diagnoses`, diagnosis, { headers: authHeaders })
      setSaved(true)
      const hRes = await axios.get(`/api/patients/${id}/diagnoses`, { headers: authHeaders })
      setDiagnoses(hRes.data.filter(d => d.diseaseType === 'skin-disease'))
    } catch {
      setError('결과 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setSaved(false)
  }

  // ──────────────────────────────── RENDER ────────────────────────────────

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* 페이지 헤더 */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-100 tracking-tight">
            피부질환 분류 분석
          </h2>
          <p className="text-slate-500 mt-1 text-sm">
            AI 기반 피부 병변 감지 및 악성 가능성 정밀 분석 · 담당: 김민수 (MS)
          </p>
        </div>
        {result && (
          saved
            ? <span className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold rounded-xl text-sm">✓ 저장 완료</span>
            : <button
                onClick={saveResult}
                disabled={saving}
                className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-bold rounded-xl text-sm transition-colors flex items-center gap-2"
              >
                {saving ? '저장 중...' : '📋 진단 저장'}
              </button>
        )}
      </div>

      {/* ──── 업로드 섹션 (결과가 없을 때만) ──── */}
      {!result && (
        <section className="glass-card rounded-2xl p-6 border border-slate-700/50">
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => !file && fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl transition-colors
              ${dragOver
                ? 'border-rose-500 bg-rose-500/5'
                : 'border-slate-600 hover:border-rose-500/50 hover:bg-slate-800/30'}
              ${!file ? 'cursor-pointer' : ''}`}
          >
            {preview ? (
              /* 파일 선택 후: 미리보기 + 분석 버튼 */
              <div className="flex flex-col md:flex-row gap-6 p-6 items-center">
                <div className="relative w-44 h-44 flex-shrink-0">
                  <img
                    src={preview}
                    alt="업로드 이미지"
                    className="w-full h-full object-cover rounded-xl border border-slate-700"
                  />
                  <button
                    onClick={(e) => { e.stopPropagation(); reset() }}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-slate-700 hover:bg-slate-600 rounded-full text-slate-300 text-xs font-bold transition-colors flex items-center justify-center"
                  >✕</button>
                </div>
                <div className="flex-1 text-center md:text-left">
                  <p className="text-slate-200 font-semibold mb-1 truncate max-w-xs">{file.name}</p>
                  <p className="text-slate-500 text-sm mb-6">{(file.size / 1024).toFixed(1)} KB</p>
                  <button
                    onClick={(e) => { e.stopPropagation(); analyze() }}
                    disabled={analyzing}
                    className="px-8 py-3 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 disabled:opacity-60 text-white font-bold rounded-xl transition-all shadow-lg flex items-center gap-2 mx-auto md:mx-0"
                  >
                    {analyzing ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        AI 분석 중...
                      </>
                    ) : '🔬 AI 분석 시작'}
                  </button>
                </div>
              </div>
            ) : (
              /* 파일 미선택: 드래그 앤 드롭 안내 */
              <div className="flex flex-col items-center justify-center py-16 px-4">
                <div className="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mb-4">
                  <span className="text-3xl">🖼️</span>
                </div>
                <h3 className="text-lg font-bold text-slate-200 mb-2">피부 이미지 업로드</h3>
                <p className="text-slate-500 text-sm text-center max-w-sm mb-6">
                  병변이 선명하게 촬영된 이미지를 드래그하거나 클릭하여 선택하세요
                </p>
                <button
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}
                  className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold rounded-xl transition-colors text-sm"
                >
                  파일 선택
                </button>
                <p className="text-xs text-slate-600 mt-3">JPG, PNG · 최대 5MB</p>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={e => applyFile(e.target.files[0])}
          />
          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              ⚠️ {error}
            </div>
          )}
        </section>
      )}

      {/* ──── 분석 결과 섹션 ──── */}
      {result && (
        <>
          {/* 진단 결과 + Grad-CAM */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* 왼쪽: 진단 결과 카드 */}
            <div className="glass-card rounded-2xl p-6 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-5">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">AI 진단 결과</h3>
              </div>
              <div className="flex gap-5 mb-6">
                <div className="w-36 h-36 rounded-xl overflow-hidden flex-shrink-0 border border-slate-700">
                  <img src={preview} alt="분석 이미지" className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 min-w-0">
                  {(() => {
                    const meta = TRIAGE_META[result.triage_level] || TRIAGE_META.GREEN
                    return (
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border mb-3 ${meta.cls}`}>
                        {result.triage_label || '🟢 일반'}
                      </span>
                    )
                  })()}
                  <h4 className="text-xl font-black text-slate-50 leading-tight">{result.disease_ko}</h4>
                  <p className="text-sm text-slate-400 mt-1">{result.disease_en}</p>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">신뢰도</span>
                  <span className={`text-2xl font-black ${(TRIAGE_META[result.triage_level] || TRIAGE_META.GREEN).cls.split(' ')[0]}`}>
                    {result.confidence.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r transition-all duration-700 ${(TRIAGE_META[result.triage_level] || TRIAGE_META.GREEN).bar}`}
                    style={{ width: `${result.confidence}%` }}
                  />
                </div>
              </div>
            </div>

            {/* 오른쪽: 원본 vs Grad-CAM 비교 */}
            <div className="glass-card rounded-2xl p-6 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-5">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">원본 · Grad-CAM 비교</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                {/* 원본 이미지 */}
                <div>
                  <p className="text-[10px] text-slate-500 text-center mb-1.5 font-semibold uppercase tracking-wider">원본</p>
                  {result.original_b64 ? (
                    <div className="rounded-xl overflow-hidden border border-slate-700">
                      <img
                        src={`data:image/png;base64,${result.original_b64}`}
                        alt="원본 이미지"
                        className="w-full h-44 object-cover"
                      />
                    </div>
                  ) : (
                    <div className="rounded-xl overflow-hidden border border-slate-700">
                      <img
                        src={preview}
                        alt="원본 이미지"
                        className="w-full h-44 object-cover"
                      />
                    </div>
                  )}
                </div>
                {/* Grad-CAM 히트맵 */}
                <div>
                  <p className="text-[10px] text-slate-500 text-center mb-1.5 font-semibold uppercase tracking-wider">Grad-CAM</p>
                  {result.gradcam_b64 ? (
                    <div className="rounded-xl overflow-hidden border border-amber-700/40">
                      <img
                        src={`data:image/png;base64,${result.gradcam_b64}`}
                        alt="Grad-CAM 히트맵"
                        className="w-full h-44 object-cover"
                      />
                    </div>
                  ) : (
                    <div className="rounded-xl bg-slate-800/50 border border-slate-700 h-44 flex items-center justify-center">
                      <p className="text-slate-600 text-xs text-center px-2">Grad-CAM<br/>이미지 없음</p>
                    </div>
                  )}
                </div>
              </div>
              <p className="text-xs text-slate-500 text-center">빨간색/주황색 영역 = AI가 집중한 병변 부위</p>
            </div>
          </div>

          {/* Gemini Vision 판단 근거 */}
          {result.gradcam_explanation && (
            <div className="glass-card rounded-2xl p-6 border border-amber-500/20">
              <div className="flex items-center gap-2 mb-4">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">AI 판단 근거 (Gemini Vision 분석)</h3>
              </div>
              <div className="flex gap-3">
                <span className="text-amber-400 text-lg flex-shrink-0">🔍</span>
                <p className="text-sm text-slate-300 leading-relaxed">{result.gradcam_explanation}</p>
              </div>
            </div>
          )}

          {/* Top 3 감별진단 + 임상 참고 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* 감별 진단 Top 3 */}
            <div className="glass-card rounded-2xl p-6 border border-slate-700/50">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-5">
                감별 진단 Top 3
              </h3>
              <div className="space-y-4">
                {result.top3?.map((c, i) => (
                  <div key={i}>
                    <div className="flex justify-between items-center mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className={`w-5 h-5 rounded-full text-[10px] font-black flex items-center justify-center ${i === 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-700 text-slate-400'}`}>
                          {i + 1}
                        </span>
                        <span className={`text-sm font-semibold ${i === 0 ? 'text-slate-100' : 'text-slate-400'}`}>
                          {c.disease_ko}
                        </span>
                      </div>
                      <span className={`text-sm font-bold ${i === 0 ? 'text-rose-400' : 'text-slate-500'}`}>
                        {c.confidence.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${i === 0 ? 'bg-gradient-to-r from-rose-600 to-pink-400' : 'bg-slate-600'}`}
                        style={{ width: `${c.confidence}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 임상 참고 사항 + 버튼 */}
            <div className="glass-card rounded-2xl p-6 border border-slate-700/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-amber-400">⚕️</span>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">임상 참고 사항</h3>
                </div>
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                  <div className="flex gap-3">
                    <span className="text-amber-400 text-lg flex-shrink-0">⚠️</span>
                    <p className="text-sm text-amber-200/80 leading-relaxed">
                      본 AI 분석 결과는 진단 보조 도구입니다. 최종 진단을 위해서는 피부과 전문의와의
                      정밀 대면 상담 및 조직 검사가 반드시 필요합니다.
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-6">
                <button
                  onClick={reset}
                  className="py-3 bg-slate-700/50 hover:bg-slate-700 border border-slate-600/50 text-slate-300 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2"
                >
                  🔄 새 분석
                </button>
                <button
                  onClick={saveResult}
                  disabled={saving || saved}
                  className={`py-3 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2
                    ${saved
                      ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 cursor-default'
                      : 'bg-rose-600/80 hover:bg-rose-600 text-white disabled:opacity-50'}`}
                >
                  {saved ? '✓ 저장됨' : saving ? '저장 중...' : '📋 결과 저장'}
                </button>
              </div>
            </div>
          </div>

          {/* AI 진단 리포트 */}
          <div className="glass-card rounded-2xl p-6 border border-slate-700/50">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">
              AI 진단 리포트
            </h3>
            <pre className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap font-mono bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 overflow-x-auto">
              {result.report}
            </pre>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              ⚠️ {error}
            </div>
          )}
        </>
      )}

      {/* ──── 진단 이력 상세 모달 ──── */}
      {modalDiagnosis && (() => {
        let r = {}
        try { r = JSON.parse(modalDiagnosis.resultJson || '{}') } catch { void 0; }
        const meta = TRIAGE_META[r.triage_level] || TRIAGE_META.GREEN
        return (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
            onClick={() => setModalDiagnosis(null)}
          >
            <div
              className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-slate-800/50 [&::-webkit-scrollbar-thumb]:bg-slate-600 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb:hover]:bg-slate-500"
              onClick={e => e.stopPropagation()}
            >
              {/* 모달 헤더 */}
              <div className="sticky top-0 bg-slate-900/95 backdrop-blur border-b border-slate-700 px-6 py-4 flex items-center justify-between z-10">
                <div>
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border mb-1 ${meta.cls}`}>
                    {r.triage_label || '🟢 일반'}
                  </span>
                  <h3 className="text-lg font-black text-slate-100">{modalDiagnosis.title}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {modalDiagnosis.createdBy} · {new Date(modalDiagnosis.createdAt).toLocaleString('ko-KR')}
                  </p>
                </div>
                <button
                  onClick={() => setModalDiagnosis(null)}
                  className="w-8 h-8 rounded-full bg-slate-700 hover:bg-slate-600 text-slate-300 flex items-center justify-center text-sm transition-colors flex-shrink-0"
                >✕</button>
              </div>

              <div className="p-6 space-y-6">
                {/* 신뢰도 */}
                {r.confidence != null && (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">신뢰도</span>
                      <span className={`text-xl font-black ${meta.cls.split(' ')[0]}`}>{r.confidence.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full bg-gradient-to-r ${meta.bar}`} style={{ width: `${r.confidence}%` }} />
                    </div>
                  </div>
                )}

                {/* 원본 vs GradCAM */}
                {(r.original_b64 || r.gradcam_b64) && (
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">원본 · Grad-CAM</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-[10px] text-slate-500 text-center mb-1.5 font-semibold uppercase tracking-wider">원본</p>
                        {r.original_b64
                          ? <img src={`data:image/png;base64,${r.original_b64}`} alt="원본" className="w-full h-48 object-cover rounded-xl border border-slate-700" />
                          : <div className="h-48 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center"><p className="text-slate-600 text-xs">이미지 없음</p></div>
                        }
                      </div>
                      <div>
                        <p className="text-[10px] text-slate-500 text-center mb-1.5 font-semibold uppercase tracking-wider">Grad-CAM</p>
                        {r.gradcam_b64
                          ? <img src={`data:image/png;base64,${r.gradcam_b64}`} alt="GradCAM" className="w-full h-48 object-cover rounded-xl border border-amber-700/40" />
                          : <div className="h-48 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center"><p className="text-slate-600 text-xs">이미지 없음</p></div>
                        }
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 text-center mt-2">빨간색/주황색 영역 = AI가 집중한 병변 부위</p>
                  </div>
                )}

                {/* AI 판단 근거 */}
                {r.gradcam_explanation && (
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 flex gap-3">
                    <span className="text-amber-400 text-lg flex-shrink-0">🔍</span>
                    <p className="text-sm text-slate-300 leading-relaxed">{r.gradcam_explanation}</p>
                  </div>
                )}

                {/* Top 3 */}
                {r.top3?.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">감별 진단 Top 3</p>
                    <div className="space-y-3">
                      {r.top3.map((c, i) => (
                        <div key={i}>
                          <div className="flex justify-between items-center mb-1">
                            <div className="flex items-center gap-2">
                              <span className={`w-5 h-5 rounded-full text-[10px] font-black flex items-center justify-center ${i === 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-700 text-slate-400'}`}>{i + 1}</span>
                              <span className={`text-sm font-semibold ${i === 0 ? 'text-slate-100' : 'text-slate-400'}`}>{c.disease_ko}</span>
                            </div>
                            <span className={`text-sm font-bold ${i === 0 ? 'text-rose-400' : 'text-slate-500'}`}>{c.confidence.toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${i === 0 ? 'bg-gradient-to-r from-rose-600 to-pink-400' : 'bg-slate-600'}`} style={{ width: `${c.confidence}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI 리포트 */}
                {r.report && (
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">AI 진단 리포트</p>
                    <pre className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap font-mono bg-slate-950/60 rounded-xl p-4 border border-slate-700/50 overflow-x-auto">
                      {r.report}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })()}

      {/* ──── 분석 이력 테이블 ──── */}
      <section className="glass-card rounded-2xl p-6 border border-slate-700/50">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <span className="text-rose-400">📋</span> 피부질환 분석 기록
          </h3>
          <span className="text-xs text-slate-500">{diagnoses.length}건</span>
        </div>

        {loadingHist ? (
          <div className="text-center py-8">
            <div className="w-6 h-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : diagnoses.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-3xl mb-3">📭</p>
            <p className="text-slate-400 font-semibold">아직 분석 기록이 없습니다</p>
            <p className="text-slate-600 text-sm mt-1">위에서 이미지를 업로드해 첫 번째 분석을 시작하세요.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 text-slate-500 text-xs uppercase tracking-widest">
                  <th className="pb-3 px-3">진단명</th>
                  <th className="pb-3 px-3">요약</th>
                  <th className="pb-3 px-3">진단의</th>
                  <th className="pb-3 px-3">날짜</th>
                  <th className="pb-3 px-3 text-right">상태</th>
                </tr>
              </thead>
              <tbody>
                {diagnoses.map(d => (
                  <tr
                    key={d.id}
                    onClick={() => setModalDiagnosis(d)}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-3 font-semibold text-slate-200">{d.title}</td>
                    <td className="py-3 px-3 text-slate-400 max-w-xs truncate">{d.summary}</td>
                    <td className="py-3 px-3 text-slate-500 text-xs">{d.createdBy || '-'}</td>
                    <td className="py-3 px-3 text-slate-500 text-xs whitespace-nowrap">
                      {new Date(d.createdAt).toLocaleDateString('ko-KR')}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2.5 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-[10px] font-bold uppercase">
                        상세보기
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Niivue } from '@niivue/niivue'
import axios from 'axios'

const AI_URL = import.meta.env.VITE_AI_URL || 'http://localhost:8000'

const SLICE_TYPES = [
  { label: '3D', value: 'render' },
  { label: 'Axial', value: 'axial' },
  { label: 'Sagittal', value: 'sagittal' },
  { label: 'Coronal', value: 'coronal' },
  { label: '멀티뷰', value: 'multiplanar' },
]

// niivue sliceType 매핑
const SLICE_TYPE_MAP = {
  render: 4,
  axial: 0,
  sagittal: 1,
  coronal: 2,
  multiplanar: 3,
}

const CONFIDENCE_COLOR = (conf) => {
  if (conf >= 0.95) return 'text-green-400'
  if (conf >= 0.85) return 'text-yellow-400'
  return 'text-red-400'
}

const SAFETY_COLOR = {
  low: 'bg-green-500/10 border-green-500/30 text-green-400',
  moderate: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
  high_uncertainty: 'bg-red-500/10 border-red-500/30 text-red-400',
}

export default function BrainTumorPage() {
  const { id: patientId } = useParams()
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const fileRef = useRef(null)

  const [file, setFile] = useState(null)
  const [skullStrip, setSkullStrip] = useState(false)
  const [sliceType, setSliceType] = useState('multiplanar')
  const [viewerReady, setViewerReady] = useState(false)

  const [status, setStatus] = useState('idle') // idle | uploading | done | error
  const [result, setResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  // niivue 초기화
  useEffect(() => {
    if (!canvasRef.current) return
    const nv = new Niivue({
      backColor: [0.07, 0.09, 0.13, 1],
      show3Dcrosshair: true,
      isColorbar: false,
      isOrientCube: true,
    })
    nv.attachToCanvas(canvasRef.current)
    nvRef.current = nv
  }, [])

  // 뷰어 슬라이스 타입 변경
  useEffect(() => {
    if (!nvRef.current || !viewerReady) return
    nvRef.current.setSliceType(SLICE_TYPE_MAP[sliceType])
  }, [sliceType, viewerReady])

  const loadFileToViewer = useCallback(async (f) => {
    if (!nvRef.current) return
    const url = URL.createObjectURL(f)
    await nvRef.current.loadVolumes([{ url, name: f.name }])
    nvRef.current.setSliceType(SLICE_TYPE_MAP[sliceType])
    setViewerReady(true)
  }, [sliceType])

  const handleFileChange = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setResult(null)
    setErrorMsg('')
    setStatus('idle')
    await loadFileToViewer(f)
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (!f) return
    setFile(f)
    setResult(null)
    setErrorMsg('')
    setStatus('idle')
    await loadFileToViewer(f)
  }

  const handleDiagnose = async () => {
    if (!file) return
    setStatus('uploading')
    setErrorMsg('')
    try {
      const form = new FormData()
      form.append('file', file)
      const token = localStorage.getItem('token')
      const res = await axios.post(
        `${AI_URL}/ai/brain/diagnose?skull_strip=${skullStrip}`,
        form,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        }
      )
      setResult(res.data)
      setStatus('done')
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || '진단 중 오류가 발생했습니다.')
      setStatus('error')
    }
  }

  const clf = result?.classification
  const safety = result?.safety
  const report = result?.report
  const refs = result?.references || []

  return (
    <div className="space-y-5">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">뇌종양 진단</h1>
          <p className="text-xs text-slate-500 mt-0.5">3D DenseNet121 · RAG · Gemini 리포트</p>
        </div>
        {result && (
          <span className="text-xs text-slate-500 font-mono">
            처리시간 {result.metadata?.processing_time_ms}ms
          </span>
        )}
      </div>

      {/* 메인 2열: 업로드 + 뷰어 */}
      <div className="grid grid-cols-[280px_1fr] gap-4 items-start">
        {/* 업로드 패널 */}
        <div className="space-y-3">
          {/* 드래그앤드롭 영역 */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-blue-500/50 rounded-xl p-5 text-center cursor-pointer transition-colors bg-slate-900/40"
          >
            <p className="text-3xl mb-2">🧠</p>
            {file ? (
              <>
                <p className="text-xs font-semibold text-blue-400 truncate">{file.name}</p>
                <p className="text-[10px] text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
              </>
            ) : (
              <>
                <p className="text-xs text-slate-400 font-semibold">NIfTI 파일 업로드</p>
                <p className="text-[10px] text-slate-600 mt-1">.nii / .nii.gz</p>
              </>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".nii,.nii.gz"
            className="hidden"
            onChange={handleFileChange}
          />

          {/* Skull Strip 토글 */}
          <label className="flex items-center justify-between px-3 py-2.5 bg-slate-900/60 border border-slate-800 rounded-lg cursor-pointer">
            <div>
              <p className="text-xs font-semibold text-slate-300">Skull Stripping</p>
              <p className="text-[10px] text-slate-500">raw MRI 입력 시 활성화</p>
            </div>
            <div
              onClick={() => setSkullStrip(v => !v)}
              className={`w-10 h-5 rounded-full transition-colors relative ${skullStrip ? 'bg-blue-600' : 'bg-slate-700'}`}
            >
              <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${skullStrip ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </div>
          </label>

          {/* 진단 버튼 */}
          <button
            onClick={handleDiagnose}
            disabled={!file || status === 'uploading'}
            className="w-full py-2.5 rounded-xl font-semibold text-sm transition-all
              bg-blue-600 hover:bg-blue-500 text-white
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {status === 'uploading' ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                분석 중...
              </span>
            ) : '진단 시작'}
          </button>

          {errorMsg && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {errorMsg}
            </p>
          )}

          {/* 뷰 전환 버튼 */}
          {viewerReady && (
            <div className="space-y-1">
              <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider px-1">뷰어 모드</p>
              <div className="grid grid-cols-3 gap-1">
                {SLICE_TYPES.map(({ label, value }) => (
                  <button
                    key={value}
                    onClick={() => setSliceType(value)}
                    className={`py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      sliceType === value
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* MRI 뷰어 */}
        <div className="bg-[#070a10] rounded-xl overflow-hidden border border-slate-800" style={{ height: '420px' }}>
          {!viewerReady && (
            <div className="h-full flex items-center justify-center">
              <p className="text-slate-600 text-sm">NIfTI 파일을 업로드하면 여기에 표시됩니다</p>
            </div>
          )}
          <canvas
            ref={canvasRef}
            style={{ width: '100%', height: '100%', display: viewerReady ? 'block' : 'none' }}
          />
        </div>
      </div>

      {/* 진단 결과 */}
      {status === 'done' && clf && (
        <div className="grid grid-cols-3 gap-3">
          {/* 판정 */}
          <div className={`rounded-xl border p-4 ${clf.prediction === 'Tumor' ? 'bg-red-500/10 border-red-500/30' : 'bg-green-500/10 border-green-500/30'}`}>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">판정</p>
            <p className={`text-2xl font-bold ${clf.prediction === 'Tumor' ? 'text-red-400' : 'text-green-400'}`}>
              {clf.prediction === 'Tumor' ? '종양 의심' : '정상'}
            </p>
            <p className="text-[10px] text-slate-500 mt-1">{clf.prediction}</p>
          </div>

          {/* 확신도 */}
          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">확신도</p>
            <p className={`text-2xl font-bold ${CONFIDENCE_COLOR(clf.confidence)}`}>
              {(clf.confidence * 100).toFixed(1)}%
            </p>
            <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${clf.confidence >= 0.95 ? 'bg-green-500' : clf.confidence >= 0.85 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${clf.confidence * 100}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[9px] text-slate-600">종양 {(clf.tumor_probability * 100).toFixed(1)}%</span>
              <span className="text-[9px] text-slate-600">정상 {(clf.normal_probability * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* 안전 등급 */}
          {safety && (
            <div className={`rounded-xl border p-4 ${SAFETY_COLOR[safety.risk_level] || SAFETY_COLOR.low}`}>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">안전 등급</p>
              <p className="text-lg font-bold capitalize">{safety.risk_level.replace('_', ' ')}</p>
              <p className="text-[10px] mt-1 opacity-80">{safety.clinical_action}</p>
              {safety.requires_specialist_review && (
                <span className="inline-block mt-2 text-[9px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
                  전문의 검토 필요
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* LLM 리포트 */}
      {report && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
            AI 소견 리포트
          </h2>

          {report.summary && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">요약</p>
              <p className="text-sm text-slate-300 leading-relaxed">{report.summary}</p>
            </div>
          )}

          {report.findings?.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">주요 소견</p>
              <ul className="space-y-1">
                {report.findings.map((f, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-300">
                    <span className="text-blue-500 mt-0.5">·</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {report.recommendations?.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">권고사항</p>
              <ul className="space-y-1">
                {report.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-300">
                    <span className="text-green-500 mt-0.5">→</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {report.differential_diagnosis?.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">감별 진단</p>
              <div className="flex flex-wrap gap-2">
                {report.differential_diagnosis.map((d, i) => (
                  <span key={i} className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full border border-slate-700">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RAG 참고 문헌 */}
      {refs.length > 0 && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
          <h2 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-purple-500 rounded-full" />
            참고 문헌 ({refs.length}건)
          </h2>
          <div className="space-y-2">
            {refs.map((ref, i) => (
              <div key={i} className="flex gap-3 text-xs">
                <span className="text-slate-600 font-mono w-4 flex-shrink-0">{i + 1}</span>
                <div className="min-w-0">
                  <p className="text-slate-400 truncate">{ref.source}</p>
                  <p className="text-slate-600 mt-0.5 line-clamp-2">{ref.content?.slice(0, 120)}...</p>
                </div>
                <span className="flex-shrink-0 text-purple-400 text-[10px] font-mono">
                  {(ref.score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 면책 */}
      {result?.disclaimer && (
        <p className="text-[10px] text-slate-600 border-t border-slate-800 pt-3 leading-relaxed">
          ⚠ {result.disclaimer}
        </p>
      )}
    </div>
  )
}

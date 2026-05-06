import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Niivue } from '@niivue/niivue'
import axios from 'axios'

const AI_URL = import.meta.env.VITE_AI_URL || ''
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

const C = {
  bg:     '#080808',
  panel:  '#121212',
  border: '#2a2a2a',
  text:   '#ececec',
  sub:    '#848484',
  dim:    '#464646',
  accent: '#c8c8c8',
  hover:  '#1a1a1a',
  red:    '#f87171',
  green:  '#34d399',
  yellow: '#fbbf24',
}

const confColor = (c) => c >= 0.95 ? C.green : c >= 0.85 ? C.yellow : C.red

const AXES = ['axial', 'coronal', 'sagittal']
const AXIS_ICONS = {
  axial:    '/WJ/axial.PNG',
  coronal:  '/WJ/coronal.PNG',
  sagittal: '/WJ/sagital.PNG',
}

let _sid = 0
const mkSess = (file, fileId) => ({
  key:               String(++_sid),
  fileId,
  file,
  fileName:          file.name,
  uploadedAt:        new Date(),
  viewMode:          '2d',
  axis:              null,
  sliceCount:        0,
  currentIndex:      0,
  axisCache:         {},
  highlightAxisCache: {},  // axis → highlight slice count (pre-generated at diagnosis)
  highlightOn:       false,
  maskReady:         false, // true when Tumor detected and mask files are ready
  status:            'idle',
  result:            null,
  errorMsg:          '',
})

const Btn = ({ children, onClick, disabled, primary, style: s }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      width: '100%', padding: '9px 12px', borderRadius: 6,
      fontSize: 13, fontWeight: 600, cursor: disabled ? 'not-allowed' : 'pointer',
      background: disabled ? C.bg : primary ? '#d4d4d4' : C.hover,
      border: `1px solid ${disabled ? C.border : primary ? '#d4d4d4' : '#363636'}`,
      color: disabled ? C.dim : primary ? '#080808' : C.text,
      transition: 'all 0.15s', textAlign: 'center', ...s,
    }}
  >
    {children}
  </button>
)

const Spinner = ({ size = 16 }) => (
  <span style={{
    width: size, height: size, flexShrink: 0,
    border: `${size > 20 ? 3 : 2}px solid ${C.dim}`,
    borderTopColor: C.accent, borderRadius: '50%',
    animation: 'wj-spin 0.7s linear infinite', display: 'inline-block',
  }} />
)

export default function BrainTumorPage() {
  const { id: patientId } = useParams()

  const nvCanvasRef  = useRef(null)
  const nvRef        = useRef(null)
  const fileInputRef = useRef(null)
  const sliceViewRef = useRef(null)
  const thumbListRef = useRef(null)
  const activeKeyRef = useRef(null)

  const [phase,       setPhase]       = useState('upload')
  const [sessions,    setSessions]    = useState([])
  const [activeKey,   setActiveKey]   = useState(null)
  const [thumbsOpen,  setThumbsOpen]  = useState(true)
  const [uploading,   setUploading]   = useState(false)
  const [dragOver,    setDragOver]    = useState(false)
  const [diagHistory, setDiagHistory] = useState([])

  useEffect(() => { activeKeyRef.current = activeKey }, [activeKey])

  // ── 진단 기록 조회 ──
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token || !patientId) return
    axios.get(`${BACKEND_URL}/api/patients/${patientId}/diagnoses`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(res => {
      const records = (res.data || []).filter(d => d.diseaseType === 'brain-tumor')
      setDiagHistory(records)
    }).catch(() => {})
  }, [patientId])

  const activeSess = sessions.find(s => s.key === activeKey) ?? null

  // ── Init Niivue (lazy — canvas must be display:block when called) ──
  const initNiivue = useCallback(() => {
    if (nvRef.current || !nvCanvasRef.current) return
    const nv = new Niivue({
      backColor: [0.05, 0.07, 0.09, 1],
      show3Dcrosshair: false,
      isColorbar: false,
      isOrientCube: false,
    })
    nv.attachToCanvas(nvCanvasRef.current)
    nvRef.current = nv
  }, [])

  // ── Wheel scroll ──
  useEffect(() => {
    const el = sliceViewRef.current
    if (!el) return
    const handler = (e) => {
      e.preventDefault()
      const key = activeKeyRef.current
      setSessions(prev => {
        const sess = prev.find(s => s.key === key)
        if (!sess || sess.viewMode === '3d') return prev
        const effCount = sess.highlightOn && sess.maskReady && sess.axis
          ? (sess.highlightAxisCache[sess.axis] || sess.sliceCount)
          : sess.sliceCount
        if (!effCount) return prev
        const next = Math.max(0, Math.min(effCount - 1, sess.currentIndex + (e.deltaY > 0 ? 1 : -1)))
        return prev.map(s => s.key === key ? { ...s, currentIndex: next } : s)
      })
    }
    el.addEventListener('wheel', handler, { passive: false })
    return () => el.removeEventListener('wheel', handler)
  }, [phase])

  // ── Auto-scroll thumbnail ──
  useEffect(() => {
    if (!thumbListRef.current || !activeSess) return
    const el = thumbListRef.current.querySelector(`[data-idx="${activeSess.currentIndex}"]`)
    if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }, [activeSess])

  const updateSess = useCallback((key, upd) =>
    setSessions(prev => prev.map(s => s.key === key ? { ...s, ...upd } : s)), [])

  // ── Upload ──
  const handleFile = async (file) => {
    if (!file) return
    const lower = file.name.toLowerCase()
    if (!lower.endsWith('.nii') && !lower.endsWith('.nii.gz')) {
      alert('.nii 또는 .nii.gz 파일만 지원합니다.')
      return
    }
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await axios.post(
        `${AI_URL}/ai/brain/upload`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      const sess = mkSess(file, res.data.fileId)
      setSessions(prev => [...prev, sess])
      setActiveKey(sess.key)
      setPhase('viewer')
    } catch (err) {
      alert('업로드 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
    }
  }

  // ── Normal slices ──
  const loadSlices = useCallback(async (key, fileId, axis) => {
    setSessions(prev => prev.map(s => s.key === key ? { ...s, status: 'loading-slices', axis } : s))
    try {
      const res = await axios.post(`${AI_URL}/ai/brain/slices`, { fileId, axis })
      const { sliceCount } = res.data
      setSessions(prev => prev.map(s => s.key === key ? {
        ...s,
        status: 'idle',
        axis,
        sliceCount,
        currentIndex: 0,
        axisCache: { ...s.axisCache, [axis]: sliceCount },
      } : s))
    } catch {
      setSessions(prev => prev.map(s => s.key === key
        ? { ...s, status: 'error', errorMsg: '슬라이스 생성에 실패했습니다.' }
        : s))
    }
  }, [])

  // ── Axis selection ──
  const handleAxis = (axis) => {
    if (!activeSess || activeSess.status === 'loading-slices') return

    // Highlight 모드: 서버에 슬라이스 pre-generated → 그냥 axis 변경
    if (activeSess.highlightOn && activeSess.maskReady) {
      updateSess(activeSess.key, { axis, currentIndex: 0 })
      return
    }

    if (activeSess.axis === axis && activeSess.sliceCount > 0) return
    if (activeSess.axisCache?.[axis]) {
      updateSess(activeSess.key, { axis, sliceCount: activeSess.axisCache[axis], currentIndex: 0 })
      return
    }
    loadSlices(activeSess.key, activeSess.fileId, axis)
  }

  // ── 3D (supports highlight) ──
  const handle3D = async (forceHighlight) => {
    if (!activeSess?.file) return
    const key = activeSess.key
    const useHL = forceHighlight !== undefined
      ? forceHighlight
      : (activeSess.highlightOn && activeSess.maskReady)

    let volumes
    if (useHL && activeSess.maskReady) {
      volumes = [
        {
          url: `${AI_URL}/ai/brain/preprocessed/${activeSess.fileId}/preprocessed.nii`,
          name: 'preprocessed.nii',
          colormap: 'gray',
          opacity: 1.0,
          cal_min: 0.001,
          cal_max: 1.0,
        },
        {
          url: `${AI_URL}/ai/brain/mask/${activeSess.fileId}/mask.nii`,
          name: 'mask.nii',
          colormap: 'hot',
          opacity: 0.6,
          cal_min: 0.5,
          cal_max: 1.0,
        },
      ]
    } else {
      const url = URL.createObjectURL(activeSess.file)
      volumes = [{ url, name: activeSess.file.name, colormap: 'gray', opacity: 1.0 }]
    }

    // 캔버스를 display:block으로 만들기 위해 먼저 3D 모드로 전환
    updateSess(key, { viewMode: '3d', errorMsg: '' })

    // React가 캔버스를 DOM에 그릴 때까지 대기
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))

    // 캔버스가 보이는 상태에서 Niivue 지연 초기화
    initNiivue()
    if (!nvRef.current) {
      updateSess(key, { viewMode: '2d', errorMsg: '3D 초기화에 실패했습니다.' })
      return
    }

    try {
      await nvRef.current.loadVolumes(volumes)
      nvRef.current.setSliceType(4)
    } catch (err) {
      console.error('3D 렌더링 오류:', err)
      updateSess(key, { viewMode: '2d', errorMsg: '3D 렌더링에 실패했습니다: ' + (err?.message || String(err)) })
    }
  }

  const handle2D = () => {
    if (!activeSess) return
    updateSess(activeSess.key, { viewMode: '2d' })
  }

  // ── Highlight toggle ──
  const toggleHighlight = async (on) => {
    if (!activeSess?.maskReady) return

    // highlight OFF → ON 시 axis가 없으면 아무것도 안 해도 됨 (이미지 없음)
    // highlight ON → OFF 시 해당 axis의 normal 슬라이스가 없으면 로드
    if (!on && activeSess.axis) {
      const cachedCount = activeSess.axisCache[activeSess.axis]
      if (!cachedCount) {
        updateSess(activeSess.key, { highlightOn: false, sliceCount: 0, currentIndex: 0 })
        loadSlices(activeSess.key, activeSess.fileId, activeSess.axis)
        return
      }
      updateSess(activeSess.key, { highlightOn: false, sliceCount: cachedCount, currentIndex: 0 })
    } else {
      updateSess(activeSess.key, { highlightOn: on, currentIndex: 0 })
    }

    // 3D 모드면 Niivue 재로드
    if (activeSess.viewMode === '3d' && nvRef.current) {
      await handle3D(on)
    }
  }

  // ── Tab management ──
  const switchTab = (key) => {
    if (key === activeKey) return
    setActiveKey(key)
  }

  const closeTab = (key, e) => {
    e.stopPropagation()
    setSessions(prev => {
      const remaining = prev.filter(s => s.key !== key)
      if (remaining.length === 0) {
        setPhase('upload')
        setActiveKey(null)
      } else if (key === activeKey) {
        setActiveKey(remaining[remaining.length - 1].key)
      }
      return remaining
    })
  }

  // ── Diagnosis ──
  const handleDiagnose = async () => {
    if (!activeSess || activeSess.status === 'loading-diagnose') return
    const key = activeSess.key
    updateSess(key, { status: 'loading-diagnose', errorMsg: '' })
    try {
      const form = new FormData()
      form.append('file', activeSess.file)
      form.append('fileId', activeSess.fileId)  // 마스크 저장 위치 전달
      const token = localStorage.getItem('token')
      const res = await axios.post(
        `${AI_URL}/ai/brain/diagnose`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data', ...(token ? { Authorization: `Bearer ${token}` } : {}) } },
      )

      const meta = res.data?.metadata || {}
      updateSess(key, {
        status: 'done',
        result: res.data,
        maskReady: meta.mask_ready === true,
        highlightAxisCache: meta.highlight_slice_counts || {},
      })

      const clf = res.data.classification
      if (clf && res.data.report) {
        const title = `${clf.prediction === 'Tumor' ? '종양 의심' : '정상'} - ${(clf.confidence * 100).toFixed(1)}%`
        try {
          const saved = await axios.post(
            `${BACKEND_URL}/api/patients/${patientId}/diagnoses`,
            { diseaseType: 'brain-tumor', title, summary: res.data.report.impression, resultJson: JSON.stringify(res.data) },
            { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } },
          )
          setDiagHistory(prev => [saved.data, ...prev])
        } catch { void 0; }
      }
    } catch (err) {
      updateSess(key, { status: 'error', errorMsg: err.response?.data?.detail || '진단 중 오류가 발생했습니다.' })
    }
  }

  // ════════════════════════════════
  // PHASE 1 — UPLOAD SCREEN
  // ════════════════════════════════
  if (phase === 'upload') {
    return (
      <div style={{ minHeight: '100vh', background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 480, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, padding: '40px 24px' }}>
          <h2 style={{ color: C.text, fontSize: 22, fontWeight: 700, margin: 0 }}>뇌종양 MRI 분석</h2>
          <p style={{ color: C.sub, fontSize: 14, margin: 0 }}>NIfTI 파일을 업로드하여 AI 진단을 시작합니다</p>

          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]) }}
            onClick={() => !uploading && fileInputRef.current?.click()}
            style={{
              width: '100%', padding: '48px 24px', borderRadius: 12, textAlign: 'center',
              cursor: uploading ? 'wait' : 'pointer',
              border: `2px dashed ${dragOver ? C.accent : C.border}`,
              background: dragOver ? '#0d2040' : C.panel,
              transition: 'all 0.2s',
            }}
          >
            {uploading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                <Spinner size={28} />
                <p style={{ color: C.sub, fontSize: 14 }}>업로드 중...</p>
              </div>
            ) : (
              <>
                <p style={{ color: dragOver ? C.accent : C.sub, fontSize: 14, marginBottom: 8 }}>
                  파일을 여기에 드래그하거나 클릭하여 선택하세요
                </p>
                <p style={{ color: C.dim, fontSize: 12 }}>.nii / .nii.gz</p>
              </>
            )}
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".nii,.nii.gz"
          style={{ display: 'none' }}
          onChange={e => { handleFile(e.target.files?.[0]); e.target.value = '' }}
        />
        <style>{`@keyframes wj-spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  // ════════════════════════════════
  // PHASE 2 — VIEWER SCREEN
  // ════════════════════════════════

  // 현재 유효 슬라이스 수 (하이라이트 ON이면 highlight count 사용)
  const useHighlight = activeSess?.highlightOn && activeSess?.maskReady
  const effSliceCount = useHighlight && activeSess?.axis
    ? (activeSess.highlightAxisCache[activeSess.axis] || activeSess.sliceCount)
    : (activeSess?.sliceCount || 0)

  const sliceUrl = activeSess?.axis && effSliceCount > 0
    ? useHighlight
      ? `${AI_URL}/ai/brain/highlight/${activeSess.fileId}/${activeSess.axis}/slice_${String(activeSess.currentIndex).padStart(3, '0')}.png`
      : `${AI_URL}/ai/brain/slices/${activeSess.fileId}/${activeSess.axis}/slice_${String(activeSess.currentIndex).padStart(3, '0')}.png`
    : null

  const thumbUrls = activeSess?.axis && effSliceCount > 0
    ? Array.from({ length: effSliceCount }, (_, i) =>
        useHighlight
          ? `${AI_URL}/ai/brain/highlight/${activeSess.fileId}/${activeSess.axis}/slice_${String(i).padStart(3, '0')}.png`
          : `${AI_URL}/ai/brain/slices/${activeSess.fileId}/${activeSess.axis}/slice_${String(i).padStart(3, '0')}.png`,
      )
    : []

  const clf    = activeSess?.result?.classification
  const safety = activeSess?.result?.safety
  const report = activeSess?.result?.report
  const refs   = activeSess?.result?.references || []

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%',
      overflowY: 'auto',
      background: C.bg, color: C.text,
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>

      {/* ════ TAB BAR ════ */}
      <div style={{
        display: 'flex', alignItems: 'stretch',
        background: C.panel, borderBottom: `1px solid ${C.border}`,
        height: 36, flexShrink: 0, overflowX: 'auto',
      }}>
        {sessions.map(sess => (
          <div
            key={sess.key}
            onClick={() => switchTab(sess.key)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '0 8px 0 12px', cursor: 'pointer',
              maxWidth: 200, minWidth: 100, flexShrink: 0,
              background: sess.key === activeKey ? C.bg : 'transparent',
              borderRight: `1px solid ${C.border}`,
              borderTop: `2px solid ${sess.key === activeKey ? C.accent : 'transparent'}`,
              color: sess.key === activeKey ? C.text : C.sub,
              fontSize: 12,
            }}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
              {sess.fileName}
            </span>
            {sess.status === 'loading-diagnose' && <Spinner size={10} />}
            <span
              onClick={e => closeTab(sess.key, e)}
              style={{ color: C.dim, fontSize: 14, padding: '0 2px', flexShrink: 0, lineHeight: 1, cursor: 'pointer' }}
            >×</span>
          </div>
        ))}
        <button
          onClick={() => fileInputRef.current?.click()}
          style={{
            width: 36, background: 'transparent', border: 'none', color: C.sub,
            fontSize: 20, cursor: 'pointer', borderRight: `1px solid ${C.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}
        >+</button>
      </div>

      {/* ════ 3-PANEL BODY ════ */}
      <div style={{ display: 'flex', flex: '0 0 auto', height: 'calc(100vh - 36px)', minHeight: 500 }}>

        {/* ── LEFT: 2D/3D + Axis + Highlight ── */}
        <div style={{
          width: 116, flexShrink: 0, background: C.panel,
          borderRight: `1px solid ${C.border}`,
          display: 'flex', flexDirection: 'column',
          padding: '8px 6px', gap: 5, overflowY: 'auto',
        }}>
          {/* 2D / 3D pill */}
          <div style={{
            background: C.bg, border: `1px solid ${C.border}`,
            borderRadius: 7, padding: 3, display: 'flex', gap: 2,
            opacity: activeSess ? 1 : 0.38, marginBottom: 2,
          }}>
            {[
              { label: '2D', sub: 'SLICE', mode: '2d', fn: handle2D },
              { label: '3D', sub: 'VOL',   mode: '3d', fn: handle3D },
            ].map(({ label, sub, mode, fn }) => {
              const isActive = activeSess?.viewMode === mode
              return (
                <button
                  key={mode}
                  onClick={() => activeSess && fn()}
                  disabled={!activeSess}
                  style={{
                    flex: 1, padding: '7px 4px', border: 'none', borderRadius: 5,
                    background: isActive ? '#d4d4d4' : 'transparent',
                    color: isActive ? '#080808' : C.dim,
                    cursor: activeSess ? 'pointer' : 'default',
                    transition: 'all 0.15s',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1,
                  }}
                >
                  <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.04em' }}>{label}</span>
                  <span style={{ fontSize: 8, fontWeight: 600, letterSpacing: '0.12em', opacity: 0.65 }}>{sub}</span>
                </button>
              )
            })}
          </div>

          <div style={{ height: 1, background: C.border, margin: '2px 0' }} />

          {/* Axis buttons */}
          {AXES.map(axis => {
            const isActive  = activeSess?.axis === axis
            const isLoading = activeSess?.status === 'loading-slices' && activeSess?.axis === axis
            return (
              <div
                key={axis}
                onClick={() => activeSess?.viewMode !== '3d' && handleAxis(axis)}
                style={{
                  borderRadius: 6, overflow: 'hidden', position: 'relative',
                  cursor: activeSess && activeSess.viewMode !== '3d' ? 'pointer' : 'default',
                  background: '#000',
                  border: `2px solid ${isActive ? C.accent : C.border}`,
                  opacity: activeSess && activeSess.viewMode !== '3d' ? 1 : 0.35,
                  boxShadow: isActive ? `0 0 0 1px rgba(200,200,200,0.2)` : 'none',
                  transition: 'border-color 0.15s, box-shadow 0.15s',
                }}
              >
                <img
                  src={AXIS_ICONS[axis]}
                  alt={axis}
                  style={{ width: '100%', height: 90, objectFit: 'contain', display: 'block' }}
                />
                <div style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0,
                  background: 'linear-gradient(transparent, rgba(0,0,0,0.88))',
                  padding: '12px 6px 5px',
                  textAlign: 'center',
                }}>
                  <span style={{
                    fontSize: 11, letterSpacing: '0.14em', fontWeight: 700,
                    color: isActive ? C.accent : 'rgba(255,255,255,0.7)',
                    textTransform: 'uppercase',
                  }}>
                    {axis.slice(0, 3).toUpperCase()}
                  </span>
                </div>
                {isLoading && (
                  <div style={{
                    position: 'absolute', inset: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: 'rgba(13,17,23,0.75)',
                  }}>
                    <Spinner size={18} />
                  </div>
                )}
              </div>
            )
          })}

          {/* ── Highlight toggle ── */}
          <div style={{ height: 1, background: C.border, margin: '4px 0 2px' }} />

          <div style={{
            background: C.bg, border: `1px solid ${activeSess?.maskReady ? '#4a1a1a' : C.border}`,
            borderRadius: 7, padding: 3, display: 'flex', gap: 2,
            opacity: activeSess?.maskReady ? 1 : 0.3,
          }}>
            {[false, true].map(on => {
              const isActive = activeSess?.highlightOn === on
              return (
                <button
                  key={String(on)}
                  onClick={() => activeSess?.maskReady && toggleHighlight(on)}
                  disabled={!activeSess?.maskReady}
                  style={{
                    flex: 1, padding: '6px 4px', border: 'none', borderRadius: 5,
                    background: isActive ? (on ? '#3a0808' : '#1e1e1e') : 'transparent',
                    color: isActive ? (on ? C.red : C.text) : C.dim,
                    cursor: activeSess?.maskReady ? 'pointer' : 'default',
                    transition: 'all 0.15s',
                    display: 'flex', flexDirection: 'column', alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.1em' }}>
                    {on ? 'ON' : 'OFF'}
                  </span>
                </button>
              )
            })}
          </div>
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textAlign: 'center',
            color: activeSess?.maskReady ? (activeSess.highlightOn ? C.red : C.sub) : C.dim,
          }}>
            HIGHLIGHT
          </span>

          {!activeSess && (
            <p style={{ fontSize: 10, color: C.dim, textAlign: 'center', marginTop: 6, lineHeight: 1.7 }}>
              파일을<br />업로드하면<br />활성화됩니다
            </p>
          )}
        </div>

        {/* ── CENTER: Viewer + Thumbnails ── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Title bar */}
          <div style={{
            height: 34, display: 'flex', alignItems: 'center',
            paddingLeft: 16, paddingRight: 16,
            borderBottom: `1px solid ${C.border}`, flexShrink: 0, background: C.panel,
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: C.text, letterSpacing: '0.04em' }}>
              {activeSess?.viewMode === '3d'
                ? `3D Render${useHighlight ? ' · HIGHLIGHT' : ''}`
                : activeSess?.axis
                  ? `${activeSess.axis.toUpperCase()} View${useHighlight ? ' · HIGHLIGHT' : ''}`
                  : 'BRAIN TUMOR ANALYSIS'}
            </span>
            {effSliceCount > 0 && activeSess?.viewMode !== '3d' && (
              <span style={{ marginLeft: 'auto', fontSize: 11, color: C.dim }}>
                {activeSess.currentIndex + 1} / {effSliceCount}
              </span>
            )}
          </div>

          {/* Main image area */}
          <div ref={sliceViewRef} style={{ flex: 1, position: 'relative', background: '#050505', overflow: 'hidden' }}>

            {/* Niivue 3D — display:none when 2D so WebGL doesn't bleed over HTML layers */}
            <div style={{ position: 'absolute', inset: 0, display: activeSess?.viewMode === '3d' ? 'block' : 'none' }}>
              <canvas ref={nvCanvasRef} style={{ width: '100%', height: '100%' }} />
            </div>

            {/* 2D slice */}
            <div style={{ position: 'absolute', inset: 0, display: activeSess?.viewMode === '3d' ? 'none' : 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {sliceUrl
                ? <img
                    src={sliceUrl}
                    alt="MRI slice"
                    style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }}
                  />
                : <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                    {activeSess?.status === 'loading-slices'
                      ? <>
                          <Spinner size={28} />
                          <p style={{ color: C.sub, fontSize: 13 }}>슬라이스 생성 중...</p>
                        </>
                      : <>
                          <p style={{ color: C.dim, fontSize: 14 }}>좌측에서 축(Axis)을 선택하세요</p>
                          <p style={{ color: C.dim, fontSize: 11, opacity: 0.7 }}>Axial / Coronal / Sagittal</p>
                        </>
                    }
                  </div>
              }
            </div>
          </div>

          {/* Thumbnail strip */}
          {activeSess?.viewMode !== '3d' && (
            <div style={{ flexShrink: 0, background: '#080808', borderTop: `1px solid ${C.border}` }}>
              <div style={{ display: 'flex', justifyContent: 'flex-end', borderBottom: `1px solid ${C.border}` }}>
                <span style={{ color: C.dim, fontSize: 11, padding: '1px 8px', alignSelf: 'center', marginRight: 'auto', marginLeft: 8 }}>
                  Thumbnails
                </span>
                <button
                  onClick={() => setThumbsOpen(p => !p)}
                  style={{
                    background: 'transparent', border: 'none', color: C.dim,
                    cursor: 'pointer', padding: '3px 12px', fontSize: 11,
                  }}
                >{thumbsOpen ? '▲' : '▼'}</button>
              </div>

              {thumbsOpen && (
                <div
                  ref={thumbListRef}
                  style={{
                    display: 'flex', gap: 4, padding: '6px 8px',
                    overflowX: 'auto', height: 82,
                    scrollbarWidth: 'thin', scrollbarColor: `${C.dim} transparent`,
                  }}
                >
                  {thumbUrls.length > 0
                    ? thumbUrls.map((url, i) => (
                        <div
                          key={i}
                          data-idx={i}
                          onClick={() => activeSess && updateSess(activeSess.key, { currentIndex: i })}
                          style={{
                            flexShrink: 0, width: 60, height: 70, borderRadius: 4,
                            overflow: 'hidden', cursor: 'pointer',
                            border: `2px solid ${i === activeSess?.currentIndex ? C.accent : C.border}`,
                            background: C.panel,
                          }}
                        >
                          <img
                            src={url}
                            alt={`slice ${i}`}
                            loading="lazy"
                            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                          />
                        </div>
                      ))
                    : <p style={{ color: C.dim, fontSize: 11, margin: 'auto' }}>
                        축을 선택하면 썸네일이 표시됩니다
                      </p>
                  }
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── RIGHT: Records + Buttons ── */}
        <div style={{
          width: 220, flexShrink: 0, background: C.panel,
          borderLeft: `1px solid ${C.border}`,
          display: 'flex', flexDirection: 'column',
        }}>
          <div style={{ padding: '10px 12px 8px', borderBottom: `1px solid ${C.border}` }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: C.sub, letterSpacing: '0.04em' }}>
              환자 MRI 기록
            </span>
          </div>

          <div style={{ padding: '8px 10px', borderBottom: `1px solid ${C.border}` }}>
            {sessions.length === 0
              ? <p style={{ fontSize: 11, color: C.dim, textAlign: 'center', padding: '8px 0' }}>업로드된 파일 없음</p>
              : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {sessions.map(sess => (
                    <div
                      key={sess.key}
                      onClick={() => switchTab(sess.key)}
                      style={{
                        padding: '7px 10px', borderRadius: 6, cursor: 'pointer',
                        background: sess.key === activeKey ? '#242424' : C.hover,
                        border: `1px solid ${sess.key === activeKey ? '#606060' : C.border}`,
                      }}
                    >
                      <p style={{
                        fontSize: 12, color: C.text,
                        fontWeight: sess.key === activeKey ? 600 : 400,
                        marginBottom: 2, overflow: 'hidden',
                        textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {sess.fileName}
                      </p>
                      <p style={{ fontSize: 10, color: C.sub }}>
                        {sess.uploadedAt.toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  ))}
                </div>
              )
            }
          </div>

          {/* 진단 기록 */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '8px 12px 6px', borderBottom: `1px solid ${C.border}` }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: C.sub, letterSpacing: '0.04em' }}>
                진단 기록
              </span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '6px 10px' }}>
              {diagHistory.length === 0
                ? <p style={{ fontSize: 11, color: C.dim, textAlign: 'center', marginTop: 14 }}>진단 기록 없음</p>
                : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    {diagHistory.map((d, i) => {
                      const isTumor = d.title?.includes('종양')
                      return (
                        <div key={d.id ?? i} style={{
                          padding: '8px 10px', borderRadius: 6,
                          background: C.hover,
                          border: `1px solid ${isTumor ? '#3a1a1a' : '#1a3a2a'}`,
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3 }}>
                            <span style={{
                              fontSize: 10, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                              background: isTumor ? '#3a0a0a' : '#0a2a1a',
                              color: isTumor ? C.red : C.green,
                              flexShrink: 0,
                            }}>
                              {isTumor ? 'TUMOR' : 'NORMAL'}
                            </span>
                            <p style={{
                              fontSize: 11, color: C.text, overflow: 'hidden',
                              textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
                            }}>
                              {d.title || 'AI 진단'}
                            </p>
                          </div>
                          {d.summary && (
                            <p style={{
                              fontSize: 10, color: C.sub, lineHeight: 1.5,
                              overflow: 'hidden', display: '-webkit-box',
                              WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                            }}>
                              {d.summary}
                            </p>
                          )}
                          <p style={{ fontSize: 10, color: C.dim, marginTop: 3 }}>
                            {d.createdAt
                              ? new Date(d.createdAt).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
                              : ''}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                )
              }
            </div>
          </div>

          {activeSess?.errorMsg && (
            <div style={{ padding: '0 10px 6px' }}>
              <p style={{
                fontSize: 11, color: C.red,
                padding: '6px 8px', background: '#1a0808',
                border: '1px solid #3a1010', borderRadius: 4, lineHeight: 1.5,
              }}>
                {activeSess.errorMsg}
              </p>
            </div>
          )}

          <div style={{ padding: 10, borderTop: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <Btn onClick={() => fileInputRef.current?.click()}>파일 업로드</Btn>
            <Btn
              onClick={activeSess?.viewMode === '3d' ? handle2D : handle3D}
              disabled={!activeSess}
            >
              {activeSess?.viewMode === '3d' ? '2D 변환' : '3D 변환'}
            </Btn>
            <Btn
              onClick={handleDiagnose}
              disabled={!activeSess || activeSess.status === 'loading-diagnose'}
              primary
            >
              {activeSess?.status === 'loading-diagnose'
                ? <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                    <Spinner size={12} />분석 중...
                  </span>
                : '분석하기'
              }
            </Btn>
          </div>
        </div>
      </div>

      {/* ════ ANALYSIS RESULTS PANEL ════ */}
      {activeSess?.status === 'done' && clf && (
        <div style={{ background: C.bg, borderTop: `1px solid ${C.border}`, padding: 16 }}>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
            <div style={{ padding: 16, borderRadius: 8, background: C.panel, border: `1px solid ${clf.prediction === 'Tumor' ? '#4a1a1a' : '#1a4a2a'}` }}>
              <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 8 }}>Prediction</p>
              <p style={{ fontSize: 24, fontWeight: 700, color: clf.prediction === 'Tumor' ? C.red : C.green }}>
                {clf.prediction === 'Tumor' ? 'TUMOR' : 'NORMAL'}
              </p>
              <p style={{ fontSize: 11, color: C.sub, marginTop: 4 }}>{clf.prediction}</p>
            </div>

            <div style={{ padding: 16, borderRadius: 8, background: C.panel, border: `1px solid ${C.border}` }}>
              <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 8 }}>Confidence</p>
              <p style={{ fontSize: 24, fontWeight: 700, color: confColor(clf.confidence) }}>
                {(clf.confidence * 100).toFixed(1)}%
              </p>
              <div style={{ marginTop: 10, height: 3, background: C.border, borderRadius: 2 }}>
                <div style={{ width: `${clf.confidence * 100}%`, height: '100%', background: confColor(clf.confidence), borderRadius: 2 }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
                <span style={{ fontSize: 11, color: C.sub }}>Tumor {(clf.tumor_probability * 100).toFixed(1)}%</span>
                <span style={{ fontSize: 11, color: C.sub }}>Normal {(clf.normal_probability * 100).toFixed(1)}%</span>
              </div>
            </div>

            {safety && (
              <div style={{ padding: 16, borderRadius: 8, background: C.panel, border: `1px solid ${C.border}` }}>
                <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 8 }}>Risk Level</p>
                <p style={{ fontSize: 16, fontWeight: 700, textTransform: 'uppercase', color: safety.risk_level === 'low' ? C.green : safety.risk_level === 'moderate' ? C.yellow : C.red }}>
                  {safety.risk_level?.replace('_', ' ')}
                </p>
                <p style={{ fontSize: 12, color: C.sub, marginTop: 6, lineHeight: 1.6 }}>{safety.clinical_action}</p>
                {safety.requires_specialist_review && (
                  <span style={{ display: 'inline-block', marginTop: 6, fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#1e1e1e', color: C.yellow, border: '1px solid #444444' }}>
                    전문의 검토 필요
                  </span>
                )}
              </div>
            )}
          </div>

          {report && (
            <div style={{ padding: 18, borderRadius: 8, background: C.panel, border: `1px solid ${C.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, paddingBottom: 12, borderBottom: `1px solid ${C.border}` }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.accent }} />
                <p style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.12em', color: C.sub, textTransform: 'uppercase' }}>AI Medical Report</p>
                {activeSess.result?.metadata?.processing_time_ms && (
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: C.dim }}>
                    {activeSess.result.metadata.processing_time_ms}ms
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {report.impression && (
                  <div>
                    <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 6 }}>Impression</p>
                    <p style={{ fontSize: 14, color: C.text, lineHeight: 1.8 }}>{report.impression}</p>
                  </div>
                )}
                {report.findings && (
                  <div>
                    <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 6 }}>Findings</p>
                    <p style={{ fontSize: 14, color: C.text, lineHeight: 1.8 }}>{report.findings}</p>
                  </div>
                )}
                {report.recommendations?.length > 0 && (
                  <div>
                    <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 6 }}>Recommendations</p>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {report.recommendations.map((r, i) => (
                        <li key={i} style={{ display: 'flex', gap: 10, fontSize: 14, color: C.text, lineHeight: 1.7 }}>
                          <span style={{ color: C.accent, flexShrink: 0 }}>▸</span><span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {report.differential_diagnosis?.length > 0 && (
                  <div>
                    <p style={{ fontSize: 11, letterSpacing: '0.15em', color: C.sub, textTransform: 'uppercase', marginBottom: 6 }}>Differential Diagnosis</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {report.differential_diagnosis.map((d, i) => (
                        <span key={i} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#1e1e1e', color: C.accent, border: '1px solid #3a3a3a' }}>{d}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {refs.length > 0 && (
            <div style={{ marginTop: 10, padding: 16, borderRadius: 8, background: C.panel, border: `1px solid ${C.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#848484' }} />
                <p style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.12em', color: C.sub, textTransform: 'uppercase' }}>
                  References ({refs.length})
                </p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {refs.map((ref, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, fontSize: 13 }}>
                    <span style={{ color: C.dim, flexShrink: 0, width: 16, fontFamily: 'monospace' }}>{i + 1}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ color: C.sub, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ref.source}</p>
                      <p style={{ color: C.dim, marginTop: 2, lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                        {ref.content?.slice(0, 120)}...
                      </p>
                    </div>
                    <span style={{ flexShrink: 0, color: '#848484', fontSize: 12, fontFamily: 'monospace' }}>
                      {((ref.relevance_score ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeSess.result?.disclaimer && (
            <p style={{ marginTop: 10, fontSize: 12, color: C.sub, lineHeight: 1.7 }}>
              ⚠ {activeSess.result.disclaimer}
            </p>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept=".nii,.nii.gz"
        style={{ display: 'none' }}
        onChange={e => { handleFile(e.target.files?.[0]); e.target.value = '' }}
      />
      <style>{`@keyframes wj-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

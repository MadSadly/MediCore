/**
 * GradCAM 히트맵 오버레이 뷰어
 */

export default function GradCAMViewer({ gradcamBase64, loading }) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-5 text-center">
        <div className="animate-pulse text-slate-400">
          <p className="text-2xl mb-1">🔬</p>
          <p className="text-sm">AI 시각화 분석 중...</p>
        </div>
      </div>
    );
  }

  if (!gradcamBase64) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500 uppercase tracking-wide">AI 진단 근거 시각화</p>
        <span className="text-xs bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded-full">
          GradCAM
        </span>
      </div>

      <img
        src={`data:image/png;base64,${gradcamBase64}`}
        alt="GradCAM 히트맵"
        className="w-full rounded-lg object-contain max-h-72"
      />

      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-sky-400 inline-block" />
          낮은 관련성
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-400 inline-block" />
          중간
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
          높은 관련성
        </div>
      </div>
    </div>
  );
}

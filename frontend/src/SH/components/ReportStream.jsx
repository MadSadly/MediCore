/**
 * Gemini 소견서 SSE 스트리밍 표시
 */

export default function ReportStream({ report, loading, citations }) {
  if (!loading && !report) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500 uppercase tracking-wide">AI 임상 소견서</p>
        {loading && (
          <span className="flex items-center gap-1 text-xs text-sky-400">
            <span className="animate-pulse">●</span> 생성 중
          </span>
        )}
      </div>

      <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap min-h-16">
        {report}
        {loading && <span className="animate-pulse text-sky-400">▌</span>}
      </div>

      {citations && citations.length > 0 && (
        <div className="border-t border-slate-700 pt-3 space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wide">근거 문헌</p>
          {citations.map((c, idx) => (
            <div key={idx} className="rounded-lg bg-slate-900/50 p-3 text-xs text-slate-400">
              <p className="font-medium text-slate-200 mb-0.5">{c.title}</p>
              <p>{c.source}{c.page ? ` · p.${c.page}` : ""}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

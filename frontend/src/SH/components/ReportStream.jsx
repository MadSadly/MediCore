/**
 * Gemini 소견 SSE 스트리밍 · 인용 각주 배지 · 자동 스크롤 · 복사
 */

import { useEffect, useRef, useState } from "react";

export default function ReportStream({ report, loading, citations }) {
  const bodyRef = useRef(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!bodyRef.current) return;
    bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [report]);

  useEffect(() => {
    if (!copied) return undefined;
    const timeoutId = setTimeout(() => setCopied(false), 1200);
    return () => clearTimeout(timeoutId);
  }, [copied]);

  const handleCopy = async () => {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
    } catch {
      console.warn("clipboard write failed");
    }
  };

  const scrollToCitation = (idx) => {
    const el = document.getElementById(`sh-citation-${idx}`);
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  if (!loading && !report) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide">AI 임상 소견서</p>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="flex items-center gap-1 text-xs text-sky-400">
              <span className="inline-block min-w-[7px] font-mono animate-pulse">▌</span>
              실시간 생성
            </span>
          )}
          <button
            type="button"
            onClick={handleCopy}
            disabled={!report}
            className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {copied ? "복사됨" : "복사"}
          </button>
        </div>
      </div>

      {citations && citations.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-slate-500 font-semibold">근거 각주</span>
          {citations.map((_, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => scrollToCitation(idx)}
              className="rounded-md border border-sky-500/40 bg-sky-500/15 px-2 py-0.5 text-[11px] font-bold text-sky-300 hover:bg-sky-500/25 transition-colors"
            >
              [{idx + 1}]
            </button>
          ))}
        </div>
      )}

      <div
        ref={bodyRef}
        className="max-h-64 overflow-y-auto text-sm text-slate-200 leading-relaxed whitespace-pre-wrap min-h-16 pr-1 custom-scrollbar"
      >
        {report}
        {loading && (
          <span className="inline-block w-px ml-px font-mono animate-pulse text-sky-400 align-baseline select-none" aria-hidden>
            ▍
          </span>
        )}
      </div>

      {citations && citations.length > 0 && (
        <div className="border-t border-slate-700 pt-3 space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wide">참고 문헌 · 근거</p>
          {citations.map((c, idx) => (
            <div
              id={`sh-citation-${idx}`}
              key={idx}
              className="scroll-mt-4 rounded-lg bg-slate-900/50 p-3 text-xs text-slate-400 border border-slate-700/80"
            >
              <button
                type="button"
                onClick={() => scrollToCitation(idx)}
                className="mb-1 inline-flex items-center rounded border border-sky-500/35 bg-sky-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold text-sky-300"
              >
                [{idx + 1}]
              </button>
              <p className="font-medium text-slate-200 mb-0.5">{c.title}</p>
              <p>{c.source}{c.page ? ` · p.${c.page}` : ""}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

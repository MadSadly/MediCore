/**
 * Gemini report stream UI.
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

  if (!loading && !report) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide">AI clinical report</p>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="flex items-center gap-1 text-xs text-sky-400">
              <span className="animate-pulse">*</span> streaming
            </span>
          )}
          <button
            type="button"
            onClick={handleCopy}
            disabled={!report}
            className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {copied ? "copied" : "copy"}
          </button>
        </div>
      </div>

      <div
        ref={bodyRef}
        className="max-h-64 overflow-y-auto text-sm text-slate-200 leading-relaxed whitespace-pre-wrap min-h-16 pr-1"
      >
        {report}
        {loading && <span className="animate-pulse text-sky-400">|</span>}
      </div>

      {citations && citations.length > 0 && (
        <div className="border-t border-slate-700 pt-3 space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wide">citations</p>
          {citations.map((c, idx) => (
            <div key={idx} className="rounded-lg bg-slate-900/50 p-3 text-xs text-slate-400">
              <p className="font-medium text-slate-200 mb-0.5">{c.title}</p>
              <p>{c.source}{c.page ? ` / p.${c.page}` : ""}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

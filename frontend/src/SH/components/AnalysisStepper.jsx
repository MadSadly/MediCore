/**
 * SSE 진행 상태에 따른 7단계 스텝 바 (품질 → DL → 응급 → GradCAM → RAG → 소견서 → 완료)
 */

const PHASES = [
  { key: "quality", label: "품질 검증", short: "QC" },
  { key: "dl", label: "DL 추론", short: "DL" },
  { key: "emergency", label: "응급 판정", short: "ER" },
  { key: "gradcam", label: "GradCAM", short: "XAI" },
  { key: "rag", label: "문헌 검색", short: "RAG" },
  { key: "report", label: "소견서", short: "GPT" },
  { key: "finish", label: "완료", short: "OK" },
];

/** @param {{ step: string, gradcamLoading: boolean }} props */
export default function AnalysisStepper({ step, gradcamLoading }) {
  if (step === "idle" || step === "error") return null;

  const idx = (() => {
    switch (step) {
      case "uploading":
      case "image_validated":
        return 0;
      case "dl_running":
        return 1;
      case "dl_done":
        return gradcamLoading ? 2 : 1;
      case "gradcam":
        return 3;
      case "rag":
        return 4;
      case "report":
        return 5;
      case "done":
        return 6;
      default:
        return 0;
    }
  })();

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">
        분석 진행 단계
      </p>
      <div className="flex flex-wrap items-center gap-1 sm:gap-0 sm:justify-between">
        {PHASES.map((p, i) => {
          const done = i < idx;
          const active = i === idx;
          return (
            <div key={p.key} className="flex items-center flex-1 min-w-0 last:flex-none">
              <div className="flex flex-col items-center flex-1 min-w-[3rem]">
                <div
                  className={`
                    relative flex h-9 w-9 items-center justify-center rounded-full text-[10px] font-black
                    transition-all duration-300
                    ${done
                      ? "bg-emerald-500/90 text-slate-900 shadow-[0_0_12px_rgba(16,185,129,0.45)]"
                      : active
                        ? "bg-sky-500 text-white ring-2 ring-sky-300/70 shadow-[0_0_14px_rgba(14,165,233,0.35)]"
                        : "bg-slate-800 text-slate-500 border border-slate-600"
                    }
                  `}
                  title={p.label}
                >
                  {done ? "✓" : p.short}
                  {active && !done ? (
                    <span
                      className="pointer-events-none absolute inset-0 rounded-full border-2 border-white/40 animate-ping opacity-40"
                      aria-hidden
                    />
                  ) : null}
                </div>
                <span
                  className={`mt-1.5 hidden text-[9px] font-semibold uppercase tracking-wide sm:block text-center max-w-[4.5rem] leading-tight ${
                    active ? "text-sky-300" : done ? "text-emerald-400/90" : "text-slate-600"
                  }`}
                >
                  {p.label}
                </span>
              </div>
              {i < PHASES.length - 1 && (
                <div
                  className={`mx-0.5 h-0.5 flex-1 min-w-[4px] max-w-[24px] rounded-full transition-colors ${
                    i < idx ? "bg-emerald-500/70" : "bg-slate-700"
                  }`}
                  aria-hidden
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

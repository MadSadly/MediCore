/**
 * SSE 진행 단계 표시 스텝퍼 — step은 페이지 STEPS 문자열 값
 */

const DISPLAY_STEPS = [
  { key: "uploading", label: "업로드", mapFrom: ["uploading"] },
  { key: "image_validated", label: "품질 검증", mapFrom: ["image_validated"] },
  { key: "dl_running", label: "AI 분석", mapFrom: ["dl_running"] },
  { key: "dl_done", label: "진단 완료", mapFrom: ["dl_done"] },
  { key: "gradcam", label: "시각화", mapFrom: ["gradcam"] },
  { key: "rag", label: "문헌 검색", mapFrom: ["rag"] },
  { key: "report", label: "소견서", mapFrom: ["report", "done"] },
];

/** @param {{ step: string }} props */
export default function AnalysisStepper({ step }) {
  if (step === "idle" || step === "error") return null;

  const currentIdx = DISPLAY_STEPS.findIndex((d) => d.mapFrom.includes(step));
  const safeIdx = currentIdx >= 0 ? currentIdx : 0;

  return (
    <div className="w-full overflow-x-auto pb-1 -mx-1 px-1">
      <div className="flex flex-row flex-nowrap items-center gap-0 min-w-min py-2">
        {DISPLAY_STEPS.map((s, i) => {
          const done = i < safeIdx;
          const active = i === safeIdx;

          const circleBase =
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-colors";

          const circleCls = done
            ? `${circleBase} border-transparent bg-transparent text-emerald-400 leading-none`
            : active
              ? `${circleBase} animate-pulse border-sky-400 bg-sky-500 text-white shadow-[0_0_14px_rgba(56,189,248,0.35)]`
              : `${circleBase} border-slate-600 bg-slate-800 text-slate-500`;

          const textCls = done
            ? "text-slate-100"
            : active
              ? "text-sky-400 font-semibold"
              : "text-slate-600";

          const circleInner = done ? "✅" : i + 1;

          return (
            <div key={s.key} className="flex flex-row flex-nowrap items-center shrink-0">
              <div className="flex flex-col items-center px-2 min-w-[4.25rem] sm:min-w-[4.75rem]">
                <div className={circleCls} aria-current={active ? "step" : undefined}>
                  {circleInner}
                </div>
                <span className={`mt-1.5 text-center text-[11px] leading-snug whitespace-nowrap ${textCls}`}>
                  {s.label}
                </span>
              </div>
              {i < DISPLAY_STEPS.length - 1 && (
                <div
                  className={`mx-1 h-[1px] w-6 shrink-0 sm:w-10 ${done ? "bg-emerald-500/55" : "bg-slate-700/75"}`}
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

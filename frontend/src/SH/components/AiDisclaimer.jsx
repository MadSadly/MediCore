/**
 * 고정 면책 문구 (진단 결과 상단/하단 배너)
 */

export default function AiDisclaimer({ className = "" }) {
  return (
    <div
      className={`rounded-lg border border-amber-500/25 bg-amber-950/25 px-3 py-2 text-[11px] leading-relaxed text-amber-200/85 ${className}`}
      role="note"
    >
      <strong className="text-amber-400/95">면책:</strong>{" "}
      본 결과는 AI 보조 지표일 뿐이며, 최종 진단·처치·법적 책임은 반드시 전문의가 수행합니다.
    </div>
  );
}

/**
 * 고정 면책 조항
 */

export default function AiDisclaimer() {
  return (
    <div
      className="flex gap-2 rounded-lg border border-slate-700/50 bg-slate-800/30 px-3 py-2.5 text-xs text-slate-500 leading-relaxed"
      role="note"
    >
      <span className="select-none shrink-0" aria-hidden>
        ⚠️
      </span>
      <p className="m-0">
        본 AI 분석 결과는 임상 의사 결정을 보조하는 도구입니다.
        <br />
        최종 진단 및 치료 결정은 반드시 담당 의사의 판단에 따라야 합니다.
      </p>
    </div>
  );
}

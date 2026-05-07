/**
 * AI 진단 면책 — 페이지 톤에 맞는 슬레이트 박스 + 앰버 느낌표 아이콘만 강조
 */

import { AlertCircle } from "lucide-react";

export default function AiDisclaimer({ className = "" }) {
  return (
    <aside
      className={`flex gap-3 rounded-lg border border-slate-700/50 bg-slate-800/30 px-4 py-3 text-sm leading-relaxed text-slate-400 ${className}`}
      role="note"
    >
      <AlertCircle
        className="h-6 w-6 shrink-0 text-amber-400"
        strokeWidth={2}
        aria-hidden
      />
      <p className="m-0">
        <span className="font-semibold text-slate-200">AI 진단 유의사항</span>
        <br />
        본 AI 분석 결과는 임상 의사 결정을 보조하는 도구입니다.
        <br />
        최종 진단 및 치료 결정은 반드시 담당 의사의 판단에 따라야 합니다.
      </p>
    </aside>
  );
}

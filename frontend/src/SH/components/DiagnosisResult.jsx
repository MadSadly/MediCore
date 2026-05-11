/**
 * 5개 질환 확신도 바 차트 (임계값 기반 바 강조)
 */

const DISEASE_COLORS = {
  정상:       "bg-green-400",
  녹내장:     "bg-blue-500",
  백내장:     "bg-yellow-400",
  당뇨망막병증: "bg-orange-500",
  황반변성:   "bg-red-500",
};

const THRESH_WARN = 0.35;
const THRESH_HIGH = 0.55;

function barClasses(score) {
  const pct = typeof score.confidence === "number" ? score.confidence : 0;
  const disease = score.disease_name;
  const base = DISEASE_COLORS[disease] || "bg-slate-500";
  const isNormal = disease === "정상";
  if (isNormal) return base;

  let ring = "";
  if (pct >= THRESH_HIGH) ring = "shadow-[inset_0_0_0_1px_rgba(248,113,113,0.9)]";
  else if (pct >= THRESH_WARN) ring = "shadow-[inset_0_0_0_1px_rgba(250,204,21,0.7)]";

  return `${base} ${ring}`;
}

export default function DiagnosisResult({ dlResult }) {
  if (!dlResult || !dlResult.primary_disease) return null;

  const { all_scores } = dlResult;
  const safeScores = Array.isArray(all_scores) ? all_scores : [];

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6 space-y-4">
      <div className="space-y-3">
        <p className="text-base text-slate-400 uppercase tracking-wide font-semibold">전체 질환 분석</p>
        <p className="text-[12.5px] text-slate-400 mb-2">
          질병 클래스는 {Math.round(THRESH_WARN * 100)}% 이상에서 주황 테두리, {Math.round(THRESH_HIGH * 100)}% 이상에서 빨강 테두리로 표시합니다.
        </p>
        {[...safeScores]
          .sort((a, b) => b.confidence - a.confidence)
          .map((score) => (
            <div key={score.disease_id}>
              <div className="flex justify-between text-base mb-1">
                <span className={`font-medium ${score.is_positive ? "text-slate-100" : "text-slate-500"}`}>
                  {score.disease_name}
                </span>
                <span className="text-sm font-medium text-slate-300">
                  {(score.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-900/80 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-3 rounded-full transition-all duration-700 ${barClasses(score)}`}
                  style={{ width: `${score.confidence * 100}%` }}
                />
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

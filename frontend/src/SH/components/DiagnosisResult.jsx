/**
 * 5개 질환 확신도 바 차트 + 주요 진단 표시 (임계값 기반 바 강조)
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

  const { primary_disease, all_scores, stage } = dlResult;
  const safeScores = Array.isArray(all_scores) ? all_scores : [];

  const primaryPct = typeof primary_disease.confidence === "number"
    ? primary_disease.confidence * 100
    : 0;
  let primaryAccent = "text-sky-400";
  if (primary_disease.disease_name !== "정상") {
    if (primaryPct >= THRESH_HIGH * 100) primaryAccent = "text-red-400";
    else if (primaryPct >= THRESH_WARN * 100) primaryAccent = "text-amber-400";
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">주요 진단</p>
          <p className="text-2xl font-bold text-slate-100 mt-0.5">
            {primary_disease.disease_name}
          </p>
          {stage && (
            <p className="text-sm text-slate-400 mt-0.5">
              중증도: <span className="font-medium text-slate-200">{stage.stage_name}</span>
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">확신도</p>
          <p className={`text-3xl font-bold ${primaryAccent}`}>
            {primaryPct.toFixed(1)}%
          </p>
          {primary_disease.disease_name !== "정상" && primaryPct >= THRESH_WARN * 100 && (
            <p className="text-[10px] text-slate-500 mt-1">
              {primaryPct >= THRESH_HIGH * 100 ? "고위험 구간으로 강조 표시되었습니다." : "중간 이상 가능성 구간입니다."}
            </p>
          )}
        </div>
      </div>

      <hr className="border-slate-700" />

      <div className="space-y-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide">전체 질환 분석</p>
        <p className="text-[10px] text-slate-600 mb-2">
          질병 클래스는 {Math.round(THRESH_WARN * 100)}% 이상에서 주황 테두리, {Math.round(THRESH_HIGH * 100)}% 이상에서 빨강 테두리로 표시합니다.
        </p>
        {[...safeScores]
          .sort((a, b) => b.confidence - a.confidence)
          .map((score) => (
            <div key={score.disease_id}>
              <div className="flex justify-between text-sm mb-0.5">
                <span className={`font-medium ${score.is_positive ? "text-slate-100" : "text-slate-500"}`}>
                  {score.disease_name}
                </span>
                <span className="text-slate-400">
                  {(score.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-900/80 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-700 ${barClasses(score)}`}
                  style={{ width: `${score.confidence * 100}%` }}
                />
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

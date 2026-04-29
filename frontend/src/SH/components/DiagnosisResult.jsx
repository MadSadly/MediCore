/**
 * 5개 질환 확신도 바 차트 + 주요 진단 표시
 */

const DISEASE_COLORS = {
  정상:       "bg-green-400",
  녹내장:     "bg-blue-500",
  백내장:     "bg-yellow-400",
  당뇨망막병증: "bg-orange-500",
  황반변성:   "bg-red-500",
};

export default function DiagnosisResult({ dlResult }) {
  if (!dlResult) return null;

  const { primary_disease, all_scores, stage } = dlResult;

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
          <p className="text-3xl font-bold text-sky-400">
            {(primary_disease.confidence * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <hr className="border-slate-700" />

      <div className="space-y-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide">전체 질환 분석</p>
        {[...all_scores]
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
              <div className="w-full bg-slate-900/80 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-700
                    ${DISEASE_COLORS[score.disease_name] || "bg-slate-500"}`}
                  style={{ width: `${score.confidence * 100}%` }}
                />
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

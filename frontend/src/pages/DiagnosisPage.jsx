export default function DiagnosisPage({ label, assignee, diseaseType }) {
  return (
    <div className="max-w-2xl mx-auto flex items-center justify-center min-h-[60vh]">
      <div className="text-center bg-[#0f172a] border border-slate-800 rounded-2xl p-16 w-full">
        <p className="text-5xl mb-6">🚧</p>
        <h2 className="text-2xl font-bold text-slate-200 mb-2">{label}</h2>
        <p className="text-slate-500 text-sm mb-1">담당: {assignee}</p>
        <p className="text-slate-600 text-xs font-mono mb-8">{diseaseType}</p>
        <p className="text-slate-400 text-sm leading-relaxed">
          아직 개발중입니다.<br />
          담당 모듈이 완성되면 이 페이지에서 AI 진단을 수행하고<br />
          결과를 환자 리포트로 저장할 수 있습니다.
        </p>
        <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-600">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
          개발 진행 중
        </div>
      </div>
    </div>
  )
}
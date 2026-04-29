/**
 * 응급 판정 시 강제 알림 모달 (OPH-08)
 */

const LEVEL_STYLES = {
  3: { bg: "bg-red-50",    border: "border-red-400",  icon: "🚨", text: "text-red-700",  label: "즉시 처치 필요" },
  2: { bg: "bg-orange-50", border: "border-orange-400", icon: "⚠️", text: "text-orange-700", label: "신속 대응 필요" },
  1: { bg: "bg-yellow-50", border: "border-yellow-400", icon: "⚡", text: "text-yellow-700", label: "주의 필요" },
};

export default function EmergencyModal({ emergency, onClose }) {
  if (!emergency?.is_emergency) return null;

  const style = LEVEL_STYLES[emergency.emergency_level] || LEVEL_STYLES[2];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className={`w-full max-w-md mx-4 rounded-2xl border-2 ${style.border} ${style.bg} p-6 shadow-xl`}>
        <div className="text-center space-y-3">
          <p className="text-5xl">{style.icon}</p>

          <div>
            <p className={`text-lg font-bold ${style.text}`}>{style.label}</p>
            <p className={`text-sm mt-1 ${style.text} opacity-80`}>
              {emergency.reason}
            </p>
          </div>

          <div className="bg-white/60 rounded-xl p-3 text-xs text-gray-600">
            AI 진단 결과를 확인하고 즉시 전문의 판단을 진행하세요.
            본 알림은 AI 보조 판단이며 최종 진단은 의사에게 있습니다.
          </div>

          <button
            type="button"
            onClick={onClose}
            className={`w-full py-2.5 rounded-xl font-medium text-white
              ${emergency.emergency_level === 3 ? "bg-red-500 hover:bg-red-600" : "bg-orange-500 hover:bg-orange-600"}
              transition-colors`}
          >
            확인 — 즉시 조치하겠습니다
          </button>
        </div>
      </div>
    </div>
  );
}

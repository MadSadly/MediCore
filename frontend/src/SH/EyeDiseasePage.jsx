/**
 * frontend/src/SH/EyeDiseasePage.jsx
 * 안과 CDSS 메인 진단 페이지 — 라우트: /patients/:id/eye-disease
 *
 * SSE 순서: image_validated → dl_result → emergency → gradcam_ready → rag_retrieved
 *           → report_chunk* → done
 */

import { useState, useRef, useEffect } from "react";
import { useParams } from "react-router-dom";
import { analyzeEye } from "./api/eyeApi";
import ImageUpload from "./components/ImageUpload";
import DiagnosisResult from "./components/DiagnosisResult";
import GradCAMViewer from "./components/GradCAMViewer";
import ReportStream from "./components/ReportStream";
import EmergencyModal from "./components/EmergencyModal";

const STEPS = {
  IDLE:            "idle",
  UPLOADING:       "uploading",
  IMAGE_VALIDATED: "image_validated",
  DL_RUNNING:      "dl_running",
  DL_DONE:         "dl_done",
  GRADCAM:         "gradcam",
  RAG:             "rag",
  REPORT:          "report",
  DONE:            "done",
  ERROR:           "error",
};

const STEP_LABELS = {
  uploading:       "이미지 업로드 중...",
  image_validated: "이미지 품질 검증 완료",
  dl_running:      "AI 분석 중...",
  dl_done:         "진단 완료",
  gradcam:         "시각화 분석 중...",
  rag:             "임상 문헌 검색 중...",
  report:          "소견서 생성 중...",
  done:            "분석 완료",
  error:           "오류 발생",
};

function isAbortError(err) {
  return err?.name === "AbortError";
}

export default function EyeDiseasePage() {
  const { id: patientId } = useParams();
  const [imageFile, setImageFile] = useState(null);
  const [step, setStep] = useState(STEPS.IDLE);
  const [dlResult, setDlResult] = useState(null);
  const [emergency, setEmergency] = useState(null);
  const [showEmergency, setShowEmergency] = useState(false);
  const [gradcamB64, setGradcamB64] = useState(null);
  const [gradcamLoading, setGradcamLoading] = useState(false);
  const [citations, setCitations] = useState([]);
  const [report, setReport] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState(null);
  const [qualityScore, setQualityScore] = useState(null);
  const [inferenceMs, setInferenceMs] = useState(null);

  const analyzeAbortRef = useRef(null);

  useEffect(() => {
    return () => {
      analyzeAbortRef.current?.abort();
      analyzeAbortRef.current = null;
    };
  }, []);

  const clearAnalysisState = () => {
    setStep(STEPS.IDLE);
    setDlResult(null);
    setEmergency(null);
    setShowEmergency(false);
    setGradcamB64(null);
    setGradcamLoading(false);
    setCitations([]);
    setReport("");
    setReportLoading(false);
    setError(null);
    setQualityScore(null);
    setInferenceMs(null);
  };

  const resetLoading = () => {
    setGradcamLoading(false);
    setReportLoading(false);
  };

  const reset = () => {
    analyzeAbortRef.current?.abort();
    analyzeAbortRef.current = null;
    clearAnalysisState();
  };

  const handleAnalyze = async () => {
    if (!imageFile || !patientId) return;

    analyzeAbortRef.current?.abort();
    const controller = new AbortController();
    analyzeAbortRef.current = controller;
    const { signal } = controller;

    clearAnalysisState();
    setStep(STEPS.UPLOADING);

    try {
      await analyzeEye(
        imageFile,
        {
          patientId,
          patientAge:      null,
          hasDiabetes:     false,
          hasHypertension: false,
          clinicalNote:    "",
        },
        (event, data) => {
          if (signal.aborted) return;
          switch (event) {
            case "image_validated":
              setStep(STEPS.IMAGE_VALIDATED);
              setQualityScore(data.quality_score);
              setStep(STEPS.DL_RUNNING);
              break;

            case "dl_result":
              setDlResult(data.dl_result);
              setInferenceMs(data.inference_time_ms);
              setStep(STEPS.DL_DONE);
              setGradcamLoading(true);
              break;

            case "emergency":
              setEmergency(data.emergency);
              if (data.emergency?.is_emergency) setShowEmergency(true);
              break;

            case "gradcam_ready":
              setGradcamB64(data.gradcam_base64);
              setGradcamLoading(false);
              setStep(STEPS.GRADCAM);
              break;

            case "rag_retrieved":
              setGradcamLoading(false);
              setCitations(data.citations ?? []);
              setStep(STEPS.RAG);
              setReportLoading(true);
              break;

            case "report_chunk":
              setReport((prev) => prev + (data.data ?? ""));
              setStep(STEPS.REPORT);
              break;

            case "done":
              resetLoading();
              if (data.inference_time_ms != null) setInferenceMs(data.inference_time_ms);
              if (data.quality_score != null) setQualityScore(data.quality_score);
              setStep(STEPS.DONE);
              break;

            case "error":
              setError(data.message || "알 수 없는 오류");
              resetLoading();
              setStep(STEPS.ERROR);
              break;

            default:
              break;
          }
        },
        signal,
      );
    } catch (err) {
      if (isAbortError(err)) return;
      setError(err.message);
      resetLoading();
      setStep(STEPS.ERROR);
    }
  };

  const isRunning = [
    STEPS.UPLOADING,
    STEPS.IMAGE_VALIDATED,
    STEPS.DL_RUNNING,
    STEPS.GRADCAM,
    STEPS.RAG,
    STEPS.REPORT,
  ].includes(step);

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100">
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">

        {showEmergency && (
          <EmergencyModal
            emergency={emergency}
            onClose={() => setShowEmergency(false)}
          />
        )}

        <div>
          <h1 className="text-xl font-bold text-slate-100">안과 AI 진단</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            환자 {!patientId ? "(ID 없음)" : `#${patientId}`} · 안저 이미지를 업로드하면 AI가 5개 질환을 분석합니다.
          </p>
        </div>

        <ImageUpload onImageSelect={setImageFile} disabled={isRunning} />

        {step !== STEPS.IDLE && (
          <div
            className={`flex items-center gap-2 text-sm px-4 py-2.5 rounded-lg border
              ${step === STEPS.ERROR
                ? "bg-rose-950/50 border-rose-800 text-rose-300"
                : "bg-slate-800/80 border-slate-700 text-sky-300"}`}
          >
            {isRunning && <span className="animate-spin">⏳</span>}
            {step === STEPS.DONE && <span>✅</span>}
            {step === STEPS.ERROR && <span>❌</span>}
            <span>{STEP_LABELS[step] || step}</span>
            {inferenceMs != null && step === STEPS.DONE && (
              <span className="ml-auto text-xs text-slate-500">
                추론 {Number(inferenceMs).toFixed(0)}ms
              </span>
            )}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-rose-800/50 bg-rose-950/30 p-4 text-sm text-rose-300">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={isRunning ? undefined : (step === STEPS.DONE ? reset : handleAnalyze)}
          disabled={(!imageFile && step === STEPS.IDLE) || !patientId}
          className={`w-full py-3 rounded-xl font-medium text-white transition-colors
            ${isRunning
              ? "bg-slate-600 cursor-not-allowed"
              : step === STEPS.DONE
                ? "bg-slate-600 hover:bg-slate-500"
                : "bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed"
            }`}
        >
          {!patientId
            ? "환자 ID가 없습니다"
            : isRunning
              ? "분석 중..."
              : step === STEPS.DONE
                ? "새 분석 시작"
                : "AI 분석 시작"}
        </button>

        {dlResult && <DiagnosisResult dlResult={dlResult} />}

        {(gradcamLoading || gradcamB64) && (
          <GradCAMViewer gradcamBase64={gradcamB64} loading={gradcamLoading} />
        )}

        {(reportLoading || report) && (
          <ReportStream
            report={report}
            loading={reportLoading}
            citations={citations}
          />
        )}

        {qualityScore !== null && step === STEPS.DONE && (
          <p className="text-xs text-slate-500 text-right">
            이미지 품질: {(qualityScore * 100).toFixed(0)}점
          </p>
        )}
      </div>
    </div>
  );
}

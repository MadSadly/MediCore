/**
 * GradCAM 히트맵 — 원본과 나란히 / 토글 / 오버레이 슬라이더 비교
 */

import { useState } from "react";

const VIEW = {
  SIDE: "side",
  TOGGLE: "toggle",
  OVERLAY: "overlay",
};

export default function GradCAMViewer({ gradcamBase64, originalObjectUrl, loading }) {
  const [view, setView] = useState(VIEW.SIDE);
  const [toggleWhich, setToggleWhich] = useState("heat");
  const [overlayOpacity, setOverlayOpacity] = useState(0.55);
  const [zoomedSrc, setZoomedSrc] = useState(null);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-5 text-center">
        <div className="animate-pulse text-slate-400">
          <p className="text-2xl mb-1">🔬</p>
          <p className="text-sm">AI 시각화 분석 중...</p>
        </div>
      </div>
    );
  }

  if (!gradcamBase64) return null;

  const heatSrc = `data:image/png;base64,${gradcamBase64}`;
  const hasOriginal = !!originalObjectUrl;
  const openZoom = (src) => setZoomedSrc(src);

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">AI 진단 근거 시각화</p>
          <p className="text-[11px] text-slate-500 mt-0.5">원본과 히트맵을 비교해 병변 주시 영역을 확인하세요.</p>
        </div>
        <span className="text-xs bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded-full w-fit">
          GradCAM
        </span>
      </div>

      {hasOriginal && (
        <div className="flex flex-wrap gap-2">
          {[
            [VIEW.SIDE, "나란히"],
            [VIEW.TOGGLE, "토글"],
            [VIEW.OVERLAY, "오버레이"],
          ].map(([k, lab]) => (
            <button
              key={k}
              type="button"
              onClick={() => setView(k)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                view === k
                  ? "bg-sky-600 text-white"
                  : "bg-slate-800 text-slate-400 border border-slate-600 hover:bg-slate-700"
              }`}
            >
              {lab}
            </button>
          ))}
        </div>
      )}

      <div className="rounded-lg overflow-hidden bg-black/40 border border-slate-700/80">
        {!hasOriginal ? (
          <div className="relative">
            <img
              src={heatSrc}
              alt="GradCAM 히트맵"
              className="w-full object-contain max-h-96 cursor-zoom-in hover:opacity-90 transition-opacity"
              onClick={() => openZoom(heatSrc)}
            />
            <span className="absolute top-2 right-2 rounded-full bg-black/60 px-2 py-1 text-xs text-slate-200">🔍</span>
          </div>
        ) : view === VIEW.SIDE ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-slate-700">
            <div className="bg-slate-900/80 p-2">
              <p className="text-[10px] text-slate-500 text-center mb-1 font-semibold uppercase">원본</p>
              <div className="relative">
                <img
                  src={originalObjectUrl}
                  alt="원본 안저"
                  className="w-full h-64 object-contain bg-black rounded-lg cursor-zoom-in hover:opacity-90 transition-opacity"
                  onClick={() => openZoom(originalObjectUrl)}
                />
                <span className="absolute top-2 right-2 rounded-full bg-black/60 px-2 py-1 text-xs text-slate-200">🔍</span>
              </div>
            </div>
            <div className="bg-slate-900/80 p-2">
              <p className="text-[10px] text-slate-500 text-center mb-1 font-semibold uppercase">GradCAM</p>
              <div className="relative">
                <img
                  src={heatSrc}
                  alt="GradCAM"
                  className="w-full h-64 object-contain bg-black rounded-lg cursor-zoom-in hover:opacity-90 transition-opacity"
                  onClick={() => openZoom(heatSrc)}
                />
                <span className="absolute top-2 right-2 rounded-full bg-black/60 px-2 py-1 text-xs text-slate-200">🔍</span>
              </div>
            </div>
          </div>
        ) : view === VIEW.TOGGLE ? (
          <div className="p-3">
            <div className="flex justify-center gap-2 mb-2">
              <button
                type="button"
                onClick={() => setToggleWhich("orig")}
                className={`rounded-md px-3 py-1 text-xs font-semibold ${toggleWhich === "orig" ? "bg-slate-600 text-white" : "text-slate-400"}`}
              >
                원본
              </button>
              <button
                type="button"
                onClick={() => setToggleWhich("heat")}
                className={`rounded-md px-3 py-1 text-xs font-semibold ${toggleWhich === "heat" ? "bg-orange-600/90 text-white" : "text-slate-400"}`}
              >
                히트맵
              </button>
            </div>
            <img
              src={toggleWhich === "orig" ? originalObjectUrl : heatSrc}
              alt={toggleWhich === "orig" ? "원본" : "GradCAM"}
              className="w-full h-64 object-contain bg-black rounded-lg mx-auto cursor-zoom-in hover:opacity-90 transition-opacity"
              onClick={() => openZoom(toggleWhich === "orig" ? originalObjectUrl : heatSrc)}
            />
          </div>
        ) : (
          <div className="p-3 space-y-2">
            <p className="text-[11px] text-slate-500 text-center">슬라이더로 히트맵 강도를 조절합니다.</p>
            <div
              className="relative w-full h-64 bg-black rounded-lg overflow-hidden cursor-zoom-in hover:opacity-90 transition-opacity"
              onClick={() => openZoom(heatSrc)}
            >
              <img
                src={originalObjectUrl}
                alt=""
                className="absolute inset-0 w-full h-full object-contain"
              />
              <img
                src={heatSrc}
                alt=""
                className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                style={{ opacity: overlayOpacity }}
              />
              <span className="absolute top-2 right-2 rounded-full bg-black/60 px-2 py-1 text-xs text-slate-200">🔍</span>
            </div>
            <label className="flex items-center gap-3 px-2 text-xs text-slate-400">
              <span className="w-12 shrink-0">투명도</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={overlayOpacity}
                onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                className="flex-1 accent-orange-500"
              />
              <span className="w-10 text-right tabular-nums">{Math.round(overlayOpacity * 100)}%</span>
            </label>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-sky-400 inline-block" />
          낮은 관련성
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-400 inline-block" />
          중간
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
          높은 관련성
        </div>
      </div>

      {zoomedSrc && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setZoomedSrc(null)}
        >
          <button
            type="button"
            className="absolute top-4 right-4 rounded-full bg-slate-900/80 border border-slate-600 w-9 h-9 text-slate-100"
            onClick={() => setZoomedSrc(null)}
            aria-label="확대 이미지 닫기"
          >
            ✕
          </button>
          <img
            src={zoomedSrc}
            alt="확대 이미지"
            className="max-w-[90vw] max-h-[90vh] object-contain rounded-xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

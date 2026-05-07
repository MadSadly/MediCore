/**
 * 안저 이미지 업로드 + 미리보기 (인라인 친화 에러 메시지)
 */

import { useState, useRef, useEffect } from "react";

export default function ImageUpload({ onImageSelect, disabled }) {
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleFile = (file) => {
    setError(null);
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/tiff"];
    if (!allowed.includes(file.type)) {
      setError("JPG, PNG, TIFF 형식만 업로드할 수 있습니다. 다른 파일은 선택할 수 없어요.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError("파일이 20MB를 넘습니다. 안저가 선명하게 보이도록 압축하거나 다른 사진을 올려 주세요.");
      return;
    }

    const url = URL.createObjectURL(file);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
    onImageSelect(file, url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const clearPreview = () => {
    setError(null);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    onImageSelect(null, null);
  };

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div
        className={`w-full border-2 border-dashed rounded-xl p-6 text-center transition-colors
          ${dragging ? "border-sky-400 bg-sky-500/10" : "border-slate-600 bg-slate-800/40"}
          ${disabled ? "opacity-50 pointer-events-none" : "cursor-pointer hover:border-sky-500/60"}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        {preview ? (
          <img src={preview} alt="미리보기" className="mx-auto max-h-64 rounded-lg object-contain" />
        ) : (
          <div className="text-slate-400">
            <p className="font-medium text-slate-200">안저 이미지를 드래그하거나 클릭하여 업로드</p>
            <p className="text-sm mt-1">JPG · PNG · TIFF / 최대 20MB</p>
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.tiff,.tif"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      {error && (
        <div
          role="alert"
          className="w-full rounded-lg border border-amber-500/40 bg-amber-950/35 px-3 py-2 text-left text-xs text-amber-100 leading-relaxed"
        >
          <span className="mr-1 text-amber-400">⚠</span>
          {error}
        </div>
      )}

      {preview && !disabled && (
        <button
          type="button"
          className="text-sm text-slate-400 hover:text-rose-400 underline"
          onClick={clearPreview}
        >
          이미지 제거
        </button>
      )}
    </div>
  );
}

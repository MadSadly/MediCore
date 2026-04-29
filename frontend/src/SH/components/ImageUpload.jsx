/**
 * 안저 이미지 업로드 + 미리보기
 */

import { useState, useRef, useEffect } from "react";

export default function ImageUpload({ onImageSelect, disabled }) {
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleFile = (file) => {
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/tiff"];
    if (!allowed.includes(file.type)) {
      alert("JPG, PNG, TIFF 파일만 업로드 가능합니다.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      alert("파일 크기는 20MB 이하여야 합니다.");
      return;
    }
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
    onImageSelect(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const clearPreview = () => {
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    onImageSelect(null);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className={`w-full border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
          ${dragging ? "border-sky-400 bg-sky-500/10" : "border-slate-600 bg-slate-800/40"}
          ${disabled ? "opacity-50 pointer-events-none" : "hover:border-sky-500/60"}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        {preview ? (
          <img src={preview} alt="미리보기" className="mx-auto max-h-64 rounded-lg object-contain" />
        ) : (
          <div className="text-slate-400">
            <p className="text-4xl mb-2">👁️</p>
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
        onChange={(e) => handleFile(e.target.files[0])}
      />

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

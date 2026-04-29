/**
 * 안과 AI 분석 — POST /sh/analyze (SSE)
 * 프록시: /ai → AI 서버 (vite.config.js)
 */

const ANALYZE_URL = "/ai/sh/analyze";

function parseSseBlocks(buffer) {
  const events = [];
  const parts = buffer.split(/\n\n/);
  const rest = parts.pop() ?? "";
  for (const block of parts) {
    if (!block.trim()) continue;
    let eventType = "message";
    let dataStr = null;
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) eventType = line.slice(6).trim();
      else if (line.startsWith("data:")) dataStr = line.slice(5).trim();
    }
    if (dataStr) {
      try {
        events.push({ event: eventType, data: JSON.parse(dataStr) });
      } catch (e) {
        // 불완전·손상 JSON: 다음 청크와 합쳐진 뒤 재시도되거나, 해당 이벤트만 건너뜀
        console.warn("eyeApi: SSE JSON parse skipped", e?.message, dataStr.slice(0, 120));
      }
    }
  }
  return { events, rest };
}

/**
 * @param {File} file
 * @param {{ patientId: string, patientAge?: number|null, hasDiabetes: boolean, hasHypertension: boolean, clinicalNote?: string }} meta
 * @param {(event: string, data: object) => void} onEvent
 * @param {AbortSignal} [abortSignal]
 */
export async function analyzeEye(file, meta, onEvent, abortSignal) {
  const token = localStorage.getItem("token");
  const form = new FormData();
  form.append("file", file);
  form.append("patient_id", meta.patientId);
  if (meta.patientAge != null && meta.patientAge !== "") {
    form.append("patient_age", String(meta.patientAge));
  }
  form.append("has_diabetes", String(!!meta.hasDiabetes));
  form.append("has_hypertension", String(!!meta.hasHypertension));
  if (meta.clinicalNote) form.append("clinical_note", meta.clinicalNote);

  const fetchOpts = {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  };
  if (abortSignal) fetchOpts.signal = abortSignal;

  const res = await fetch(ANALYZE_URL, fetchOpts);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("스트림을 읽을 수 없습니다.");

  const decoder = new TextDecoder();
  let carry = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    carry += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseBlocks(carry);
    carry = rest;
    for (const { event, data } of events) {
      if (abortSignal?.aborted) return;
      onEvent(event, data);
    }
  }

  if (carry.trim() && !abortSignal?.aborted) {
    const { events } = parseSseBlocks(carry + "\n\n");
    for (const { event, data } of events) {
      if (abortSignal?.aborted) return;
      onEvent(event, data);
    }
  }
}

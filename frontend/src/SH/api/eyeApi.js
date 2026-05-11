/**
 * Eye AI analysis SSE client.
 *
 * 기본: 상대 경로 `/ai/sh/analyze` (nginx `ai-router` 등에서 /ai → AI로 프록시할 때).
 * 파트너 환경에서 vite 프록시를 못 쓸 때: `frontend/.env` 에
 *   VITE_SH_AI_ORIGIN=http://192.168.0.32:8000
 * 처럼 넣고 재시작하면 해당 호스트로 직접 요청합니다.
 */
function resolveAnalyzeUrl() {
  const raw =
    typeof import.meta !== "undefined" && import.meta.env?.VITE_SH_AI_ORIGIN
      ? String(import.meta.env.VITE_SH_AI_ORIGIN).trim()
      : "";
  if (!raw) return "/ai/sh/analyze";
  const base = raw.replace(/\/$/, "");
  return `${base}/ai/sh/analyze`;
}

function parseApiErrorMessage(rawText, status) {
  if (!rawText) return `Request failed (HTTP ${status})`;

  try {
    const parsed = JSON.parse(rawText);
    if (typeof parsed === "string") return parsed;
    if (parsed?.message) return parsed.message;
    if (parsed?.detail) return parsed.detail;
    return rawText;
  } catch {
    return rawText;
  }
}

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

  let res;
  try {
    res = await fetch(resolveAnalyzeUrl(), fetchOpts);
  } catch (err) {
    if (err?.name === "AbortError") throw err;
    throw new Error("Network connection failed. Check AI server status.");
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseApiErrorMessage(text, res.status));
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("Unable to read response stream.");

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

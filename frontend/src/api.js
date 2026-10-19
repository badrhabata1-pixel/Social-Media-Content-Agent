// Shared backend access for the UI. Override the address with VITE_API_URL in frontend/.env.
export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const BACKEND_UNREACHABLE = 'Could not reach the backend. Ensure app.py is running on port 8000.';

/** Parsed JSON body, or null when the response has none (e.g. a plain-text 500). */
export async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/** The most useful message from any backend error shape: { error: {message, hint} } or FastAPI's { detail }. */
export function apiErrorMessage(payload, status) {
  const detail = Array.isArray(payload?.detail) ? payload.detail[0]?.msg : payload?.detail;
  const error = payload?.error;
  return [error?.message, error?.hint].filter(Boolean).join(' ') || detail || `Request failed (HTTP ${status}).`;
}

/** File name of a generated image ("<id>.png") from its /images/... URL, or null. */
export function imageFilename(imageUrl) {
  if (!imageUrl) return null;
  try {
    return new URL(imageUrl).pathname.split('/').pop() || null;
  } catch {
    return null;
  }
}

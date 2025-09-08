import { API_URL } from "./config";

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function streamSSE(
  path: string,
  body: unknown,
  onChunk: (data: unknown) => void,
): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Stream failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    // SSE format: lines starting with 'data: '
    chunk
      .split(/\n\n/) // events separated by blank line
      .map((c) => c.trim())
      .filter(Boolean)
      .forEach((line) => {
        const m = line.match(/^data:\s*(.*)$/s);
        if (m) {
          try {
            const payload = JSON.parse(m[1]);
            onChunk(payload);
          } catch {
            // Some backends send dict-like string; try to eval minimally
            try {
              const safe = m[1].replace(/'/g, '"');
              const payload = JSON.parse(safe);
              onChunk(payload);
            } catch {
              // ignore non-JSON lines
            }
          }
        }
      });
  }
}

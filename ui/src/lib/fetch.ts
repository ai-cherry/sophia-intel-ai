export class FetchError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'FetchError';
  }
}

export async function fetchJSON<T = any>(
  url: string,
  init: RequestInit = {},
  retries = 3,
  base?: string
): Promise<T> {
  const abs = `${base ?? ''}${url}`;
  let err: any;
  
  for (let i = 0; i <= retries; i++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout for JSON
      
      const res = await fetch(abs, {
        ...init,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...init.headers,
        },
      });
      
      clearTimeout(timeout);
      
      if (!res.ok) {
        throw new FetchError(res.status, `HTTP ${res.status}: ${res.statusText}`);
      }
      
      return await res.json();
    } catch (e) {
      err = e;
      if (i < retries) {
        // Exponential backoff with jitter
        await new Promise(r => setTimeout(r, 200 * (2 ** i) + Math.random() * 120));
      }
    }
  }
  
  throw err;
}
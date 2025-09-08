/*
  Typed API client
  - Wraps fetch with JSON parsing and error normalization
  - AbortController support
  - Helper methods: get/post
*/

export interface ApiError {
  status: number;
  message: string;
  details?: unknown;
}

export interface RequestOptions extends RequestInit {
  signal?: AbortSignal;
  headers?: Record<string, string>;
  category?: string; // for telemetry
}

export class ApiClient {
  constructor(private baseUrl: string, private onTiming?: (category: string, ms: number) => void) {}

  async request<T>(path: string, opts?: RequestOptions): Promise<T> {
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;
    const t0 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const res = await fetch(url, {
      ...opts,
      headers: {
        'Content-Type': 'application/json',
        ...(opts?.headers || {}),
      },
    });
    const t1 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    if (this.onTiming && opts?.category) {
      try { this.onTiming(opts.category, t1 - t0); } catch {}
    }
    const text = await res.text();
    const tryJson = () => {
      try {
        return text ? JSON.parse(text) : null;
      } catch {
        return null;
      }
    };
    const data = tryJson();
    if (!res.ok) {
      const err: ApiError = {
        status: res.status,
        message: (data && (data.message || data.error)) || res.statusText || 'Request failed',
        details: data || text,
      };
      throw err;
    }
    return (data ?? (text as unknown)) as T;
  }

  get<T>(path: string, opts?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...opts, method: 'GET' });
  }

  post<T, B = unknown>(path: string, body?: B, opts?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...opts, method: 'POST', body: body ? JSON.stringify(body) : undefined });
  }
}
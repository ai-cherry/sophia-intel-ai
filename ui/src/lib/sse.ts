import { StreamResponse } from './types';

export interface StreamOptions extends RequestInit {
  onToken?: (token: string) => void;
  onDone?: (final?: any) => void;
  onError?: (error: any) => void;
  timeout?: number;
}

export async function streamText(
  url: string,
  options: StreamOptions = {}
): Promise<void> {
  const {
    onToken = () => {},
    onDone = () => {},
    onError = () => {},
    timeout = Number(process.env.NEXT_PUBLIC_STREAM_TIMEOUT_MS) || 600000,
    ...fetchOptions
  } = options;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const res = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        ...fetchOptions.headers,
        'Accept': 'text/event-stream',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim()) continue;
        
        if (line.startsWith('data: ')) {
          const payload = line.slice(6).trim();
          if (!payload) continue;
          
          if (payload === '[DONE]') {
            onDone();
            return;
          }
          
          try {
            const obj: StreamResponse = JSON.parse(payload);
            if (obj.token) onToken(obj.token);
            if (obj.final) onDone(obj.final);
            if (obj.error) onError(new Error(obj.error));
          } catch {
            // Treat as plain text token
            onToken(payload);
          }
        }
      }
    }
    
    onDone();
  } catch (e) {
    onError(e);
  }
}
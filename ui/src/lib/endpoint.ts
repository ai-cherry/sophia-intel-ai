export const DEFAULT_ENDPOINT = process.env.NEXT_PUBLIC_DEFAULT_ENDPOINT ?? 'http://localhost:7777';
const KEY = 'slim-agno-endpoint';

export const getEndpoint = (): string => {
  if (typeof window === 'undefined') return DEFAULT_ENDPOINT;
  try {
    return localStorage.getItem(KEY) || DEFAULT_ENDPOINT;
  } catch {
    return DEFAULT_ENDPOINT;
  }
};

export const setEndpoint = (url: string): void => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(KEY, url);
  } catch (e) {
    console.warn('Failed to save endpoint:', e);
  }
};
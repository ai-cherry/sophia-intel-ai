/*
  RealtimeManager
  - Centralizes WebSocket/SSE connections
  - Pub/sub API with typed events
  - Reconnection with exponential backoff and jitter
  - Auth token injection via header param

  Non-breaking: nothing imports this yet. Wire up incrementally.
*/

export type RealtimeEventType =
  | 'chat.delta'
  | 'chat.complete'
  | 'swarm.update'
  | 'metrics.update'
  | 'system.error'
  | 'system.info';

export interface RealtimeEvent<T = unknown> {
  type: RealtimeEventType;
  payload: T;
  ts?: number;
}

type Handler<T = any> = (event: RealtimeEvent<T>) => void;

export interface RealtimeOptions {
  protocol?: 'ws' | 'sse';
  token?: string;
  backoffBaseMs?: number; // default 500ms
  backoffMaxMs?: number; // default 8000ms
}

export class RealtimeManager {
  private url: string;
  private opts: Required<Pick<RealtimeOptions, 'protocol' | 'backoffBaseMs' | 'backoffMaxMs'>> & { token?: string };
  private ws?: WebSocket;
  private sse?: EventSource;
  private handlers: Map<RealtimeEventType, Set<Handler>> = new Map();
  private reconnectAttempts = 0;
  private closedByUser = false;

  constructor(url: string, opts?: RealtimeOptions) {
    this.url = url;
    this.opts = {
      protocol: opts?.protocol ?? 'ws',
      token: opts?.token,
      backoffBaseMs: opts?.backoffBaseMs ?? 500,
      backoffMaxMs: opts?.backoffMaxMs ?? 8000,
    };
  }

  setAuthToken(token?: string) {
    this.opts.token = token;
  }

  on<T = any>(type: RealtimeEventType, handler: Handler<T>) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler as Handler);
    return () => this.off(type, handler);
  }

  off<T = any>(type: RealtimeEventType, handler: Handler<T>) {
    this.handlers.get(type)?.delete(handler as Handler);
  }

  private emit<T = any>(evt: RealtimeEvent<T>) {
    const subs = this.handlers.get(evt.type);
    if (!subs) return;
    for (const fn of subs) fn(evt);
  }

  async connect() {
    this.closedByUser = false;
    this.reconnectAttempts = 0;
    if (this.opts.protocol === 'ws') this.connectWS();
    else this.connectSSE();
  }

  close() {
    this.closedByUser = true;
    this.ws?.close();
    this.sse?.close();
  }

  // ---- WebSocket implementation ----
  private connectWS() {
    const url = new URL(this.url);
    if (this.opts.token) url.searchParams.set('auth', this.opts.token);
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit({ type: 'system.info', payload: { msg: 'ws_open' }, ts: Date.now() });
    };
    this.ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data && data.type) this.emit({ type: data.type, payload: data.payload, ts: Date.now() });
      } catch (e) {
        this.emit({ type: 'system.error', payload: { err: 'bad_json', raw: ev.data }, ts: Date.now() });
      }
    };
    this.ws.onclose = () => this.scheduleReconnect('ws');
    this.ws.onerror = () => this.scheduleReconnect('ws');
  }

  // ---- SSE implementation ----
  private connectSSE() {
    const url = new URL(this.url);
    if (this.opts.token) url.searchParams.set('auth', this.opts.token);
    this.sse = new EventSource(url);
    this.sse.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit({ type: 'system.info', payload: { msg: 'sse_open' }, ts: Date.now() });
    };
    this.sse.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data && data.type) this.emit({ type: data.type, payload: data.payload, ts: Date.now() });
      } catch (e) {
        this.emit({ type: 'system.error', payload: { err: 'bad_json', raw: ev.data }, ts: Date.now() });
      }
    };
    this.sse.onerror = () => this.scheduleReconnect('sse');
  }

  private scheduleReconnect(kind: 'ws' | 'sse') {
    if (this.closedByUser) return;
    const attempt = ++this.reconnectAttempts;
    const base = this.opts.backoffBaseMs;
    const max = this.opts.backoffMaxMs;
    const delay = Math.min(max, base * Math.pow(2, attempt - 1)) + Math.random() * 100;
    setTimeout(() => {
      if (kind === 'ws') this.connectWS();
      else this.connectSSE();
    }, delay);
  }

  // ---- Send payloads (WS only) ----
  send(type: string, payload: unknown) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
    this.ws.send(JSON.stringify({ type, payload }));
    return true;
  }
}

"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };

function genId() {
  return Math.random().toString(36).slice(2);
}

export default function SophiaChat() {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [startMeta, setStartMeta] = useState<any>(null);
  const [metrics, setMetrics] = useState<{ tokens?: number; cost?: number }>({});
  const evtSrc = useRef<EventSource | null>(null);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("sophia-session") : null;
    const sid = saved || genId();
    setSessionId(sid);
    if (!saved && typeof window !== "undefined") localStorage.setItem("sophia-session", sid);
  }, []);

  const send = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const payload = {
      message: input.trim(),
      sessionId,
      context: { path: typeof window !== "undefined" ? window.location.pathname : "/" },
    };
    setMessages((m) => [...m, { role: "user", content: input.trim() }]);
    setInput("");
    setStreaming(true);

    // Start SSE handshake to get stream URL
    const resp = await fetch("/api/sophia/chat/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      setStreaming(false);
      setMessages((m) => [...m, { role: "assistant", content: "Error starting stream." }]);
      return;
    }
    const { stream_url } = await resp.json();
    const url = stream_url || "/events"; // fallback
    const es = new EventSource(url);
    evtSrc.current = es;
    let buffer = "";
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data?.data?.type === "start" || data?.type === "start") {
          const meta = data?.data?.metadata || data?.metadata;
          if (meta) setStartMeta(meta);
        }
        const meta = data?.data?.metadata || data?.metadata;
        if (meta && (meta.tokens || meta.cost)) {
          setMetrics((m) => ({ tokens: meta.tokens ?? m.tokens, cost: meta.cost ?? m.cost }));
        }
        if (data?.data?.data?.content) {
          buffer += data.data.data.content;
          setMessages((m) => {
            const last = m[m.length - 1];
            if (last && last.role === "assistant") {
              const copy = m.slice();
              copy[copy.length - 1] = { role: "assistant", content: buffer };
              return copy;
            }
            return [...m, { role: "assistant", content: buffer }];
          });
        }
      } catch (e) {
        // ignore parse errors
      }
    };
    es.onerror = () => {
      es.close();
      evtSrc.current = null;
      setStreaming(false);
    };
  }, [input, sessionId, streaming]);

  return (
    <div className="fixed bottom-4 right-4 z-50" data-testid="sophia-chat">
      {open && (
        <div className="w-80 h-96 border rounded shadow bg-white flex flex-col">
          <div className="px-3 py-2 border-b flex items-center justify-between">
            <div className="font-medium">Sophia</div>
            <button className="text-sm" onClick={() => setOpen(false)}>
              Close
            </button>
          </div>
          {startMeta && (
            <div className="px-3 py-1 text-xs text-gray-600 border-b flex items-center gap-2">
              <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5">session: {sessionId.slice(0,6)}</span>
              {startMeta.correlation_id && (
                <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5">cid: {String(startMeta.correlation_id).slice(0,6)}</span>
              )}
              {typeof metrics.tokens === 'number' && (
                <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5">tokens: {metrics.tokens}</span>
              )}
              {typeof metrics.cost === 'number' && (
                <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5">cost: ${metrics.cost.toFixed(4)}</span>
              )}
            </div>
          )}
          <div className="flex-1 overflow-auto p-3 space-y-2">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div className={"inline-block px-2 py-1 rounded " + (m.role === "user" ? "bg-blue-100" : "bg-gray-100")}>{m.content}</div>
              </div>
            ))}
          </div>
          <div className="p-2 border-t flex gap-2">
            <input
              data-testid="sophia-input"
              className="flex-1 border rounded px-2 py-1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Sophia..."
              onKeyDown={(e) => {
                if (e.key === "Enter") send();
              }}
            />
            <button className="border rounded px-3" onClick={send} disabled={streaming}>
              Send
            </button>
          </div>
        </div>
      )}
      {!open && (
        <button data-testid="sophia-chat-toggle" className="border rounded-full px-4 py-2 bg-white shadow" onClick={() => setOpen(true)}>
          Chat with Sophia
        </button>
      )}
    </div>
  );
}

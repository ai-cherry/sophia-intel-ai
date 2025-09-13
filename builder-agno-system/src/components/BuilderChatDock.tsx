"use client";
import React, { useState } from "react";

interface Message { role: "user" | "assistant"; content: string }

export const BuilderChatDock: React.FC = () => {
  const [open, setOpen] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const runTeam = async (text: string) => {
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/builder/team/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: "default", task: text })
      });
      const data = await res.json();
      const summary = data?.result?.summary || "Processed";
      setMessages(prev => [...prev, { role: "assistant", content: summary }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${e?.message || e}` }]);
    } finally {
      setBusy(false);
    }
  };

  const onSend = async () => {
    const text = input.trim();
    if (!text) return;
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setInput("");
    await runTeam(text);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-gray-800 text-white rounded-lg shadow-xl w-96 border border-gray-700">
        <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
          <div className="font-semibold text-sm">Sophia Engineer (Builder)</div>
          <button className="text-xs text-gray-300 hover:text-white" onClick={() => setOpen(!open)}>
            {open ? "Hide" : "Show"}
          </button>
        </div>
        {open && (
          <div className="p-3">
            <div className="h-56 overflow-y-auto space-y-2 mb-3 bg-gray-900 rounded p-2 border border-gray-700">
              {messages.length === 0 ? (
                <div className="text-xs text-gray-400">Ask me to plan or generate code. I use Builder teams only.</div>
              ) : messages.map((m, i) => (
                <div key={i} className="text-xs"><span className="font-semibold">{m.role === 'user' ? 'You' : 'Agent'}</span>: {m.content}</div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                className="flex-1 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs focus:outline-none"
                placeholder="Describe your coding task..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !busy && onSend()}
                disabled={busy}
              />
              <button
                className={`px-3 py-1 rounded text-xs ${busy ? 'bg-gray-600' : 'bg-purple-600 hover:bg-purple-700'} text-white`}
                onClick={onSend}
                disabled={busy}
              >
                {busy ? '...' : 'Send'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BuilderChatDock;


"use client";
import React, { useState } from "react";

type ChatMessage = { role: "user" | "assistant"; content: string };

export const SophiaDock: React.FC = () => {
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const handleChatMessage = async () => {
    if (!input.trim()) return;
    const next = [...chatHistory, { role: "user", content: input }];
    setChatHistory(next);
    setInput("");
    // TODO: call backend chat endpoint
  };

  const handleVoiceCommand = async () => {
    // TODO: wire voice command handler
    setIsVoiceActive(!isVoiceActive);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
      <div className="bg-white/90 dark:bg-neutral-900/90 rounded-md shadow-xl border p-2 max-h-80 overflow-y-auto">
        {chatHistory.length === 0 ? (
          <div className="text-sm text-neutral-500">Ask Sophia anything…</div>
        ) : (
          chatHistory.map((m, i) => (
            <div key={i} className="text-sm my-1">
              <span className="font-semibold mr-1">{m.role === "user" ? "You" : "Sophia"}:</span>
              <span>{m.content}</span>
            </div>
          ))
        )}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded px-2 py-1 text-sm"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleChatMessage()}
        />
        <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm" onClick={handleChatMessage}>
          Send
        </button>
        <button
          className={`px-3 py-1 rounded text-sm ${isVoiceActive ? "bg-red-600 text-white" : "bg-neutral-200"}`}
          onClick={handleVoiceCommand}
          title="Toggle Voice"
        >
          🎤
        </button>
      </div>
    </div>
  );
};

export default SophiaDock;


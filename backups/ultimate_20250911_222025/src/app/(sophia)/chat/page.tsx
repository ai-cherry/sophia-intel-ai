"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL, ENABLE_MEMORY } from "@/lib/config";
import { streamSSE } from "@/lib/api";

type Message = { 
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: {
    persona?: string;
    context?: string[];
    timestamp?: string;
  };
};

type Persona = {
  id: string;
  name: string;
  icon: string;
  description: string;
  systemPrompt: string;
};

const PERSONAS: Persona[] = [
  {
    id: "analyst",
    name: "Revenue Analyst",
    icon: "📊",
    description: "Deep dive into metrics and pipeline analysis",
    systemPrompt: "You are Sophia, a revenue analyst expert. Focus on data-driven insights, conversion metrics, and pipeline health."
  },
  {
    id: "sales-coach",
    name: "Sales Coach",
    icon: "🎯",
    description: "Deal strategy and call coaching from Gong insights",
    systemPrompt: "You are Sophia, a sales coaching expert. Analyze Gong calls, provide deal strategies, and coach on objection handling."
  },
  {
    id: "ops-assistant",
    name: "Ops Assistant",
    icon: "⚙️",
    description: "Process automation and workflow optimization",
    systemPrompt: "You are Sophia, an operations assistant. Help streamline processes, automate workflows, and resolve blockers."
  },
  {
    id: "strategic-advisor",
    name: "Strategic Advisor",
    icon: "🧠",
    description: "High-level business strategy and planning",
    systemPrompt: "You are Sophia, a strategic business advisor. Provide executive insights, market analysis, and strategic recommendations."
  }
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<Persona>(PERSONAS[0]);
  const [context, setContext] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  // Bridge recording state to global binder for handlers defined below
  useEffect(() => {
    (window as any).bindChatRecording?.(setIsRecording);
    const onTranscription = (e: any) => {
      const text = e?.detail?.text as string;
      if (text) {
        setInput((prev) => (prev ? prev + " " + text : text));
      }
    };
    window.addEventListener("chat-transcription", onTranscription as any);
    return () => window.removeEventListener("chat-transcription", onTranscription as any);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || streaming) return;
    
    const userMessage: Message = {
      role: "user",
      content: msg,
      metadata: {
        timestamp: new Date().toISOString()
      }
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setStreaming(true);
    
    // Add assistant message placeholder
    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      metadata: {
        persona: selectedPersona.name,
        context: context,
        timestamp: new Date().toISOString()
      }
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Optionally enrich context from memory
      if (ENABLE_MEMORY) {
        try {
          const resp = await fetch(`${API_URL}/api/memory/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: msg, user_id: 'demo' })
          });
          const data = await resp.json();
          const hits: string[] = (data?.results || []).slice(0, 5).map((r: any) => {
            try {
              if (r?.content?.text) return r.content.text as string;
              return typeof r === 'string' ? r : JSON.stringify(r).slice(0, 400);
            } catch { return ''; }
          }).filter(Boolean);
          if (hits.length) {
            setContext(hits);
          }
        } catch {}
      }
      const body = {
        message: msg,
        system_prompt: selectedPersona.systemPrompt,
        context: context.join("\n"),
        temperature: 0.4,
        max_tokens: 1500,
        metadata: {
          source: "sophia-ui",
          persona: selectedPersona.id
        }
      };

      for await (const chunkData of streamSSE("/api/orchestration/chat/stream", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })) {
        try {
          const chunk = JSON.parse(chunkData);
          if (chunk?.content) {
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg && lastMsg.role === "assistant") {
                lastMsg.content += chunk.content;
              }
              return updated;
            });
            if (ttsEnabled && chunk?.is_final && chunk?.content) {
              try {
                fetch(`${API_URL}/api/voice/synthesize`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ text: chunk.content, system: "sophia", persona: "smart" })
                }).then(r => r.json()).then(d => {
                  if (d?.audio_base64) {
                    const audio = new Audio(`data:audio/mpeg;base64,${d.audio_base64}`);
                    audio.play().catch(() => {});
                  }
                }).catch(() => {});
              } catch {}
            }
        } catch (parseError) {
          // Skip invalid JSON chunks
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          lastMsg.content = `⚠️ Error: ${(e as Error).message}`;
        }
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }, [input, streaming, selectedPersona, context]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        // TODO: Send to speech-to-text endpoint
        setIsRecording(false);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  }, [isRecording]);

  const loadContext = useCallback(async (type: string) => {
    // Simulate loading context from different sources
    const contexts: Record<string, string[]> = {
      "recent-calls": ["Latest Gong call with Acme Corp discussed pricing concerns", "Follow-up needed on security requirements"],
      "pipeline": ["5 deals in closing stage worth $450K", "2 deals at risk due to budget constraints"],
      "tasks": ["Review contract for TechCo deal", "Schedule demo with FinanceApp team"],
    };
    setContext(contexts[type] || []);
  }, []);

  return (
    <div className="h-full flex">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold">Sophia Chat</h1>
              <div className="flex gap-2">
                {PERSONAS.map((persona) => (
                  <button
                    key={persona.id}
                    onClick={() => setSelectedPersona(persona)}
                    className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5 transition-colors ${
                      selectedPersona.id === persona.id
                        ? "bg-blue-100 text-blue-700 border-blue-200 border"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    <span>{persona.icon}</span>
                    <span>{persona.name}</span>
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={() => setShowContext(!showContext)}
              className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm hover:bg-gray-200"
            >
              {showContext ? "Hide" : "Show"} Context
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-2">{selectedPersona.description}</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Start a conversation with Sophia</p>
              <div className="flex justify-center gap-2 flex-wrap">
                <button
                  onClick={() => send("What are my top deals this week?")}
                  className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50"
                >
                  💰 Top deals this week
                </button>
                <button
                  onClick={() => send("Analyze recent Gong calls")}
                  className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50"
                >
                  📞 Recent call insights
                </button>
                <button
                  onClick={() => send("What tasks need attention?")}
                  className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50"
                >
                  ✅ Priority tasks
                </button>
                <button
                  onClick={() => send("Show pipeline health metrics")}
                  className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50"
                >
                  📊 Pipeline health
                </button>
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`max-w-3xl ${msg.role === "user" ? "order-2" : "order-1"}`}>
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{selectedPersona.icon}</span>
                    <span className="text-sm text-gray-600">{msg.metadata?.persona || "Sophia"}</span>
                    {msg.metadata?.context && msg.metadata.context.length > 0 && (
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {msg.metadata.context.length} context items
                      </span>
                    )}
                  </div>
                )}
                <div
                  className={`px-4 py-2.5 rounded-lg ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border text-gray-800"
                  }`}
                >
                  <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
                </div>
                {msg.metadata?.timestamp && (
                  <p className="text-xs text-gray-400 mt-1 px-1">
                    {new Date(msg.metadata.timestamp).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t bg-white p-4">
          <div className="flex gap-2 items-center">
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isRecording
                  ? "bg-red-600 text-white animate-pulse"
                  : "bg-gray-100 hover:bg-gray-200"
              }`}
            >
              {isRecording ? "🔴 Recording" : "🎤 Hold to Talk"}
            </button>
            <input
              className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Ask ${selectedPersona.name} anything...`}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              disabled={streaming}
            />
            <button
              onClick={() => send()}
              disabled={streaming || !input.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {streaming ? "..." : "Send"}
            </button>
            <label className="text-sm ml-2 inline-flex items-center gap-1">
              <input type="checkbox" checked={ttsEnabled} onChange={(e) => setTtsEnabled(e.target.checked)} />
              TTS
            </label>
          </div>
        </div>
      </div>

      {/* Context Sidebar */}
      {showContext && (
        <div className="w-80 border-l bg-white p-4 space-y-4">
          <h2 className="font-semibold">Context Sources</h2>
          
          <div className="space-y-2">
            <button
              onClick={() => loadContext("recent-calls")}
              className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <p className="font-medium text-sm">📞 Recent Gong Calls</p>
              <p className="text-xs text-gray-500">Load call summaries</p>
            </button>
            
            <button
              onClick={() => loadContext("pipeline")}
              className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <p className="font-medium text-sm">🎯 Active Pipeline</p>
              <p className="text-xs text-gray-500">Current deals & status</p>
            </button>
            
            <button
              onClick={() => loadContext("tasks")}
              className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <p className="font-medium text-sm">✅ Open Tasks</p>
              <p className="text-xs text-gray-500">Priority action items</p>
            </button>
          </div>

          {context.length > 0 && (
            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-2">Active Context ({context.length})</p>
              <div className="space-y-1">
                {context.map((item, idx) => (
                  <div key={idx} className="text-xs bg-blue-50 p-2 rounded">
                    {item}
                  </div>
                ))}
              </div>
              <button
                onClick={() => setContext([])}
                className="mt-2 text-xs text-red-600 hover:underline"
              >
                Clear Context
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- Audio Recording Helpers (Web Audio API / MediaRecorder) ---

async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = (reader.result as string) || "";
      const base64 = result.split(",")[1] || ""; // strip data: prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function startRecording(this: unknown) {
  (async () => {
    try {
      // @ts-ignore
      const setIsRecording = this?.setIsRecording || (window as any).setIsRecording;
    } catch {}
  })();
}

// Attach functions on component scope by augmenting window (since we’re in page component)
// This is a pragmatic approach to bind handlers without extra refactoring.
// We rely on the closures defined below to access state setters.
(function bindRecording() {
  let setIsRecordingFn: (b: boolean) => void;
  let mediaRecorder: MediaRecorder | null = null;
  let chunks: BlobPart[] = [];
  const w = window as any;
  w.bindChatRecording = (setIsRecordingCb: unknown) => { setIsRecordingFn = setIsRecordingCb; };
  w.startRecording = async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunks = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data?.size) chunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        try {
          const blob = new Blob(chunks, { type: "audio/webm" });
          const base64 = await blobToBase64(blob);
          const res = await fetch(`${API_URL}/api/voice/transcribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ audio_base64: base64, audio_format: "webm", system: "sophia" })
          });
          const data = await res.json();
          const text = (data?.text || "").trim();
          if (text) {
            const ev = new CustomEvent("chat-transcription", { detail: { text } });
            window.dispatchEvent(ev);
          }
        } catch {}
        if (mediaRecorder) {
          mediaRecorder.stream.getTracks().forEach((t) => t.stop());
          mediaRecorder = null;
        }
      };
      mediaRecorder.start();
      setIsRecordingFn?.(true);
    } catch {
      setIsRecordingFn?.(false);
    }
  };
  w.stopRecording = function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      setIsRecordingFn?.(false);
    }
  };
})();

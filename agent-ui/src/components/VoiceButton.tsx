"use client";
import { useEffect, useRef, useState } from "react";

type Props = {
  onTranscription: (text: string) => void;
  system?: "sophia" | "artemis";
};

export default function VoiceButton({ onTranscription, system = "sophia" }: Props) {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
    chunksRef.current = [];
    mr.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };
    mr.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const base64 = await blobToBase64(blob);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003"}/api/voice/transcribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ audio_base64: base64, audio_format: "webm", system }),
        });
        const data = await res.json();
        if (data?.success && data?.text) onTranscription(data.text);
        else onTranscription(data?.text || "");
      } catch (e) {
        console.error("Transcription failed", e);
      }
    };
    mediaRecorderRef.current = mr;
    mr.start();
    setRecording(true);
  }

  function stop() {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== "inactive") {
      mr.stop();
      mr.stream.getTracks().forEach((t) => t.stop());
    }
    setRecording(false);
  }

  return (
    <button
      className={`border rounded-md px-3 py-2 ${recording ? "bg-red-600 text-white" : "bg-gray-100"}`}
      onMouseDown={start}
      onMouseUp={stop}
      onTouchStart={(e) => { e.preventDefault(); start(); }}
      onTouchEnd={(e) => { e.preventDefault(); stop(); }}
      aria-pressed={recording}
    >
      {recording ? "Release to stop" : "Hold to talk"}
    </button>
  );
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const res = (reader.result as string) || "";
      const base64 = res.split(",")[1] || ""; // remove data: prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}


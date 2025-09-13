"use client";
import React, { useState, useRef, useEffect } from "react";

interface VoiceControlProps {
  onTranscript?: (text: string) => void;
  onResponse?: (text: string) => void;
}

export const VoiceControl: React.FC<VoiceControlProps> = ({ onTranscript, onResponse }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState("Ready");
  const [isConnected, setIsConnected] = useState(false);
  
  const ws = useRef<WebSocket | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const audioQueue = useRef<ArrayBuffer[]>([]);
  
  const VOICE_SERVER_URL = process.env.NEXT_PUBLIC_VOICE_SERVER_URL || "ws://localhost:8090/ws/voice";
  
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (mediaRecorder.current) {
        mediaRecorder.current.stop();
      }
    };
  }, []);
  
  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    
    ws.current = new WebSocket(VOICE_SERVER_URL);
    
    ws.current.onopen = () => {
      setIsConnected(true);
      setStatus("Connected");
    };
    
    ws.current.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Audio data from TTS
        const arrayBuffer = await event.data.arrayBuffer();
        audioQueue.current.push(arrayBuffer);
        playAudio();
      } else {
        // JSON message
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "transcript") {
            setTranscript(data.text);
            if (data.is_final && onTranscript) {
              onTranscript(data.text);
            }
          } else if (data.type === "response") {
            setStatus("Response received");
            if (onResponse) {
              onResponse(data.text);
            }
          }
        } catch (e) {
          console.error("Failed to parse message:", e);
        }
      }
    };
    
    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setStatus("Connection error");
      setIsConnected(false);
    };
    
    ws.current.onclose = () => {
      setIsConnected(false);
      setStatus("Disconnected");
    };
  };
  
  const startListening = async () => {
    try {
      // Connect WebSocket if needed
      if (!isConnected) {
        connectWebSocket();
        // Wait for connection
        await new Promise((resolve) => {
          const checkConnection = setInterval(() => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              clearInterval(checkConnection);
              resolve(true);
            }
          }, 100);
        });
      }
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          sampleSize: 16
        } 
      });
      
      // Create audio context for processing
      audioContext.current = new AudioContext({ sampleRate: 16000 });
      const source = audioContext.current.createMediaStreamSource(stream);
      const processor = audioContext.current.createScriptProcessor(2048, 1, 1);
      
      processor.onaudioprocess = (e) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = convertFloat32ToPCM16(inputData);
          ws.current.send(pcm16);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.current.destination);
      
      setIsListening(true);
      setStatus("Listening...");
      
    } catch (error) {
      console.error("Failed to start listening:", error);
      setStatus("Microphone access denied");
    }
  };
  
  const stopListening = () => {
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();
      mediaRecorder.current = null;
    }
    
    if (audioContext.current) {
      audioContext.current.close();
      audioContext.current = null;
    }
    
    setIsListening(false);
    setStatus("Ready");
  };
  
  const convertFloat32ToPCM16 = (float32Array: Float32Array): ArrayBuffer => {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    
    return buffer;
  };
  
  const playAudio = async () => {
    if (audioQueue.current.length === 0) return;
    
    const audioBuffer = audioQueue.current.shift()!;
    const audioCtx = new AudioContext();
    
    try {
      const decodedData = await audioCtx.decodeAudioData(audioBuffer);
      const source = audioCtx.createBufferSource();
      source.buffer = decodedData;
      source.connect(audioCtx.destination);
      source.start();
    } catch (e) {
      console.error("Failed to play audio:", e);
    }
  };
  
  return (
    <div className="fixed bottom-20 right-4 z-40">
      <div className="bg-gray-800 text-white rounded-lg shadow-xl p-4 border border-gray-700">
        <div className="flex items-center gap-4 mb-3">
          <button
            onClick={isListening ? stopListening : startListening}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isListening 
                ? "bg-red-600 hover:bg-red-700" 
                : "bg-green-600 hover:bg-green-700"
            }`}
          >
            {isListening ? "🎤 Stop" : "🎤 Start Voice"}
          </button>
          
          <div className="flex-1">
            <div className="text-xs text-gray-400">Status</div>
            <div className="text-sm font-medium">{status}</div>
          </div>
          
          <div className={`w-3 h-3 rounded-full ${
            isConnected ? "bg-green-500" : "bg-gray-500"
          }`} />
        </div>
        
        {transcript && (
          <div className="mt-2 p-2 bg-gray-900 rounded text-xs">
            <div className="text-gray-400 mb-1">Transcript:</div>
            <div>{transcript}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceControl;
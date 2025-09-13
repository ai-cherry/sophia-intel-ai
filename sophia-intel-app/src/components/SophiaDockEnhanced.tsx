"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";

type ChatMessage = { 
  role: "user" | "assistant"; 
  content: string;
  audio?: boolean;
};

type VoiceState = "idle" | "listening" | "processing" | "speaking" | "error";

interface WebRTCVoiceConfig {
  apiUrl: string;
  stunServers?: string[];
  turnServers?: { url: string; username?: string; credential?: string }[];
}

export const SophiaDockEnhanced: React.FC = () => {
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [useWebRTC, setUseWebRTC] = useState(true);
  
  // WebRTC refs
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const controlWsRef = useRef<WebSocket | null>(null);
  const audioWsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  
  // Voice Activity Detection
  const vadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const vadThreshold = 0.01;
  const vadEndDelay = 1000; // ms
  
  const config: WebRTCVoiceConfig = {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    stunServers: ["stun:stun.l.google.com:19302"]
  };

  // Initialize WebRTC
  const initializeWebRTC = useCallback(async () => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });
      localStreamRef.current = stream;
      
      // Create peer connection
      const pc = new RTCPeerConnection({
        iceServers: config.stunServers?.map(url => ({ urls: url })) || []
      });
      peerConnectionRef.current = pc;
      
      // Add local stream
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });
      
      // Handle remote stream (TTS audio)
      pc.ontrack = (event) => {
        if (event.track.kind === 'audio') {
          handleRemoteAudio(event.streams[0]);
        }
      };
      
      // Create offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      
      // Send offer to server
      const response = await fetch(`${config.apiUrl}/api/voice/webrtc/offer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: offer.sdp,
          session_id: sessionId || undefined
        })
      });
      
      const answer = await response.json();
      setSessionId(answer.session_id);
      
      // Set remote description
      await pc.setRemoteDescription(new RTCSessionDescription({
        type: 'answer',
        sdp: answer.sdp
      }));
      
      // Initialize control WebSocket
      initializeControlWebSocket(answer.session_id);
      
      return true;
    } catch (error) {
      console.error('WebRTC initialization failed:', error);
      setUseWebRTC(false);
      return false;
    }
  }, [sessionId, config]);
  
  // Initialize WebSocket fallback
  const initializeWebSocketFallback = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });
      localStreamRef.current = stream;
      
      // Create audio WebSocket
      const ws = new WebSocket(`${config.apiUrl.replace('http', 'ws')}/api/voice/ws`);
      ws.binaryType = 'arraybuffer';
      
      ws.onopen = () => {
        console.log('WebSocket audio connected');
        setVoiceState("idle");
      };
      
      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Audio data from TTS
          playAudioChunk(event.data);
        } else {
          // JSON message (transcripts)
          const data = JSON.parse(event.data);
          handleTranscript(data);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setVoiceState("error");
      };
      
      audioWsRef.current = ws;
      
      // Setup audio processing
      setupAudioProcessing(stream, ws);
      
      return true;
    } catch (error) {
      console.error('WebSocket fallback failed:', error);
      setVoiceState("error");
      return false;
    }
  }, [config]);
  
  // Initialize control WebSocket
  const initializeControlWebSocket = (sessionId: string) => {
    const ws = new WebSocket(`${config.apiUrl.replace('http', 'ws')}/api/voice/control`);
    
    ws.onopen = () => {
      // Send session ID
      ws.send(JSON.stringify({ session_id: sessionId }));
      console.log('Control WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleControlMessage(data);
    };
    
    controlWsRef.current = ws;
  };
  
  // Setup audio processing for WebSocket
  const setupAudioProcessing = (stream: MediaStream, ws: WebSocket) => {
    const audioContext = new AudioContext({ sampleRate: 16000 });
    audioContextRef.current = audioContext;
    
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    processor.onaudioprocess = (event) => {
      if (!isVoiceActive || ws.readyState !== WebSocket.OPEN) return;
      
      const inputData = event.inputBuffer.getChannelData(0);
      
      // Simple VAD
      const energy = inputData.reduce((sum, val) => sum + Math.abs(val), 0) / inputData.length;
      
      if (energy > vadThreshold) {
        // Voice detected
        if (vadTimeoutRef.current) {
          clearTimeout(vadTimeoutRef.current);
          vadTimeoutRef.current = null;
        }
        
        if (voiceState === "idle") {
          setVoiceState("listening");
          sendControlMessage("bargeIn");
        }
        
        // Convert to PCM16
        const pcm16 = floatTo16BitPCM(inputData);
        ws.send(pcm16);
      } else if (voiceState === "listening") {
        // Start end-of-speech timer
        if (!vadTimeoutRef.current) {
          vadTimeoutRef.current = setTimeout(() => {
            setVoiceState("processing");
            vadTimeoutRef.current = null;
          }, vadEndDelay);
        }
      }
    };
    
    source.connect(processor);
    processor.connect(audioContext.destination);
  };
  
  // Handle remote audio stream
  const handleRemoteAudio = (stream: MediaStream) => {
    const audio = new Audio();
    audio.srcObject = stream;
    audio.play();
  };
  
  // Play audio chunk (for WebSocket fallback)
  const playAudioChunk = async (data: ArrayBuffer) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
    }
    
    const audioContext = audioContextRef.current;
    const audioBuffer = await audioContext.decodeAudioData(data);
    audioQueueRef.current.push(audioBuffer);
    
    if (!isPlayingRef.current) {
      playNextAudioChunk();
    }
  };
  
  // Play queued audio chunks
  const playNextAudioChunk = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setVoiceState("idle");
      return;
    }
    
    isPlayingRef.current = true;
    setVoiceState("speaking");
    
    const audioContext = audioContextRef.current!;
    const buffer = audioQueueRef.current.shift()!;
    const source = audioContext.createBufferSource();
    
    source.buffer = buffer;
    source.connect(audioContext.destination);
    source.onended = playNextAudioChunk;
    source.start();
  };
  
  // Handle transcript messages
  const handleTranscript = (data: any) => {
    if (data.type === "transcript_partial") {
      // Update UI with partial transcript
      console.log("Partial:", data.text);
    } else if (data.type === "transcript_final") {
      // Add to chat history
      setChatHistory(prev => [...prev, {
        role: "user",
        content: data.text,
        audio: true
      }]);
    }
  };
  
  // Handle control messages
  const handleControlMessage = (data: any) => {
    console.log("Control message:", data);
  };
  
  // Send control message
  const sendControlMessage = (type: string, data?: any) => {
    const ws = controlWsRef.current || audioWsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, data }));
    }
  };
  
  // Convert float32 to PCM16
  const floatTo16BitPCM = (float32Array: Float32Array): ArrayBuffer => {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buffer;
  };
  
  // Handle push-to-talk
  const handleVoiceToggle = async () => {
    if (!isVoiceActive) {
      // Start voice
      setIsVoiceActive(true);
      setVoiceState("idle");
      
      // Initialize voice system
      const success = useWebRTC 
        ? await initializeWebRTC()
        : await initializeWebSocketFallback();
        
      if (!success) {
        setIsVoiceActive(false);
        setVoiceState("error");
      }
    } else {
      // Stop voice
      setIsVoiceActive(false);
      setVoiceState("idle");
      
      // Stop barge-in if speaking
      if (voiceState === "speaking") {
        sendControlMessage("stopTTS");
        audioQueueRef.current = [];
      }
      
      // Cleanup
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }
      
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }
      
      if (controlWsRef.current) {
        controlWsRef.current.close();
        controlWsRef.current = null;
      }
      
      if (audioWsRef.current) {
        audioWsRef.current.close();
        audioWsRef.current = null;
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    }
  };
  
  // Handle chat message
  const handleChatMessage = async () => {
    if (!input.trim()) return;
    
    setChatHistory(prev => [...prev, { 
      role: "user", 
      content: input,
      audio: false
    }]);
    
    const message = input;
    setInput("");
    
    // Send to backend
    try {
      const response = await fetch(`${config.apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          history: chatHistory
        })
      });
      
      const data = await response.json();
      
      setChatHistory(prev => [...prev, {
        role: "assistant",
        content: data.response,
        audio: false
      }]);
      
      // If voice is active, synthesize response
      if (isVoiceActive) {
        sendControlMessage("synthesize", { text: data.response });
      }
    } catch (error) {
      console.error('Chat error:', error);
    }
  };
  
  // Voice state indicator
  const getVoiceStateIcon = () => {
    switch (voiceState) {
      case "listening": return "🎤 Listening...";
      case "processing": return "⏳ Processing...";
      case "speaking": return "🔊 Speaking...";
      case "error": return "❌ Error";
      default: return isVoiceActive ? "🎤 Ready" : "🎤";
    }
  };
  
  // Voice state color
  const getVoiceButtonClass = () => {
    if (voiceState === "error") return "bg-red-600 text-white";
    if (voiceState === "listening") return "bg-green-600 text-white animate-pulse";
    if (voiceState === "speaking") return "bg-blue-600 text-white";
    if (voiceState === "processing") return "bg-yellow-600 text-white";
    if (isVoiceActive) return "bg-purple-600 text-white";
    return "bg-neutral-200 dark:bg-neutral-700";
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-96">
      {/* Status Bar */}
      {isVoiceActive && (
        <div className="bg-white/90 dark:bg-neutral-900/90 rounded-md shadow-xl border px-3 py-1 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-medium">{voiceState.toUpperCase()}</span>
            <span className="text-neutral-500">
              {useWebRTC ? "WebRTC" : "WebSocket"} • Session: {sessionId.slice(0, 8)}
            </span>
          </div>
        </div>
      )}
      
      {/* Chat History */}
      <div className="bg-white/90 dark:bg-neutral-900/90 rounded-md shadow-xl border p-3 max-h-96 overflow-y-auto">
        {chatHistory.length === 0 ? (
          <div className="text-sm text-neutral-500">Ask Sophia anything...</div>
        ) : (
          chatHistory.map((msg, i) => (
            <div key={i} className="text-sm my-2">
              <div className="flex items-start gap-2">
                <span className="font-semibold">
                  {msg.role === "user" ? "You" : "Sophia"}
                  {msg.audio && " 🎤"}:
                </span>
                <span className="flex-1">{msg.content}</span>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Input Controls */}
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleChatMessage()}
          disabled={voiceState === "listening" || voiceState === "processing"}
        />
        <button 
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors" 
          onClick={handleChatMessage}
          disabled={!input.trim()}
        >
          Send
        </button>
        <button
          className={`px-4 py-2 rounded text-sm transition-all ${getVoiceButtonClass()}`}
          onClick={handleVoiceToggle}
          title={isVoiceActive ? "Stop Voice" : "Start Voice"}
        >
          {getVoiceStateIcon()}
        </button>
      </div>
      
      {/* Barge-in Control */}
      {isVoiceActive && voiceState === "speaking" && (
        <button
          className="w-full py-2 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition-colors"
          onClick={() => sendControlMessage("bargeIn")}
        >
          Stop & Speak (Barge-in)
        </button>
      )}
    </div>
  );
};

export default SophiaDockEnhanced;
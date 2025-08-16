import React, { useRef, useState, useCallback } from 'react';
import { Mic, MicOff, Square, Loader2, Volume2, AlertCircle } from 'lucide-react';

/**
 * VoiceCapture Component
 * Real voice recording with MediaRecorder → STT → Orchestration → TTS pipeline
 */
export default function VoiceCapture({ onTranscription, onResponse, className = "" }) {
  const mediaRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  
  const [state, setState] = useState('idle'); // idle, recording, transcribing, orchestrating, speaking
  const [error, setError] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setState('recording');
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      mediaRef.current = stream;
      chunksRef.current = [];
      
      // Create MediaRecorder
      const recorder = new MediaRecorder(stream, { 
        mimeType: 'audio/webm;codecs=opus' 
      });
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        await processRecording();
      };
      
      recorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setError(`Recording error: ${event.error.message}`);
        setState('idle');
      };
      
      recorderRef.current = recorder;
      recorder.start(1000); // Collect data every second
      
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError(`Microphone access denied: ${err.message}`);
      setState('idle');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
    }
    
    if (mediaRef.current) {
      mediaRef.current.getTracks().forEach(track => track.stop());
      mediaRef.current = null;
    }
  }, []);

  const processRecording = useCallback(async () => {
    try {
      setState('transcribing');
      
      // Create audio blob
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
      
      if (audioBlob.size === 0) {
        throw new Error('No audio data recorded');
      }
      
      // Send to STT endpoint
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice.webm');
      
      const sttResponse = await fetch('/api/speech/stt', {
        method: 'POST',
        body: formData
      });
      
      if (!sttResponse.ok) {
        const errorData = await sttResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `STT failed: ${sttResponse.status}`);
      }
      
      const sttData = await sttResponse.json();
      const transcribedText = sttData.text?.trim();
      
      if (!transcribedText) {
        throw new Error('No speech detected in audio');
      }
      
      setTranscription(transcribedText);
      onTranscription?.(transcribedText);
      
      // Send to orchestration
      setState('orchestrating');
      
      const orchestrationResponse = await fetch('/api/orchestration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          request_type: 'chat',
          payload: {
            message: transcribedText,
            voice_response: true
          }
        })
      });
      
      if (!orchestrationResponse.ok) {
        const errorData = await orchestrationResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `Orchestration failed: ${orchestrationResponse.status}`);
      }
      
      const orchestrationData = await orchestrationResponse.json();
      const responseText = orchestrationData.response || orchestrationData.result || 'No response received';
      
      setResponse(responseText);
      onResponse?.(responseText);
      
      // Convert response to speech
      setState('speaking');
      
      const ttsResponse = await fetch('/api/speech/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: responseText,
          speed: 1.0
        })
      });
      
      if (ttsResponse.ok) {
        const audioBlob = await ttsResponse.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          setState('idle');
        };
        
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          console.warn('TTS playback failed, but continuing...');
          setState('idle');
        };
        
        await audio.play();
      } else {
        console.warn('TTS failed, but continuing without audio');
        setState('idle');
      }
      
    } catch (err) {
      console.error('Voice processing error:', err);
      setError(err.message);
      setState('idle');
    }
  }, [onTranscription, onResponse]);

  const handleToggleRecording = useCallback(() => {
    if (state === 'recording') {
      stopRecording();
    } else if (state === 'idle') {
      startRecording();
    }
  }, [state, startRecording, stopRecording]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // State-based UI configuration
  const getStateConfig = () => {
    switch (state) {
      case 'recording':
        return {
          icon: Square,
          label: 'Stop Recording',
          color: 'bg-red-500 hover:bg-red-600',
          pulse: true
        };
      case 'transcribing':
        return {
          icon: Loader2,
          label: 'Transcribing...',
          color: 'bg-blue-500',
          spin: true,
          disabled: true
        };
      case 'orchestrating':
        return {
          icon: Loader2,
          label: 'Processing...',
          color: 'bg-purple-500',
          spin: true,
          disabled: true
        };
      case 'speaking':
        return {
          icon: Volume2,
          label: 'Speaking...',
          color: 'bg-green-500',
          pulse: true,
          disabled: true
        };
      default:
        return {
          icon: Mic,
          label: 'Start Recording',
          color: 'bg-blue-500 hover:bg-blue-600'
        };
    }
  };

  const stateConfig = getStateConfig();
  const Icon = stateConfig.icon;

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* Voice Button */}
      <div className="relative">
        <button
          onClick={handleToggleRecording}
          disabled={stateConfig.disabled}
          className={`
            relative flex items-center justify-center w-16 h-16 rounded-full text-white
            transition-all duration-200 transform hover:scale-105 active:scale-95
            disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
            ${stateConfig.color}
            ${stateConfig.pulse ? 'animate-pulse' : ''}
          `}
          title={stateConfig.label}
        >
          <Icon 
            size={24} 
            className={stateConfig.spin ? 'animate-spin' : ''} 
          />
          
          {/* Recording indicator */}
          {state === 'recording' && (
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-400 rounded-full animate-pulse" />
          )}
        </button>
        
        {/* State label */}
        <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {stateConfig.label}
          </span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg max-w-md">
          <AlertCircle size={16} className="text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
          <button
            onClick={clearError}
            className="ml-auto text-red-500 hover:text-red-700 text-sm font-medium"
          >
            ×
          </button>
        </div>
      )}

      {/* Transcription Display */}
      {transcription && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg max-w-md">
          <div className="text-xs text-blue-600 dark:text-blue-400 font-medium mb-1">
            You said:
          </div>
          <div className="text-sm text-blue-800 dark:text-blue-200">
            "{transcription}"
          </div>
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg max-w-md">
          <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-1">
            SOPHIA responded:
          </div>
          <div className="text-sm text-green-800 dark:text-green-200">
            {response}
          </div>
        </div>
      )}

      {/* Usage Instructions */}
      {state === 'idle' && !transcription && !error && (
        <div className="text-center max-w-sm">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Click the microphone to start voice interaction
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Try: "Research today's AI news" or "Create a branch and add a note"
          </p>
        </div>
      )}
    </div>
  );
}


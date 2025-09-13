"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import VoiceButton from './VoiceButton'
import CodeDisplay from './CodeDisplay'

type Props = {
  apiBase?: string
}

export default function MobileVoiceInterface({ apiBase = '' }: Props) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [code, setCode] = useState('')
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // Choose API base (Next.js rewrite proxies /api/* in dev)
  const endpoints = useMemo(() => ({
    process: `${apiBase || ''}/api/voice/process`.replace(/\/$/, ''),
  }), [apiBase])

  useEffect(() => {
    // Init Web Speech API fallback (simple Phase 1a baseline)
    const SR: any = (globalThis as any).SpeechRecognition || (globalThis as any).webkitSpeechRecognition
    if (SR) {
      const rec: SpeechRecognition = new SR()
      rec.continuous = true
      rec.interimResults = true
      rec.lang = 'en-US'
      rec.onresult = (e: SpeechRecognitionEvent) => {
        const idx = e.resultIndex
        const txt = e.results[idx][0].transcript
        setTranscript(txt)
        if (e.results[idx].isFinal) {
          handleSubmit(txt)
        }
      }
      rec.onerror = () => setIsListening(false)
      recognitionRef.current = rec
    }

    return () => {
      recognitionRef.current?.stop()
      recognitionRef.current = null
    }
  }, [])

  const start = useCallback(() => {
    setTranscript('')
    setIsListening(true)
    recognitionRef.current?.start()
    if ('vibrate' in navigator) navigator.vibrate(40)
  }, [])

  const stop = useCallback(() => {
    setIsListening(false)
    recognitionRef.current?.stop()
  }, [])

  const handleSubmit = useCallback(async (text: string) => {
    const content = text?.trim()
    if (!content) return
    setIsProcessing(true)
    try {
      // Send to voice processing API (existing route in app)
      const res = await fetch(endpoints.process, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: content })
      })
      const data = await res.json().catch(() => ({}))
      const aiText = data?.response || data?.text || 'Processed.'
      const codeOut = data?.code || ''
      setResponse(aiText)
      if (codeOut) setCode(codeOut)
    } catch (e) {
      setResponse('Sorry, something went wrong processing your request.')
    } finally {
      setIsProcessing(false)
    }
  }, [endpoints.process])

  return (
    <div className="max-w-md mx-auto p-4 space-y-4">
      <div className="flex items-center gap-2 text-sm opacity-80">
        <span className={`inline-block w-2 h-2 rounded-full ${isListening ? 'bg-emerald-400' : 'bg-zinc-400'}`} />
        {isListening ? 'Listening…' : 'Tap and hold to speak'}
      </div>

      <div className="rounded-xl p-6 border border-white/20 bg-white/10">
        <div className="h-24 flex items-center justify-center">
          <div className={`w-full flex gap-1 items-end ${isListening ? 'animate-pulse' : ''}`}>
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i} style={{ height: `${(i % 5) * 6 + (isListening ? 16 : 8)}px` }} className="w-2 bg-white/30 rounded" />
            ))}
          </div>
        </div>
        <div className="mt-4">
          <VoiceButton active={isListening} disabled={false} onStart={start} onEnd={stop} />
        </div>
      </div>

      {isProcessing && (
        <div className="flex items-center gap-2 text-sm opacity-80">
          <span className="w-4 h-4 border-2 border-white/40 border-t-transparent rounded-full animate-spin inline-block" />
          Processing…
        </div>
      )}

      {transcript && (
        <div className="bg-white/10 rounded-lg p-3">
          <div className="text-xs opacity-70 mb-1">You said</div>
          <p className="text-sm">{transcript}</p>
        </div>
      )}

      {response && (
        <div className="bg-white/10 rounded-lg p-3">
          <div className="text-xs opacity-70 mb-1">Assistant</div>
          <p className="text-sm whitespace-pre-wrap">{response}</p>
        </div>
      )}

      {code && <CodeDisplay code={code} />}
    </div>
  )
}


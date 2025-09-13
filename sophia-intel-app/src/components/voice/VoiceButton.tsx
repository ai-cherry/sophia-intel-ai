"use client"

import { useCallback } from 'react'

type Props = {
  active?: boolean
  disabled?: boolean
  onStart: () => void
  onEnd: () => void
}

export default function VoiceButton({ active, disabled, onStart, onEnd }: Props) {
  const handleMouseDown = useCallback(() => {
    if (!disabled) onStart()
  }, [disabled, onStart])
  const handleMouseUp = useCallback(() => {
    if (!disabled) onEnd()
  }, [disabled, onEnd])

  return (
    <button
      className={`w-full py-6 text-lg rounded-xl border transition flex items-center justify-center gap-2 select-none ${
        active ? 'bg-white/30 border-white/40' : 'bg-white/20 border-white/30'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onTouchStart={(e) => {
        e.preventDefault()
        if (!disabled) onStart()
      }}
      onTouchEnd={(e) => {
        e.preventDefault()
        if (!disabled) onEnd()
      }}
      aria-pressed={active}
      aria-label={active ? 'Listening, release to stop' : 'Hold to speak'}
    >
      <span className="text-2xl">{active ? '🎤' : '🎙️'}</span>
      <span className="font-medium">{active ? 'Listening…' : 'Hold to Speak'}</span>
    </button>
  )
}


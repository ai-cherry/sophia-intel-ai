'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function ModeSwitcher() {
  const [mode, setMode] = useState<'bi' | 'dev'>(() => (typeof window !== 'undefined' ? (localStorage.getItem('sophia-mode') as any) || 'bi' : 'bi'))
  const router = useRouter()

  useEffect(() => {
    if (typeof window !== 'undefined') localStorage.setItem('sophia-mode', mode)
  }, [mode])

  const goto = (m: 'bi' | 'dev') => {
    setMode(m)
    router.push(m === 'bi' ? '/unified' : '/chat')
  }

  return (
    <div className="flex gap-2">
      <button onClick={() => goto('bi')} className={`px-3 py-1 rounded text-xs ${mode === 'bi' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-800'}`}>BI Mode</button>
      <button onClick={() => goto('dev')} className={`px-3 py-1 rounded text-xs ${mode === 'dev' ? 'bg-green-600 text-white' : 'bg-gray-200 dark:bg-gray-800'}`}>Dev Mode</button>
    </div>
  )
}


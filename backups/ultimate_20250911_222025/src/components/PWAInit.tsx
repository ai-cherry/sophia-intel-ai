"use client"

import { useEffect } from 'react'

export default function PWAInit() {
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!('serviceWorker' in navigator)) return

    const register = async () => {
      try {
        await navigator.serviceWorker.register('/sw.js', { scope: '/' })
      } catch (err) {
        console.warn('SW registration failed', err)
      }
    }

    // Avoid registering during Next.js HMR reload storms
    const timeout = setTimeout(register, 500)
    return () => clearTimeout(timeout)
  }, [])

  return null
}


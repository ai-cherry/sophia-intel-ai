import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useUnifiedStore } from '@/lib/state/unifiedStore'

/**
 * Transitional streaming hook that proxies the existing AI stream handler
 * while starting to synchronize high-level state into the unified store.
 *
 * Swap-in point for migrating to RealtimeManager-backed streaming later.
 */
export default function useUnifiedStream() {
  const { handleStreamResponse } = useAIChatStreamHandler()
  const setSending = useUnifiedStore((s) => s.setSending)

  const handle = async (input: string | FormData) => {
    try {
      setSending(true)
      await handleStreamResponse(input)
    } finally {
      setSending(false)
    }
  }

  return { handleStreamResponse: handle }
}


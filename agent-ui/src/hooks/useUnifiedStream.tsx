"use client";
import { useCallback } from 'react';
import useAIStreamHandler from '@/hooks/useAIStreamHandler';
import { useUnifiedStore } from '@/lib/state/unifiedStore';

/*
  useUnifiedStream
  - Transitional wrapper around existing useAIStreamHandler
  - Mirrors sending state into unified store for future convergence
  - Non-breaking: delegates the actual streaming logic unchanged
*/
export default function useUnifiedStream() {
  const { handleStreamResponse: handleAIStream } = useAIStreamHandler();
  const setSending = useUnifiedStore((s) => s.setSending);

  const handleStreamResponse = useCallback(
    async (input: string | FormData) => {
      setSending(true);
      try {
        await handleAIStream(input);
      } finally {
        setSending(false);
      }
    },
    [handleAIStream, setSending]
  );

  return { handleStreamResponse };
}


"use client";
import { useCallback, useEffect, useRef } from 'react';
import useAIStreamHandler from '@/hooks/useAIStreamHandler';
import { useUnifiedStore } from '@/lib/state/unifiedStore';
import { usePlaygroundStore } from '@/store';

/*
  useUnifiedStream
  - Transitional wrapper around existing useAIStreamHandler
  - Mirrors sending state into unified store for future convergence
  - Non-breaking: delegates the actual streaming logic unchanged
*/
export default function useUnifiedStream() {
  const { handleStreamResponse: handleAIStream } = useAIStreamHandler();
  const setSending = useUnifiedStore((s) => s.setSending);
  const addMessage = useUnifiedStore((s) => s.addMessage);
  const resetChat = useUnifiedStore((s) => s.resetChat);

  // Mirror playground messages into unified store for convergence and debugging
  const subRef = useRef<(() => void) | null>(null);
  useEffect(() => {
    subRef.current = usePlaygroundStore.subscribe(
      (s) => s.messages,
      (messages) => {
        resetChat();
        const now = Date.now();
        messages.forEach((m, idx) => {
          addMessage({
            id: `${now}-${idx}`,
            role: (m.role === 'agent' ? 'assistant' : m.role) as any,
            content: m.content,
            ts: (m.created_at || Math.floor(Date.now() / 1000)) * 1000,
          });
        });
      }
    );
    return () => {
      if (subRef.current) subRef.current();
    };
  }, [addMessage, resetChat]);

  const handleStreamResponse = useCallback(
    async (input: string | FormData) => {
      setSending(true);
      const t0 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      try {
        await handleAIStream(input);
      } finally {
        setSending(false);
        const t1 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
        // Record unified chat stream timing
        useUnifiedStore.getState().updateLatency('chat.stream', t1 - t0);
      }
    },
    [handleAIStream, setSending]
  );

  return { handleStreamResponse };
}
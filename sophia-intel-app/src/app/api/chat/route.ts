import { NextResponse } from 'next/server'

type ChatMessage = { role: 'system'|'user'|'assistant'; content: string }

function providerFromModel(model: string): string | null {
  const m = model.toLowerCase()
  if (m.startsWith('openrouter/')) return 'openrouter'
  if (m.startsWith('anthropic') || m.startsWith('claude')) return 'anthropic'
  if (m.startsWith('openai') || m.startsWith('gpt-')) return 'openai'
  if (m.startsWith('xai/') || m.includes('grok')) return 'xai'
  if (m.startsWith('together') || m.includes('together_ai')) return 'together_ai'
  if (m.startsWith('groq/') || m.includes('llama3')) return 'groq'
  if (m.includes('gemini') || m.startsWith('google/')) return 'google'
  if (m.startsWith('mistral')) return 'mistral'
  return null
}

export async function POST(req: Request) {
  try {
    const url = new URL(req.url)
    const qsStream = url.searchParams.get('stream')
    const body = await req.json()
    const { model, usecase, messages, context, params, stream: bodyStream } = body || {}
    if (!Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json({ error: 'messages required' }, { status: 400 })
    }
    // Minimal context handling: prepend a system message with context summary
    const ctxParts: string[] = []
    if (context?.memory?.length) ctxParts.push(`Memory:\n${context.memory.join('\n\n')}`)
    if (context?.files?.length) {
      const fileSummaries = context.files.map((f: any) => `${f.path}${f.start?`:${f.start}`:''}${f.end?`-${f.end}`:''}`).join('\n')
      ctxParts.push(`Files:\n${fileSummaries}`)
    }
    if (context?.git?.diffs?.length) ctxParts.push(`Git Diffs:\n${context.git.diffs.join('\n\n')}`)
    const sysPrefix = ctxParts.length ? [{ role: 'system', content: `Context Provided:\n\n${ctxParts.join('\n\n')}` } as ChatMessage] : []

    const wantStream: boolean = (qsStream === '1' || qsStream === 'true' || bodyStream === true)
    const payload = {
      model: model || usecase || 'claude-3-5-sonnet',
      messages: [...sysPrefix, ...messages],
      stream: wantStream,
      temperature: params?.temperature ?? 0.3,
      max_tokens: params?.max_tokens ?? 800,
    }

    // Prefer Portkey if configured
    const preferPortkey = ((process.env.PREFER_PORTKEY || '').toLowerCase() === 'true') || (!!process.env.PORTKEY_API_KEY && !('PREFER_PORTKEY' in process.env))
    const portkeyKey = process.env.PORTKEY_API_KEY
    if (preferPortkey && portkeyKey) {
      const headers: Record<string,string> = {
        'Content-Type': 'application/json',
        'x-portkey-api-key': portkeyKey,
      }
      const prov = providerFromModel(payload.model)
      // Optional virtual key: map known providers from env if available
      const vkEnv = prov ? (process.env[`PORTKEY_VK_${prov.toUpperCase()}` as any] as string | undefined) : undefined
      if (vkEnv) headers['x-portkey-virtual-key'] = vkEnv
      // Provider hint if no VK is set
      if (!vkEnv && prov) headers['x-portkey-provider'] = prov
      const ctrl = new AbortController()
      const timer = setTimeout(()=>ctrl.abort(), 30000)
      const upstream = await fetch('https://api.portkey.ai/v1/chat/completions', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        cache: 'no-store', signal: ctrl.signal,
      })
      clearTimeout(timer)
      if (!upstream.ok) {
        const errText = await upstream.text()
        return NextResponse.json({ error: 'Portkey error', details: errText.slice(0, 400) }, { status: 502 })
      }
      if (wantStream) {
        return new Response(upstream.body, { headers: { 'Content-Type': 'text/event-stream' } })
      }
      const data = await upstream.json()
      return NextResponse.json({ message: data.choices?.[0]?.message ?? null, usage: data.usage ?? null })
    }

    // Fallback chain: LiteLLM local proxy → OpenRouter direct
    const token = process.env.LITELLM_MASTER_KEY
    if (token) {
      const ctrl = new AbortController()
      const timer = setTimeout(()=>ctrl.abort(), 30000)
      const upstream = await fetch('http://127.0.0.1:4000/v1/chat/completions', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(payload), cache: 'no-store', signal: ctrl.signal,
      })
      clearTimeout(timer)
      if (!upstream.ok) {
        const errText = await upstream.text()
        return NextResponse.json({ error: 'LiteLLM error', details: errText.slice(0, 400) }, { status: 502 })
      }
      if (wantStream) return new Response(upstream.body, { headers: { 'Content-Type': 'text/event-stream' } })
      const data = await upstream.json()
      return NextResponse.json({ message: data.choices?.[0]?.message ?? null, usage: data.usage ?? null })
    }
    const orKey = process.env.OPENROUTER_API_KEY
    if (orKey) {
      // Normalize model id: strip openrouter/ prefix if present
      const modelId = (payload.model || '').startsWith('openrouter/') ? (payload.model as string).slice('openrouter/'.length) : payload.model
      const ctrl = new AbortController()
      const timer = setTimeout(()=>ctrl.abort(), 30000)
      const upstream = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', 'Authorization': `Bearer ${orKey}`,
          'HTTP-Referer': 'https://sophia-intel.local', 'X-Title': 'Sophia Intel Studio'
        },
        body: JSON.stringify({ ...payload, model: modelId }), cache: 'no-store', signal: ctrl.signal,
      })
      clearTimeout(timer)
      if (!upstream.ok) {
        const errText = await upstream.text()
        return NextResponse.json({ error: 'OpenRouter error', details: errText.slice(0, 400) }, { status: 502 })
      }
      if (wantStream) return new Response(upstream.body, { headers: { 'Content-Type': 'text/event-stream' } })
      const data = await upstream.json()
      return NextResponse.json({ message: data.choices?.[0]?.message ?? null, usage: data.usage ?? null })
    }
    return NextResponse.json({ error: 'No gateway available. Set PORTKEY_API_KEY (preferred) or start LiteLLM or provide OPENROUTER_API_KEY.' }, { status: 500 })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? 'unknown' }, { status: 500 })
  }
}

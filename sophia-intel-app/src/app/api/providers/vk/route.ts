import { NextResponse } from 'next/server'

const PROVIDERS = [
  'OPENROUTER','TOGETHER','HUGGINGFACE','ANTHROPIC','OPENAI','GOOGLE','XAI','GROQ','MISTRAL',
] as const

export async function GET() {
  const pk = !!process.env.PORTKEY_API_KEY
  const map: Record<string, { vk?: string; present: boolean }> = {}
  for (const p of PROVIDERS) {
    const key = `PORTKEY_VK_${p}`
    const val = process.env[key]
    map[p.toLowerCase()] = { vk: val, present: !!val }
  }
  return NextResponse.json({ portkey: pk, providers: map })
}


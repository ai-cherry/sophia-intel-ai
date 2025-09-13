import { NextResponse } from 'next/server'

export async function GET() {
  const env = process.env
  const keys = Object.keys(env).filter(k => /(_API_KEY$)|(^PORTKEY_VK_)/.test(k))
  return NextResponse.json({
    ok: !!env.PORTKEY_API_KEY,
    count: keys.length,
    present: keys.sort(),
  })
}


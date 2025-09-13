import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  try {
    const r = await fetch(`http://127.0.0.1:8081/search?query=${encodeURIComponent(q)}`, { cache: 'no-store' })
    if (!r.ok) return NextResponse.json({ ok: false, items: [], error: `mem:${r.status}` }, { status: 200 })
    const data = await r.json()
    // normalize to items: string[]
    const items: string[] = Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : [])
    return NextResponse.json({ ok: true, items })
  } catch (e:any) {
    return NextResponse.json({ ok: false, items: [], error: e?.message ?? 'mem-failed' })
  }
}


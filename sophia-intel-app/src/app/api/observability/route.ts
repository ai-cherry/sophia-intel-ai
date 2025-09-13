import { NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'

type Stat = { ts?: string; model?: string; latencyMs?: number; tokensIn?: number; tokensOut?: number }

export async function GET() {
  try {
    const repoRoot = path.resolve(process.cwd(), '..')
    const logPath = path.join(repoRoot, 'logs', 'litellm.log')
    if (!fs.existsSync(logPath)) return NextResponse.json({ ok: false, error: 'no-log' })
    const content = fs.readFileSync(logPath, 'utf8')
    const lines = content.trim().split(/\r?\n/).slice(-200) // last 200 lines
    const stats: Stat[] = []
    for (const line of lines) {
      try {
        const obj = JSON.parse(line)
        const s: Stat = {
          ts: obj?.ts || obj?.time || obj?.timestamp,
          model: obj?.model || obj?.litellm_model || obj?.params?.model,
          latencyMs: obj?.latency_ms || obj?.duration_ms || obj?.timing?.latency_ms,
          tokensIn: obj?.usage?.prompt_tokens || obj?.input_tokens,
          tokensOut: obj?.usage?.completion_tokens || obj?.output_tokens,
        }
        stats.push(s)
      } catch {
        // non-JSON line; ignore
      }
    }
    // Compute aggregates
    const latencies = stats.map(s => s.latencyMs).filter((n): n is number => typeof n === 'number')
    latencies.sort((a,b)=>a-b)
    const p50 = latencies.length ? latencies[Math.floor(latencies.length*0.5)] : null
    const p95 = latencies.length ? latencies[Math.floor(latencies.length*0.95)] : null
    const count = stats.length
    const models: Record<string, number> = {}
    for (const s of stats) { if (!s.model) continue; models[s.model] = (models[s.model]||0)+1 }
    return NextResponse.json({ ok: true, count, p50, p95, models, sample: stats.slice(-10) })
  } catch (e:any) {
    return NextResponse.json({ ok: false, error: e?.message ?? 'obs-failed' }, { status: 500 })
  }
}


import { NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'

type ModelsResponse = {
  aliases: Record<string, string>
  models: Array<{ id: string; provider: string; display?: string }>
}

// Very small YAML reader for litellm-complete.yaml that extracts model_name and underlying provider
function parseLiteLLMModels(yamlText: string): Array<{ id: string; provider: string }> {
  const lines = yamlText.split(/\r?\n/)
  const out: Array<{ id: string; provider: string }> = []
  let currentModelName: string | null = null
  for (const raw of lines) {
    const line = raw.trim()
    const mName = line.match(/^-\s*model_name:\s*(.+)$/)
    if (mName) {
      currentModelName = mName[1].trim()
      // Default provider unknown until we see litellm_params.model
      out.push({ id: currentModelName, provider: 'unknown' })
      continue
    }
    const mModel = line.match(/^model:\s*(.+)$/)
    if (mModel && currentModelName) {
      const val = mModel[1].trim().replace(/^['"]|['"]$/g, '')
      const provider = val.includes('/') ? val.split('/')[0] : 'openai'
      // Update last entry provider
      out[out.length - 1] = { id: currentModelName, provider }
    }
  }
  // Dedupe by id (keep first)
  const seen = new Set<string>()
  return out.filter((m) => (seen.has(m.id) ? false : seen.add(m.id)))
}

export async function GET() {
  const repoRoot = path.resolve(process.cwd(), '..')
  const cfgPath = path.join(repoRoot, 'config', 'models.json')
  const llmYamlPath = path.join(repoRoot, 'litellm-complete.yaml')

  let aliases: Record<string, string> = {}
  try {
    const raw = fs.readFileSync(cfgPath, 'utf8')
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object' && parsed.aliases) {
      aliases = parsed.aliases as Record<string, string>
    }
  } catch {
    // fallback minimal aliases
    aliases = {
      claude: 'claude-3-5-sonnet',
      gpt4: 'gpt-4-turbo',
      analytical: 'gemini-1.5-pro',
      fast: 'groq-mixtral',
    }
  }

  let models: Array<{ id: string; provider: string }> = []
  try {
    const yml = fs.readFileSync(llmYamlPath, 'utf8')
    models = parseLiteLLMModels(yml)
  } catch {
    // minimal fallback
    models = [
      { id: 'claude-3-5-sonnet', provider: 'anthropic' },
      { id: 'gpt-4-turbo', provider: 'openai' },
      { id: 'gemini-1.5-pro', provider: 'openrouter' },
      { id: 'groq-mixtral', provider: 'groq' },
    ]
  }

  const body: ModelsResponse = {
    aliases,
    models,
  }
  return NextResponse.json(body)
}


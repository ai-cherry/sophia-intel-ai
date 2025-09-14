import fs from 'node:fs'

// Minimal Zod-like runtime validation without dependency; we keep types simple.
// If Zod is available in the project, this can be swapped to Zod schema easily.

export type AppEnv = 'dev' | 'staging' | 'prod'
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
export type AIRouter = 'portkey' | 'openrouter' | 'direct'
export type AIProvider = 'openai' | 'anthropic' | 'gemini' | 'mistral' | 'groq' | 'xai' | 'cohere' | 'ai21'

export interface EnvConfig {
  APP_ENV: AppEnv
  SERVICE_NAME: string
  LOG_LEVEL: LogLevel
  AI_ROUTER: AIRouter
  AI_PROVIDER: AIProvider
  HTTP_DEFAULT_TIMEOUT_MS: number
  HTTP_RETRY_MAX: number
  HTTP_BACKOFF_BASE_MS: number
  POSTGRES_URL?: string
  REDIS_URL?: string
  WEAVIATE_URL?: string
  NEO4J_URL?: string
  MCP_TOKEN?: string
  MCP_DEV_BYPASS: '0' | '1'
  RATE_LIMIT_RPM: number
  READ_ONLY: '0' | '1'
  OPENAI_API_KEY?: string
  ANTHROPIC_API_KEY?: string
  GOOGLE_GEMINI_API_KEY?: string
  MISTRAL_API_KEY?: string
  GROQ_API_KEY?: string
  XAI_API_KEY?: string
  COHERE_API_KEY?: string
  AI21_API_KEY?: string
  OPENROUTER_API_KEY?: string
  PORTKEY_API_KEY?: string
}

const defaults = {
  APP_ENV: 'dev',
  SERVICE_NAME: 'sophia-intel-ai',
  LOG_LEVEL: 'INFO',
  AI_ROUTER: 'direct',
  AI_PROVIDER: 'openai',
  HTTP_DEFAULT_TIMEOUT_MS: 15000,
  HTTP_RETRY_MAX: 3,
  HTTP_BACKOFF_BASE_MS: 200,
  MCP_DEV_BYPASS: '0',
  RATE_LIMIT_RPM: 120,
  READ_ONLY: '0'
} as const

function parseEnvFile(path: string): Record<string, string> {
  if (!fs.existsSync(path)) return {}
  const text = fs.readFileSync(path, 'utf8')
  const out: Record<string, string> = {}
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim()
    if (!line || line.startsWith('#') || !line.includes('=')) continue
    const [k, ...rest] = line.split('=')
    out[k.trim()] = rest.join('=').trim()
  }
  return out
}

export function loadConfig(options?: { devEnvFile?: string }): EnvConfig {
  const devEnvFile = options?.devEnvFile ?? '.env.master'
  const env: Record<string, string> = {}

  // In dev, seed from .env.master first
  const appEnv = process.env.APP_ENV ?? 'dev'
  if (appEnv === 'dev' && fs.existsSync(devEnvFile)) {
    Object.assign(env, parseEnvFile(devEnvFile))
  }
  // Overlay process env
  Object.assign(env, process.env as Record<string, string>)

  const val = <T extends string>(k: keyof EnvConfig & string, fallback?: string): string => {
    const v = env[k]
    return (v ?? (fallback ?? (defaults as any)[k])) as string
  }

  const num = (k: keyof EnvConfig & string, fallback?: number): number => {
    const v = env[k]
    const n = v != null ? Number(v) : undefined
    if (Number.isFinite(n)) return n as number
    return (fallback ?? (defaults as any)[k]) as number
  }

  const cfg: EnvConfig = {
    APP_ENV: val('APP_ENV') as AppEnv,
    SERVICE_NAME: val('SERVICE_NAME'),
    LOG_LEVEL: val('LOG_LEVEL') as LogLevel,
    AI_ROUTER: val('AI_ROUTER') as AIRouter,
    AI_PROVIDER: val('AI_PROVIDER') as AIProvider,
    HTTP_DEFAULT_TIMEOUT_MS: num('HTTP_DEFAULT_TIMEOUT_MS'),
    HTTP_RETRY_MAX: num('HTTP_RETRY_MAX'),
    HTTP_BACKOFF_BASE_MS: num('HTTP_BACKOFF_BASE_MS'),
    POSTGRES_URL: env.POSTGRES_URL,
    REDIS_URL: env.REDIS_URL,
    WEAVIATE_URL: env.WEAVIATE_URL,
    NEO4J_URL: env.NEO4J_URL,
    MCP_TOKEN: env.MCP_TOKEN,
    MCP_DEV_BYPASS: (val('MCP_DEV_BYPASS') as '0' | '1'),
    RATE_LIMIT_RPM: num('RATE_LIMIT_RPM'),
    READ_ONLY: (val('READ_ONLY') as '0' | '1'),
    OPENAI_API_KEY: env.OPENAI_API_KEY,
    ANTHROPIC_API_KEY: env.ANTHROPIC_API_KEY,
    GOOGLE_GEMINI_API_KEY: env.GOOGLE_GEMINI_API_KEY,
    MISTRAL_API_KEY: env.MISTRAL_API_KEY,
    GROQ_API_KEY: env.GROQ_API_KEY,
    XAI_API_KEY: env.XAI_API_KEY,
    COHERE_API_KEY: env.COHERE_API_KEY,
    AI21_API_KEY: env.AI21_API_KEY,
    OPENROUTER_API_KEY: env.OPENROUTER_API_KEY,
    PORTKEY_API_KEY: env.PORTKEY_API_KEY
  }

  // Basic enum validations
  const enums: Record<string, string[]> = {
    APP_ENV: ['dev', 'staging', 'prod'],
    LOG_LEVEL: ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
    AI_ROUTER: ['portkey', 'openrouter', 'direct'],
    AI_PROVIDER: ['openai', 'anthropic', 'gemini', 'mistral', 'groq', 'xai', 'cohere', 'ai21'],
    MCP_DEV_BYPASS: ['0', '1'],
    READ_ONLY: ['0', '1']
  }
  for (const [k, allowed] of Object.entries(enums)) {
    const v = (cfg as any)[k]
    if (!allowed.includes(v)) throw new Error(`Invalid ${k}: ${v}`)
  }

  return cfg
}

if (require.main === module) {
  const cfg = loadConfig()
  console.log('Environment OK:')
  for (const [k, v] of Object.entries(cfg)) {
    if (typeof v === 'string' && /_API_KEY$/.test(k) && v) {
      console.log(`- ${k}=***`)
    } else {
      console.log(`- ${k}=${v as any}`)
    }
  }
}


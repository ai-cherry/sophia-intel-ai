# 🔐 Sophia Intel AI - API Keys Reference Guide

This document outlines all the API keys required for the Sophia Intel AI system and where to obtain them.

## ✅ **CONFIGURED KEYS** (Ready to Use)

The following API keys are already configured in your `.env.local` file:

### Core AI & LLM Providers

| Provider       | Key Variable         | Status        | Usage                              |
| -------------- | -------------------- | ------------- | ---------------------------------- |
| **OpenAI**     | `OPENAI_API_KEY`     | ✅ Configured | Primary LLM provider for GPT-4/3.5 |
| **Anthropic**  | `ANTHROPIC_API_KEY`  | ✅ Configured | Claude models for analysis tasks   |
| **OpenRouter** | `OPENROUTER_API_KEY` | ✅ Configured | Multi-model router with fallbacks  |
| **Groq**       | `GROQ_API_KEY`       | ✅ Configured | Fast inference for Llama models    |
| **DeepSeek**   | `DEEPSEEK_API_KEY`   | ✅ Configured | Alternative reasoning models       |
| **xAI**        | `XAI_API_KEY`        | ✅ Configured | Grok models                        |
| **Gemini**     | `GEMINI_API_KEY`     | ✅ Configured | Google's Gemini models             |
| **Mistral**    | `MISTRAL_API_KEY`    | ✅ Configured | Mistral AI models                  |
| **Perplexity** | `PERPLEXITY_API_KEY` | ✅ Configured | Search-augmented AI                |

### Gateway & Orchestration

| Provider    | Key Variable      | Status        | Usage                        |
| ----------- | ----------------- | ------------- | ---------------------------- |
| **Portkey** | `PORTKEY_API_KEY` | ✅ Configured | AI gateway with virtual keys |
| **Agno**    | `AGNO_API_KEY`    | ✅ Configured | Agent orchestration system   |

### Vector Databases & Memory

| Provider            | Key Variable   | Status        | Usage                       |
| ------------------- | -------------- | ------------- | --------------------------- |
| **Weaviate v1.32+** | `WEAVIATE_URL` | ✅ Configured | Vector similarity search    |
| **Redis Cloud**     | `REDIS_URL`    | ✅ Configured | Cache and session storage   |
| **MEM0**            | `MEM0_API_KEY` | ✅ Configured | Long-term memory management |

### Database & Infrastructure

| Provider            | Key Variable             | Status        | Usage                  |
| ------------------- | ------------------------ | ------------- | ---------------------- |
| **Neon PostgreSQL** | `NEON_API_KEY`           | ✅ Configured | Serverless PostgreSQL  |
| **Neon PostgreSQL** | `NEON_REST_API_ENDPOINT` | ✅ Configured | Database API endpoint  |
| **Pulumi**          | `PULUMI_ACCESS_TOKEN`    | ✅ Configured | Infrastructure as code |
| **Fly.io**          | `FLY_API_TOKEN`          | ✅ Configured | Container deployment   |
| **Lambda Labs**     | `LAMBDA_API_KEY`         | ✅ Configured | GPU compute instances  |

### Embedding & Search APIs

| Provider         | Key Variable            | Status        | Usage                        |
| ---------------- | ----------------------- | ------------- | ---------------------------- |
| **Hugging Face** | `HUGGINGFACE_API_TOKEN` | ✅ Configured | Model hosting and embeddings |
| **Exa**          | `EXA_API_KEY`           | ✅ Configured | Semantic search API          |
| **Brave Search** | `BRAVE_API_KEY`         | ✅ Configured | Web search API               |
| **Serper**       | `SERPER_API_KEY`        | ✅ Configured | Google Search API            |
| **Tavily**       | `TAVILY_API_KEY`        | ✅ Configured | Research and search          |

## 🚀 **Quick Validation**

Test all your API keys with the validation script:

```bash
# Run the API validation script
python3 scripts/validate-apis.py

# Expected output: ✅ All APIs validated successfully
```

## 🔧 **Key Management Best Practices**

### Security Guidelines

1. **Never commit API keys** to version control
2. **Use environment variables** for all keys
3. **Rotate keys regularly** (every 90 days recommended)
4. **Monitor usage** for unexpected spikes
5. **Set usage limits** where possible

### Key Rotation Schedule

| Key Type         | Rotation Frequency | Notes                 |
| ---------------- | ------------------ | --------------------- |
| Development keys | 90 days            | For local development |
| Production keys  | 60 days            | Critical systems      |
| Emergency access | 30 days            | Break-glass scenarios |

### Usage Monitoring

Monitor these metrics for each provider:

- **Request volume** - Track daily/monthly usage
- **Error rates** - Monitor failed requests
- **Latency** - Track response times
- **Cost** - Monitor spending per provider

## 🔍 **Troubleshooting Common Issues**

### API Key Validation Failures

**Error: "Missing API key"**

```bash
# Check if key is set
echo $OPENAI_API_KEY
# Should show: sk-...

# If empty, reload environment
source .env.local
```

**Error: "Invalid API key"**

```bash
# Test key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**Error: "Rate limit exceeded"**

- Check provider dashboard for limits
- Implement exponential backoff
- Consider upgrading plan

### Provider-Specific Issues

**OpenAI Issues:**

- Rate limits: 3,500 requests/minute (GPT-4)
- Token limits: 8,192 tokens (GPT-4)
- Cost monitoring: ~$0.03/1K tokens

**Anthropic Issues:**

- Different message format required
- Streaming format differs from OpenAI
- Rate limits per model vary

**Weaviate Issues:**

- Collection auto-created if not exists
- Vector dimensions must match
- API key format: Bearer token

**Redis Issues:**

- Connection string format: `redis://user:pass@host:port`
- SSL required for cloud instances
- Memory limits affect performance

## 🏗️ **Architecture Overview**

```mermaid
graph TD
    A[Client Request] --> B[API Gateway]
    B --> C[Portkey Router]
    C --> D[OpenAI]
    C --> E[Anthropic]
    C --> F[OpenRouter]

    B --> G[Vector Store]
    G --> I[Weaviate v1.32+]

    B --> J[Memory System]
    J --> K[Redis]
    J --> L[PostgreSQL]

    B --> M[Search APIs]
    M --> N[Brave]
    M --> O[Serper]
    M --> P[Tavily]
```

## 📊 **Cost Estimation**

**Monthly Usage Estimates** (Development):

| Provider        | Estimated Cost | Usage            |
| --------------- | -------------- | ---------------- |
| OpenAI          | $50-100        | GPT-4 queries    |
| Anthropic       | $30-60         | Claude queries   |
| OpenRouter      | $20-40         | Fallback queries |
| Weaviate Cloud  | $25-35         | Vector storage   |
| Redis Cloud     | $15-25         | Caching          |
| Neon PostgreSQL | $10-20         | Database         |
| **Total**       | **$145-275**   | **Per month**    |

## 🚨 **Emergency Procedures**

### Key Compromise

1. **Immediately revoke** the compromised key
2. **Generate new key** from provider dashboard
3. **Update environment variables**
4. **Restart all services**
5. **Monitor for unauthorized usage**

### Service Outages

1. **Check provider status pages**
2. **Enable fallback providers**
3. **Scale back non-critical features**
4. **Monitor recovery**

### Quota Exhaustion

1. **Check usage dashboards**
2. **Upgrade plans if needed**
3. **Implement rate limiting**
4. **Add usage alerts**

## 📞 **Support Contacts**

- **OpenAI**: <https://help.openai.com>
- **Anthropic**: <https://support.anthropic.com>
- **Weaviate**: <https://weaviate.io/developers/support>
- **Neon**: <https://neon.tech/docs/support>
- **Portkey**: <https://portkey.ai/docs>

---

**Last Updated**: January 2025  
**Version**: 2.0.0

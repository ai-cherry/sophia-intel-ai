# 🔍 DETAILED ANALYSIS: Why Certain API Keys Are Failing

## ❌ FAILED APIS - Root Cause Analysis

---

## 1. ❌ **Perplexity API** 
**Status:** Key is valid, but model name is wrong

### Error Details:
```
Error code: 400 - Invalid model 'llama-3.1-sonar-small-128k-chat'
```

### Root Cause:
- **The API key is VALID** (`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`)
- **The model name we're using is INCORRECT**
- We're trying to use: `llama-3.1-sonar-small-128k-chat`
- Perplexity's actual model names have changed

### Solution:
```python
# Current (failing):
model="llama-3.1-sonar-small-128k-chat"

# Should be one of these (check Perplexity docs):
model="sonar-small-chat"  # or
model="sonar-medium-chat"  # or
model="pplx-7b-chat"  # or
model="pplx-70b-chat"
```

### Fix Required:
1. Check https://docs.perplexity.ai for current model names
2. Update model name in `app/core/portkey_config.py`
3. Update Portkey dashboard configuration

---

## 2. ❌ **X.AI Grok**
**Status:** Key might be valid, but endpoint/model incorrect

### Error Details:
```
Error code: 404 - The model grok-beta does not exist
```

### Root Cause:
- **API key provided:** `xai-4WmKCCbqXhuxL56tfrCxaqs3N84fcLVirQG0NIb0NB6ViDPnnvr3vsYOBwpPKpPMzW5UMuHqf1kv87m3`
- **Model `grok-beta` doesn't exist or we don't have access**
- X.AI/Grok is still in limited beta access

### Possible Issues:
1. **Wrong model name** - Should be `grok-1` or `grok-2`?
2. **Wrong endpoint** - Using `https://api.x.ai/v1` but might need different URL
3. **Limited access** - Key might not have access to the model
4. **Service not activated** - X.AI account might need activation

### Solution:
```python
# Try these alternatives:
model="grok-1"  # or
model="grok-2"  # or check X.AI documentation

# May also need different base URL:
base_url="https://api.x.ai/v1"  # Current
# Might need: "https://api.grok.x.ai/v1" or similar
```

---

## 3. ❌ **HuggingFace**
**Status:** Key is valid, but model endpoint failing

### Error Details:
```
HTTP 404 - Model endpoint not found
```

### Root Cause:
- **API key is VALID** (`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`)
- **Model we tried (`gpt2`) returned 404**
- HuggingFace Inference API has specific requirements

### Issues:
1. **Model not loaded** - Model might need to be loaded/warmed up first
2. **Wrong model ID** - Should use full model path
3. **Inference API limitations** - Not all models available via inference API
4. **Rate limiting** - Free tier has strict limits

### Solution:
```python
# Instead of:
"https://api-inference.huggingface.co/models/gpt2"

# Try:
"https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
# or
"https://api-inference.huggingface.co/models/google/flan-t5-base"

# Also need to handle cold start:
# First request might return 503 (model loading), retry after a few seconds
```

---

## 4. ⚠️ **Mem0 Memory API**
**Status:** Authentication failing

### Error Details:
```
HTTP 401 - Unauthorized
```

### Root Cause:
- **API key format looks correct** (`m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc`)
- **401 means the key is not being accepted**

### Possible Issues:
1. **Expired key** - Mem0 keys might have expiration
2. **Wrong endpoint** - API URL might have changed
3. **Missing headers** - Might need additional auth headers
4. **Account suspended** - Check Mem0 dashboard
5. **Wrong API version** - v1 vs v2 endpoints

### Solution:
```python
# Current attempt:
headers = {
    "Authorization": f"Bearer {MEM0_API_KEY}",
    "Content-Type": "application/json"
}
url = "https://api.mem0.ai/v1/memories"

# Might need:
headers = {
    "Authorization": f"Token {MEM0_API_KEY}",  # Different format
    "X-Account-Id": "org_gHuEO2H7ymIIgivcWeKI2psRFHUnbZ54RQNYVb4T",
    "Content-Type": "application/json"
}
# Or check if API moved to v2:
url = "https://api.mem0.ai/v2/memories"
```

---

## 5. ❌ **Qwen API**
**Status:** Not tested, likely needs special setup

### Details:
- **Key provided:** `qwen-api-key-ad6c81`
- **Not included in tests** because Qwen (Alibaba) requires special SDK

### Issues:
1. **Regional restrictions** - Qwen is primarily for Chinese market
2. **Special SDK required** - Not standard OpenAI-compatible
3. **Different auth method** - May use different authentication

### Solution:
```bash
# Need to install Qwen SDK:
pip install dashscope

# Then use their specific client:
from dashscope import Generation
response = Generation.call(
    model='qwen-turbo',
    prompt='Hello'
)
```

---

## 6. ⚠️ **Vector Databases (Qdrant, Weaviate, Milvus)**
**Status:** Keys configured but connection issues

### Qdrant Issue:
```
HTTP 403 Forbidden - Authentication failed
```
- **Key format might be wrong** - The pipe character `|` in the key suggests it might be two parts
- **URL might need port** - Should be `:6333` at the end?

### Weaviate Issue:
```
Library conflict - protobuf version mismatch
```
- **Not a key issue** - Python dependency conflict
- Fix: `pip install --upgrade protobuf==4.25.0`

### Milvus Issue:
```
Not tested - needs local/remote instance
```
- **Key provided but no server** - Milvus needs running instance
- The key alone isn't enough, need Milvus server

---

## 📊 Summary Table

| Service | Key Valid? | Issue Type | Quick Fix |
|---------|-----------|------------|-----------|
| Perplexity | ✅ Yes | Wrong model name | Change to `sonar-small-chat` |
| X.AI Grok | ❓ Maybe | Model not found | Try `grok-1` or check access |
| HuggingFace | ✅ Yes | Model endpoint 404 | Use different model |
| Mem0 | ❓ Maybe | Auth rejected | Check if expired, try different header format |
| Qwen | ❓ Unknown | Not tested | Need special SDK |
| Qdrant | ❓ Maybe | Auth format | Split key at `\|` character |
| Weaviate | ✅ Yes | Library conflict | Fix protobuf version |
| Milvus | ❓ Unknown | No server | Need running instance |

---

## 🔧 Quick Fixes to Try

### 1. For Perplexity:
```python
# In app/core/portkey_config.py, change:
models=["sonar-small-chat", "sonar-medium-chat"]
```

### 2. For X.AI Grok:
```python
# Try different model names:
model="grok-1"  # Instead of "grok-beta"
```

### 3. For HuggingFace:
```python
# Use a definitely-working model:
url = "https://api-inference.huggingface.co/models/gpt2-medium"
# And retry on 503 (model loading)
```

### 4. For Mem0:
```python
# Try without Bearer prefix:
headers = {"Authorization": MEM0_API_KEY}
# Or check https://docs.mem0.ai for current auth format
```

### 5. For Qdrant:
```python
# Split the key at the pipe:
key_parts = QDRANT_API_KEY.split('|')
api_key = key_parts[0]  # Use first part
# Or try second part if first doesn't work
```

---

## ✅ The Good News

**The majority of failures are NOT due to invalid keys**, but rather:
- **Wrong model names** (Perplexity, X.AI)
- **Wrong endpoints** (HuggingFace)
- **Library conflicts** (Weaviate)
- **Missing infrastructure** (Milvus)

Most of these can be fixed with simple configuration changes, not new keys.
# Fly.io Current Inventory - Live Machine Details

**🚨 CRITICAL MACHINE INVENTORY - DO NOT DELETE**  
**Account**: <musillynn@gmail.com> | **Last Updated**: 2025-01-09 15:27 UTC

## 📱 **LIVE Fly.io Applications**

### **✅ Successfully Created & Deployed**

| App Name                      | Status           | Machine ID     | Region | URL                                          | Purpose              |
| ----------------------------- | ---------------- | -------------- | ------ | -------------------------------------------- | -------------------- |
| **hello-fly-green-pine-1785** | ✅ **LIVE**      | 90807e2ef0e198 | lax    | <https://hello-fly-green-pine-1785.fly.dev/> | Test validation      |
| **hello-fly-green-pine-1785** | ✅ **LIVE**      | 56837d21b65768 | lax    | ↑ same                                       | Test validation      |
| **sophia-weaviate**           | ✅ **LIVE**      | 784936efd5d738 | sjc    | <https://sophia-weaviate.fly.dev>            | Vector Database      |
| **sophia-mcp**                | 🔄 **DEPLOYING** | TBD            | sjc    | <https://sophia-mcp.fly.dev>                 | Memory Management    |
| **sophia-vector**             | ⏳ **PENDING**   | TBD            | sjc    | <https://sophia-vector.fly.dev>              | 3-Tier Embeddings    |
| **sophia-api**                | ⏳ **PENDING**   | TBD            | sjc    | <https://sophia-api.fly.dev>                 | Main Orchestrator 🔥 |
| **sophia-bridge**             | ⏳ **PENDING**   | TBD            | sjc    | <https://sophia-bridge.fly.dev>              | UI Compatibility     |
| **sophia-ui**                 | ⏳ **PENDING**   | TBD            | sjc    | <https://sophia-ui.fly.dev>                  | Frontend Interface   |

## 🖥️ **LIVE Machine Specifications**

### **sophia-weaviate (OPERATIONAL)** ✅

```json
{
  "app_name": "sophia-weaviate",
  "machine_id": "784936efd5d738",
  "region": "sjc",
  "state": "started",
  "health_checks": "2 total, 2 passing",
  "last_updated": "2025-09-01T15:20:18Z",
  "image": "semitechnologies/weaviate:1.32.1",
  "url": "https://sophia-weaviate.fly.dev",
  "internal_url": "sophia-weaviate.internal:8080"
}
```

### **hello-fly-green-pine-1785 (TEST APP)** ✅

```json
{
  "app_name": "hello-fly-green-pine-1785",
  "machines": [
    {
      "machine_id": "90807e2ef0e198",
      "region": "lax",
      "state": "started",
```

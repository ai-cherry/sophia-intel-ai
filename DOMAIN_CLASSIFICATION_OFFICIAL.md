# 🎯 OFFICIAL Domain Classification & Memory Routing

## ⚠️ CRITICAL: Business Data Protection

**ALL business intelligence data, foundational knowledge, and Airtable data MUST route to SOPHIA domain ONLY.**

## Domain Classifications

### 🔵 **SOPHIA Domain** (`MemoryDomain.SOPHIA`)
**Purpose**: Business Intelligence & Strategic Operations

#### Data Types:
- ✅ **Airtable foundational knowledge**
- ✅ **Sophia business intelligence**  
- ✅ **Sales data and analytics**
- ✅ **Customer insights and data**
- ✅ **Revenue metrics and forecasting**
- ✅ **Market research and competitive analysis**
- ✅ **Strategic planning and OKR tracking**
- ✅ **Business process documentation**
- ✅ **Executive reporting data**

#### Operations:
- `BUSINESS_ANALYSIS`
- `SALES_ANALYTICS` 
- `CUSTOMER_INSIGHTS`
- `MARKET_RESEARCH`
- `COMPETITIVE_ANALYSIS`
- `REVENUE_FORECASTING`
- `STRATEGIC_PLANNING`
- `OKR_TRACKING`
- `CUSTOMER_SUCCESS`
- `BUSINESS_INTELLIGENCE`

### 🟢 **CODE Domain** (`MemoryDomain.CODE`)
**Purpose**: Technical Development & Engineering

#### Data Types:
- ✅ **Code repositories and analysis**
- ✅ **Technical documentation**
- ✅ **Architecture designs and diagrams**
- ✅ **Security scanning results**
- ✅ **Performance optimization data**
- ✅ **Test coverage and metrics**
- ✅ **CI/CD pipeline data**

#### Operations:
- `CODE_GENERATION`
- `CODE_REVIEW`
- `CODE_REFACTORING`
- `SECURITY_SCANNING`
- `PERFORMANCE_OPTIMIZATION`
- `ARCHITECTURE_DESIGN`
- `TEST_GENERATION`
- `DOCUMENTATION`
- `REPOSITORY_ANALYSIS`
- `CI_CD_OPERATIONS`

### 🟡 **SHARED Domain** (`MemoryDomain.SHARED`)
**Purpose**: Cross-Domain Knowledge

#### Data Types:
- ✅ **Company-wide policies**
- ✅ **General documentation**
- ✅ **Shared resources and tools**
- ✅ **Cross-functional processes**

#### Operations:
- `REPORTING`
- `MONITORING`
- `LOGGING`
- `METRICS_COLLECTION`

## App Names (OFFICIAL)

### ✅ **sophia-intel-app**
- **Port**: 3000
- **Purpose**: Business Intelligence Dashboard
- **Domain**: SOPHIA
- **Data**: Airtable, business metrics, executive reporting

### ✅ **agno-builder-app** 
- **Port**: 3001
- **Purpose**: AI Agent Development Platform
- **Domain**: CODE
- **Data**: Agent configurations, code generation

### ✅ **litellm-builder-app**
- **Port**: 8090
- **Purpose**: Intelligent AI Routing System
- **Domain**: CODE
- **Data**: Model routing, cost optimization

## Memory Routing Rules

### Business Intelligence Flow:
```
Airtable Data → SOPHIA Domain → Business Intelligence → Executive Dashboard
```

### Technical Development Flow:
```
Code Repository → CODE Domain → Technical Analysis → Developer Tools
```

### Cross-Domain Access:
- Business analysts can READ CODE domain data
- Developers can READ SOPHIA domain data  
- Admins have FULL access to both domains

## 🚨 NEVER DO THIS:
- ❌ Route Airtable data to CODE domain
- ❌ Route business metrics to CODE domain  
- ❌ Mix foundational knowledge with technical data
- ❌ Use "agent-ui" naming (deprecated)

## 🎯 ALWAYS DO THIS:
- ✅ Route business data to SOPHIA domain
- ✅ Route technical data to CODE domain
- ✅ Use proper app names (sophia-intel-app, etc.)
- ✅ Validate domain assignments in code reviews

---

**Last Updated**: September 2024  
**Status**: OFFICIAL - All future AI agents must follow these classifications
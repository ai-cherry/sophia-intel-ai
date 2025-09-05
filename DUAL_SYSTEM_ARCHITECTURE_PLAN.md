# 🎯 DUAL SYSTEM ARCHITECTURE: SOPHIA VS ARTEMIS

## 📋 SYSTEM SEPARATION SPECIFICATIONS

### 🔵 **SOPHIA INTELLIGENCE PLATFORM** (Business Wisdom)

- **Port Range**: 9000-9099
- **Color Theme**: Blue/Purple/Pink (Elegant Wisdom)
- **Primary Colors**:
  - `--primary-blue: #4A90E2`
  - `--secondary-purple: #9B59B6`
  - `--accent-pink: #FF6B9D`
- **Personality**: Wise, strategic, business-focused
- **Agents**: Apollo (Sales Strategy), Athena (Client Success)

### 🔴 **ARTEMIS COMMAND CENTER** (Technical Operations)

- **Port Range**: 8000-8099
- **Color Theme**: Red/Orange/Green (Dramatic Tactical)
- **Primary Colors**:
  - `--artemis-primary: #E74C3C`
  - `--artemis-secondary: #FF6600`
  - `--artemis-accent: #00FF41`
- **Personality**: Tactical, aggressive, tech-focused
- **Agents**: Ares (Code Combat), Athena Tactical (System Defense), Apollo Tech (Architecture)

### ⚪ **SHARED MCP INFRASTRUCTURE**

- **Port**: 3333
- **Purpose**: Routing, shared services, coordination
- **Theme**: Neutral/Adaptive

---

## 🏗️ IMPLEMENTATION ARCHITECTURE

### **Service Deployment Map**

```
┌─────────────────┬─────────────────┬─────────────────┐
│   SOPHIA        │   SHARED MCP    │   ARTEMIS       │
│   (9000-9099)   │   (3333)        │   (8000-8099)   │
├─────────────────┼─────────────────┼─────────────────┤
│ • Wisdom AI     │ • Routing       │ • Tactical AI   │
│ • Sales Intel   │ • Auth          │ • Code Combat   │
│ • Client Health │ • Monitoring    │ • Sys Defense   │
│ • Bus Strategy  │ • Coordination  │ • Architecture  │
└─────────────────┴─────────────────┴─────────────────┘
```

### **URL Structure**

```
SOPHIA (Business Intelligence):
- http://localhost:9000/sophia/dashboard.html
- http://localhost:9000/api/sophia/wisdom
- http://localhost:9000/api/sophia/chat/{agent}

ARTEMIS (Technical Operations):
- http://localhost:8000/artemis/command-center.html
- http://localhost:8000/api/artemis/tactical
- http://localhost:8000/api/artemis/chat/{agent}

SHARED MCP:
- http://localhost:3333/static/sophia-intelligence-hub.html
- http://localhost:3333/api/routing/
- http://localhost:3333/api/health/
```

---

## 🎨 UI/UX DESIGN SPECIFICATIONS

### **SOPHIA (Blue Theme)**

```css
:root {
  /* Sophia's Elegant Wisdom Palette */
  --primary-blue: #4a90e2;
  --primary-blue-light: #6ba6f7;
  --secondary-purple: #9b59b6;
  --secondary-purple-light: #b77fcf;
  --accent-pink: #ff6b9d;
  --accent-pink-light: #ffc0e3;

  /* Sophia Effects */
  --wisdom-glow: 0 0 20px var(--primary-blue);
  --soft-border: 12px;
  --elegant-shadow: 0 8px 32px rgba(74, 144, 226, 0.3);
}
```

### **ARTEMIS (Red Theme)**

```css
:root {
  /* Artemis Tactical Combat Palette */
  --artemis-primary: #e74c3c;
  --artemis-primary-light: #ff4444;
  --artemis-secondary: #ff6600;
  --artemis-secondary-light: #ff8800;
  --artemis-accent: #00ff41;
  --artemis-accent-bright: #39ff14;

  /* Artemis Effects */
  --electric-glow: 0 0 20px var(--artemis-accent);
  --fire-glow: 0 0 20px var(--artemis-primary);
  --hard-shadow: 4px 4px 0px var(--artemis-primary);
  --sharp-border: 4px;
}
```

---

## 🤖 AGENT PERSONALITY SPECIFICATIONS

### **SOPHIA AGENTS (Wisdom-Focused)**

#### **Apollo 'The Strategist' Thanos** ⚡

- **Role**: Sales Wisdom & Strategic Catalyst
- **Voice**: Strategic, insightful, business-focused
- **Response Style**: "Greetings, strategist! Sophia's wisdom illuminates..."
- **Specialization**: Sales strategy, market analysis, business intelligence

#### **Athena 'The Protector' Sophia** 🦉

- **Role**: Client Wisdom & Success Guardian
- **Voice**: Protective, nurturing, relationship-focused
- **Response Style**: "Wisdom guides my counsel regarding..."
- **Specialization**: Client success, relationship management, partnership health

### **ARTEMIS AGENTS (Combat-Focused)**

#### **Ares 'The Dominator' Rex** ⚔️

- **Role**: Code Combat & System Warfare Specialist
- **Voice**: Aggressive, tactical, results-driven
- **Response Style**: "Command received! Analysis complete. Engaging combat protocols..."
- **Specialization**: Code debugging, system optimization, technical warfare

#### **Athena 'The Shield' Prime** 🛡️

- **Role**: System Defense & Security Strategist
- **Voice**: Defensive, security-focused, tactical
- **Response Style**: "Security briefing... Activating protective measures..."
- **Specialization**: System security, defensive strategies, threat analysis

#### **Apollo 'The Architect' Prime** 🏗️

- **Role**: Technical Architecture & System Design
- **Voice**: Engineering-focused, systematic, builder
- **Response Style**: "Technical specification received... Initiating construction protocols..."
- **Specialization**: System architecture, technical design, infrastructure

---

## 🚀 DEPLOYMENT CONFIGURATION

### **Port Assignments (FINAL)**

```bash
# SOPHIA PLATFORM
SOPHIA_PORT=9000          # Main Sophia server
SOPHIA_API_PORT=9001      # Sophia API services
SOPHIA_WS_PORT=9002       # Sophia WebSocket

# ARTEMIS COMMAND CENTER
ARTEMIS_PORT=8000         # Main Artemis server
ARTEMIS_API_PORT=8001     # Artemis API services
ARTEMIS_WS_PORT=8002      # Artemis WebSocket

# SHARED MCP INFRASTRUCTURE
MCP_PORT=3333             # MCP unified server
MCP_ADMIN_PORT=3334       # MCP admin interface
MCP_MONITOR_PORT=3335     # MCP monitoring
```

### **Service Start Commands**

```bash
# Start Sophia Intelligence Platform
SOPHIA_PORT=9000 python3 sophia_server_standalone.py &

# Start Artemis Command Center
ARTEMIS_PORT=8000 python3 artemis_server_standalone.py &

# Start Shared MCP Infrastructure
MCP_PORT=3333 python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --port 3333 &
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### **Phase 1: Core Separation** ✅

- [x] Create separate Artemis server (port 8000)
- [x] Update Sophia server (port 9000)
- [x] Implement distinct agent personalities
- [x] Configure proper port assignments

### **Phase 2: UI/UX Implementation** 🔄

- [ ] Create Sophia dashboard with blue theme
- [ ] Create Artemis command center with red theme
- [ ] Implement theme-specific styling
- [ ] Create separate static file serving

### **Phase 3: Agent Integration** 🔄

- [ ] Implement Sophia wisdom agents (Apollo, Athena)
- [ ] Implement Artemis tactical agents (Ares, Athena Prime, Apollo Tech)
- [ ] Create distinct chat interfaces
- [ ] Implement personality-specific responses

### **Phase 4: Deployment & Testing** 📋

- [ ] Update deployment scripts for dual system
- [ ] Create separate health checks
- [ ] Implement cross-system routing
- [ ] Test complete separation

---

## 🔥 CRITICAL SUCCESS FACTORS

1. **Complete Separation**: No shared UI components between Sophia/Artemis
2. **Distinct Personalities**: Each system has unique voice and behavior
3. **Theme Consistency**: Strict adherence to color/style specifications
4. **Port Discipline**: Rigid port range enforcement
5. **Independent Deployment**: Each system can operate standalone

---

**MOTTO**:

- **Sophia**: "Through wisdom, we achieve business excellence"
- **Artemis**: "Through tactical superiority, we achieve technical victory"

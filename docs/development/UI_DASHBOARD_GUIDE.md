# 🎨 Sophia Intel AI - UI Dashboard Guide

## Available User Interfaces

### 1. **Agent UI Dashboard** (React/TypeScript)
**Location**: `/sophia-intel-app/`  
**Component**: `ModelCostDashboard.tsx`  
**Features**:
- Real-time model cost tracking
- Squad agent monitoring
- Visual orchestration platform
- Performance metrics

**Start Command**:
```bash
cd sophia-intel-app
npm install
npm run dev
# Opens at http://localhost:3001
```

---

### 2. **Builder System Dashboard** (HTML/JavaScript)
**Location**: `/builder-system/dashboard/`  
**Files**:
- `index.html` - Main dashboard
- `enhanced.html` - Enhanced features
- `smart.html` - Smart agent controls
- `ultimate.html` - Ultimate control panel

**Features**:
- Code generation interface
- Repository management
- Agent control panels
- Real-time status monitoring

**Access**:
```bash
# Open directly in browser
open builder-system/dashboard/index.html

# Or serve with Python
cd builder-system/dashboard
python3 -m http.server 8080
# Opens at http://localhost:8080
```

---

### 3. **Main Dashboard** (Svelte)
**Location**: `/dashboard/`  
**Technology**: Svelte framework  
**Features**:
- Interactive agent management
- Service monitoring
- Cost tracking

**Start Command**:
```bash
cd dashboard
npm install
npm run dev
# Opens at http://localhost:5173
```

---

### 4. **Sophia Intel App UI**
**Location**: `/sophia-intel-app/ui/`  
**File**: `index.html`  
**Features**:
- Simplified interface
- Quick access controls

**Access**:
```bash
open sophia-intel-app/ui/index.html
```

---

### 5. **Web UI Frontend**
**Location**: `/webui/frontend/`  
**Files**:
- `index.html` - Main interface
- `tactical-command.html` - Advanced controls

**Features**:
- Tactical command center
- Advanced agent controls

**Access**:
```bash
cd webui/frontend
python3 -m http.server 8081
# Opens at http://localhost:8081
```

---

### 6. **API Documentation UI**
**Endpoints with Built-in UI**:

#### AIMLAPI Squad Docs
```bash
# FastAPI automatic docs
open http://localhost:8090/docs
```

#### OpenRouter Squad Dashboard
```bash
# Service monitoring
open http://localhost:8092/docs
```

---

## 🚀 Quick Start All UIs

### Start Everything with One Script
```bash
#!/bin/bash
# Save as start_all_ui.sh

echo "Starting all UI dashboards..."

# 1. Agent UI (React)
cd sophia-intel-app && npm run dev &

# 2. Main Dashboard (Svelte)
cd dashboard && npm run dev &

# 3. Builder Dashboard
cd builder-system/dashboard && python3 -m http.server 8080 &

# 4. Web UI
cd webui/frontend && python3 -m http.server 8081 &

echo "All dashboards starting..."
echo "
Available at:
- Agent UI: http://localhost:3001
- Main Dashboard: http://localhost:5173
- Builder Dashboard: http://localhost:8080
- Web UI: http://localhost:8081
- AIMLAPI Docs: http://localhost:8090/docs
- OpenRouter Docs: http://localhost:8092/docs
"
```

---

## 📊 Dashboard Features Comparison

| Dashboard | Technology | Real-time | Cost Tracking | Agent Control | Visualization |
|-----------|------------|-----------|---------------|---------------|---------------|
| Agent UI | React/TS | ✅ | ✅ | ✅ | ✅ Charts |
| Builder | HTML/JS | ✅ | ❌ | ✅ | ✅ Status |
| Main | Svelte | ✅ | ✅ | ✅ | ✅ Interactive |
| Web UI | HTML | ⚠️ | ❌ | ✅ | ⚠️ Basic |

---

## 🎯 Recommended UI for Squad Management

### For Squad Monitoring & Control:
**Use: Agent UI Dashboard (React)**
- Most comprehensive
- Real-time updates
- Cost tracking
- Visual orchestration

### For Quick Status Checks:
**Use: API Documentation Pages**
- http://localhost:8090/docs (AIMLAPI)
- http://localhost:8092/docs (OpenRouter)

### For Code Generation:
**Use: Builder System Dashboard**
- Specialized for code tasks
- Repository management
- Multiple view options

---

## 🖥️ Terminal UI (Already Running)

### CLI Dashboard
```bash
# Rich terminal interface
python3 sophia_squad_cli.py dashboard
```

Features:
- ASCII art visualizations
- Real-time status updates
- No browser needed
- Runs in terminal

---

## 🔧 UI Configuration

### Environment Variables for UI
Add to `<repo>/.env.master`:
```bash
# UI Configuration
UI_PORT=3001
DASHBOARD_PORT=5173
BUILDER_PORT=8080
WEBUI_PORT=8081

# Enable UI features
ENABLE_REALTIME=true
ENABLE_COST_TRACKING=true
ENABLE_VISUALIZATIONS=true
```

---

## 📱 Mobile Access

All HTML dashboards are mobile-responsive. Access from your phone:
1. Find your machine's IP: `ifconfig | grep inet`
2. Access: `http://YOUR_IP:PORT`

Example:
```
http://192.168.1.100:8080  # Builder Dashboard
http://192.168.1.100:3001  # Agent UI
```

---

## 🎨 UI Customization

### Theme Configuration
Most dashboards support dark/light themes:
- Agent UI: Settings → Theme
- Builder: Click theme toggle
- Main Dashboard: Auto-detects system preference

### Custom CSS
Add to any HTML dashboard:
```css
/* Custom theme */
:root {
  --primary: #00ff88;
  --background: #0f0f1e;
  --text: #e0e0e0;
}
```

---

## 🚦 Current UI Status

Based on running services:
- ✅ **API Docs**: Available (services running)
- ⚠️ **React Dashboard**: Needs `npm install` first
- ⚠️ **Svelte Dashboard**: Needs `npm install` first
- ✅ **HTML Dashboards**: Ready to open
- ✅ **Terminal UI**: Ready to use

---

## 📋 Quick Commands

```bash
# Check which UIs are available
ls -d */dashboard* */ui* */*UI*

# Start the best dashboard for squad management
cd sophia-intel-app && npm install && npm run dev

# Quick status in terminal (no UI needed)
python3 sophia_squad_cli.py status

# Interactive terminal dashboard
python3 sophia_squad_cli.py dashboard
```

---

*Yes, there are multiple UIs available! The system has both web-based dashboards and a terminal UI for complete control and monitoring of the squad systems.*

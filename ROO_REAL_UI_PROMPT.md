# 🎨 ROO: UPGRADE THE UI FOR REAL AI SWARMS

## YOUR MISSION: Make the UI show REAL swarm activity and coordination

---

## 🎯 OBJECTIVE

Transform the current mock UI into a living, breathing command center that shows ACTUAL AI swarms working in real-time.

---

## 📍 CURRENT SITUATION

### What Exists

- Modern React dashboard at localhost:3000/dashboard
- Real-time WebSocket connections
- Static metrics that don't update

### What Needs to be REAL

- Live WebSocket connections to backend
- Real-time swarm coordination visualization
- Actual agent activity monitoring
- Dynamic performance metrics

---

## 🛠️ YOUR IMPLEMENTATION TASKS

### 1. Enhance Modern React Dashboard Components

Add WebSocket connection for REAL updates:

```javascript
// Connect to REAL backend WebSocket
class SwarmWebSocket {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket("ws://localhost:8000/ws/swarm");

    this.ws.onopen = () => {
      console.log("🔌 Connected to Real AI Backend");
      this.reconnectAttempts = 0;
      this.updateStatus("connected");
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleRealUpdate(data);
    };

    this.ws.onclose = () => {
      this.updateStatus("disconnected");
      this.reconnect();
    };
  }

  handleRealUpdate(data) {
    // Update UI with REAL swarm activity
    if (data.type === "agent_status") {
      updateAgentStatus(data);
    } else if (data.type === "coordination") {
      showCoordination(data);
    } else if (data.type === "metrics") {
      updateMetrics(data);
    }
  }
}
```

### 2. Create 3D Swarm Visualization

Add Three.js network visualization:

```html
<!-- Add to React dashboard component -->
<div id="swarm-3d-viz" style="width: 100%; height: 400px;"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
  class Swarm3DVisualization {
    constructor(containerId) {
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000,
      );
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

      this.agents = {};
      this.connections = [];

      this.init(containerId);
    }

    init(containerId) {
      const container = document.getElementById(containerId);
      this.renderer.setSize(container.offsetWidth, container.offsetHeight);
      container.appendChild(this.renderer.domElement);

      // Dark space background
      this.scene.background = new THREE.Color(0x0a0a0a);

      // Add lighting
      const ambientLight = new THREE.AmbientLight(0x404040);
      this.scene.add(ambientLight);

      const pointLight = new THREE.PointLight(0x00ffff, 1, 100);
      pointLight.position.set(10, 10, 10);
      this.scene.add(pointLight);

      this.camera.position.z = 20;

      this.animate();
    }

    addAgent(id, type, position) {
      // Create glowing sphere for agent
      const geometry = new THREE.SphereGeometry(0.5, 32, 32);
      const material = new THREE.MeshPhongMaterial({
        color: this.getColorForType(type),
        emissive: this.getColorForType(type),
        emissiveIntensity: 0.5,
      });

      const agent = new THREE.Mesh(geometry, material);
      agent.position.set(position.x, position.y, position.z);

      this.agents[id] = agent;
      this.scene.add(agent);
    }

    showCoordination(fromId, toId) {
      // Create animated connection line
      const from = this.agents[fromId].position;
      const to = this.agents[toId].position;

      const geometry = new THREE.BufferGeometry().setFromPoints([from, to]);
      const material = new THREE.LineBasicMaterial({
        color: 0x00ff00,
        linewidth: 2,
        opacity: 0.8,
        transparent: true,
      });

      const line = new THREE.Line(geometry, material);
      this.scene.add(line);

      // Animate and fade out
      this.animateConnection(line);
    }

    animateConnection(line) {
      // Pulse and fade animation
      let opacity = 1.0;
      const fade = setInterval(() => {
        opacity -= 0.02;
        line.material.opacity = opacity;
        if (opacity <= 0) {
          this.scene.remove(line);
          clearInterval(fade);
        }
      }, 50);
    }

    getColorForType(type) {
      const colors = {
        strategic: 0x00ffff, // Cyan
        coding: 0xff00ff, // Magenta
        debate: 0xffff00, // Yellow
        coordinator: 0xff0000, // Red
      };
      return colors[type] || 0xffffff;
    }

    animate() {
      requestAnimationFrame(() => this.animate());

      // Rotate agents
      Object.values(this.agents).forEach((agent) => {
        agent.rotation.y += 0.01;
      });

      this.renderer.render(this.scene, this.camera);
    }

    updateFromWebSocket(data) {
      // Update visualization based on real data
      if (data.type === "agent_spawn") {
        this.addAgent(data.id, data.agentType, data.position);
      } else if (data.type === "coordination") {
        this.showCoordination(data.from, data.to);
      }
    }
  }

  // Initialize 3D visualization
  const viz3d = new Swarm3DVisualization("swarm-3d-viz");
</script>
```

### 3. Real-Time Metrics Dashboard

Update metrics with ACTUAL data:

```javascript
class MetricsDashboard {
  constructor() {
    this.metrics = {
      messagesPerSecond: 0,
      activeAgents: 0,
      tasksCompleted: 0,
      avgResponseTime: 0,
      coordinationScore: 0,
    };

    this.charts = {};
    this.initCharts();
  }

  initCharts() {
    // Create live updating charts
    this.charts.performance = new Chart(document.getElementById("perfChart"), {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Response Time (ms)",
            data: [],
            borderColor: "#00ffff",
            tension: 0.4,
          },
        ],
      },
      options: {
        animation: { duration: 0 },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }

  updateFromBackend(data) {
    // Update with REAL metrics
    this.metrics = { ...this.metrics, ...data };

    // Update display
    document.getElementById("msgRate").textContent =
      this.metrics.messagesPerSecond;
    document.getElementById("activeAgents").textContent =
      this.metrics.activeAgents;
    document.getElementById("taskCount").textContent =
      this.metrics.tasksCompleted;

    // Update charts
    this.updateCharts(data);
  }

  updateCharts(data) {
    const now = new Date().toLocaleTimeString();

    // Add new data point
    this.charts.performance.data.labels.push(now);
    this.charts.performance.data.datasets[0].data.push(data.responseTime);

    // Keep last 20 points
    if (this.charts.performance.data.labels.length > 20) {
      this.charts.performance.data.labels.shift();
      this.charts.performance.data.datasets[0].data.shift();
    }

    this.charts.performance.update();
  }
}
```

### 4. Activity Feed with Real Events

```javascript
class ActivityFeed {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.activities = [];
    this.maxActivities = 20;
  }

  addActivity(activity) {
    const entry = {
      timestamp: new Date(),
      type: activity.type,
      message: activity.message,
      swarm: activity.swarm,
      severity: activity.severity || "info",
    };

    this.activities.unshift(entry);
    if (this.activities.length > this.maxActivities) {
      this.activities.pop();
    }

    this.render();
  }

  render() {
    this.container.innerHTML = this.activities
      .map(
        (activity) => `
            <div class="activity-item ${activity.severity}">
                <span class="time">[${activity.timestamp.toLocaleTimeString()}]</span>
                <span class="icon">${this.getIcon(activity.type)}</span>
                <span class="message">${activity.message}</span>
            </div>
        `,
      )
      .join("");
  }

  getIcon(type) {
    const icons = {
      coordination: "🔄",
      execution: "⚡",
      completion: "✅",
      error: "❌",
      spawn: "🚀",
      memory: "🧠",
    };
    return icons[type] || "📌";
  }
}
```

### 5. Enhanced Message Streaming

```javascript
async function sendStreamMessage() {
  const input = document.getElementById("messageInput");
  const message = input.value;
  if (!message) return;

  addMessage("user", message);
  input.value = "";

  // Show real-time streaming
  const aiMessageDiv = addMessage("ai", "", true);

  try {
    const response = await fetch("http://localhost:8000/teams/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        team_id: selectedTeam,
        stream: true,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.content) {
              fullResponse += data.content;
              // Update message with streaming content
              aiMessageDiv.innerHTML = `<strong>🤖 ${selectedTeam}:</strong> ${marked.parse(
                fullResponse,
              )}`;

              // Show typing indicator
              if (!data.done) {
                aiMessageDiv.innerHTML += '<span class="typing">▊</span>';
              }
            }

            // Update metrics
            if (data.metrics) {
              dashboard.updateFromBackend(data.metrics);
            }

            // Show coordination
            if (data.coordination) {
              viz3d.showCoordination(
                data.coordination.from,
                data.coordination.to,
              );
            }
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    }
  } catch (error) {
    aiMessageDiv.innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
  }
}
```

### 6. Status Indicators

```javascript
class SystemStatus {
  constructor() {
    this.statuses = {
      backend: "checking",
      openrouter: "checking",
      redis: "checking",
      websocket: "checking",
    };

    this.checkHealth();
    setInterval(() => this.checkHealth(), 5000);
  }

  async checkHealth() {
    // Check backend
    try {
      const response = await fetch("http://localhost:8000/health");
      const data = await response.json();
      this.updateStatus("backend", "online");
      this.updateStatus(
        "openrouter",
        data.openrouter === "connected" ? "online" : "offline",
      );
    } catch {
      this.updateStatus("backend", "offline");
    }

    // Update UI
    this.render();
  }

  updateStatus(service, status) {
    this.statuses[service] = status;
  }

  render() {
    Object.entries(this.statuses).forEach(([service, status]) => {
      const element = document.getElementById(`status-${service}`);
      if (element) {
        element.className = `status-indicator ${status}`;
        element.title = `${service}: ${status}`;
      }
    });
  }
}
```

---

## 🚀 INTEGRATION STEPS

1. **Update React dashboard components** with all these enhancements
2. **Add Chart.js** for metrics visualization
3. **Add Three.js** for 3D swarm network
4. **Connect WebSocket** to real backend
5. **Style with animations** for cyberpunk feel

---

## ✅ SUCCESS CRITERIA

Your enhanced UI MUST:

1. **Show REAL agent activity** not fake animations
2. **Display ACTUAL coordination** between swarms
3. **Update metrics in REAL-TIME** from backend
4. **Visualize message flow** between agents
5. **Stream responses CHARACTER BY CHARACTER**
6. **Show system health** with live indicators
7. **Handle errors gracefully** with reconnection

---

## 🎨 VISUAL REQUIREMENTS

- **Glowing neon effects** for active connections
- **Smooth animations** for state changes
- **Particle effects** for message transmission
- **Gradient backgrounds** for depth
- **Responsive layout** that scales
- **Dark theme** with bright accents

---

## 🧪 TEST SCENARIOS

1. **Connection Test**: UI should auto-reconnect if backend restarts
2. **Streaming Test**: Characters should appear smoothly
3. **Coordination Test**: 3D viz should show agent interactions
4. **Metrics Test**: Charts should update every second
5. **Error Test**: Graceful degradation if backend fails

---

## 🔥 MAKE IT SPECTACULAR

This isn't just a UI update - it's creating a COMMAND CENTER for AI coordination. Make it feel like:

- Mission Control for AI
- A cyberpunk hacker interface
- Real-time battle coordination
- Living, breathing intelligence

When done, users should feel like they're commanding an actual AI army, not clicking buttons on a webpage!

GO MAKE IT FUCKING AMAZING! 🚀

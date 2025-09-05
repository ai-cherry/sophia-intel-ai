# Agent Factory System

A comprehensive, production-ready agent and swarm management system for Sophia and Artemis AI platforms. The Agent Factory provides centralized inventory management, pre-built agent catalogs, and turnkey swarm creation capabilities.

## 🎯 Key Features

- **Centralized Agent Inventory System** - One place for all agent creation and management
- **Pre-built Agent Catalog** - Reusable catalog of specialized agents with capabilities
- **Configuration-driven Swarm Assembly** - Swarms as configurations selecting from inventory
- **Turnkey Design** - Everything ready-to-use with minimal setup
- **Production-ready** - Comprehensive database schema, API endpoints, and UI components
- **Extensible Architecture** - Easy to add new agent types and swarm patterns

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Factory System                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   Agent Catalog │  │ Swarm Templates │  │ UI Components   ││
│  │                 │  │                 │  │                 ││
│  │ • Pre-built     │  │ • Dev Team      │  │ • Dashboard     ││
│  │   Specialists   │  │ • BI Team       │  │ • Agent Cards   ││
│  │ • Capabilities  │  │ • Security Team │  │ • Swarm Builder ││
│  │ • Personalities │  │ • Custom        │  │ • Templates     ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                     Core Factory Engine                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Inventory Mgmt  │  │  Swarm Builder  │  │ API Endpoints   ││
│  │                 │  │                 │  │                 ││
│  │ • Agent CRUD    │  │ • Auto-selection│  │ • REST API      ││
│  │ • Search/Filter │  │ • Template-based│  │ • Authentication││
│  │ • Performance   │  │ • Custom Config │  │ • Validation    ││
│  │ • Metrics       │  │ • AGNO Integration│ │ • Error Handling││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Data Persistence Layer                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Agent Blueprints│  │ Swarm Instances │  │ Execution Logs  ││
│  │                 │  │                 │  │                 ││
│  │ • Metadata      │  │ • Configuration │  │ • Performance   ││
│  │ • Capabilities  │  │ • Agent Mapping │  │ • Success Rates ││
│  │ • Performance   │  │ • Templates     │  │ • Cost Tracking ││
│  │ • Versions      │  │ • Lifecycle     │  │ • Analytics     ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
app/factory/
├── agent_factory.py           # Main factory class with inventory management
├── agent_catalog.py          # Pre-built specialized agents catalog
├── database_schema.py        # SQLAlchemy models for persistence
├── ui/
│   ├── agent_factory_dashboard.html    # Standalone HTML dashboard
│   ├── AgentFactoryComponents.jsx      # React components
│   └── AgentFactoryStyles.css          # CSS styles
└── README.md                 # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install fastapi sqlalchemy pydantic

# For UI development (optional)
npm install react react-dom
```

### 2. Initialize the Factory

```python
from app.factory.agent_factory import AgentFactory

# Create factory instance
factory = AgentFactory(catalog_path="./agent_catalog")

# Factory automatically loads pre-built agents
print(f"Loaded {len(factory.inventory)} agents")
```

### 3. Use Pre-built Agents

```python
# List available agents
agents = factory.list_agent_blueprints()
print(f"Available agents: {len(agents)}")

# Search for specific capabilities
developers = factory.search_agent_blueprints("developer")
security_agents = factory.list_agent_blueprints({'specialty': 'security'})

# Create agent instance
agent_id = factory.create_agent_from_blueprint('architect_senior_v1')
```

### 4. Create Swarms from Templates

```python
# List available swarm templates
templates = factory.get_swarm_templates_from_inventory()

# Create swarm from template
swarm_id = factory.create_swarm_from_template('software_dev_team')

# Create custom swarm
custom_swarm_config = {
    'name': 'My Custom Team',
    'required_specialties': ['architect', 'developer', 'tester'],
    'max_agents': 5
}
custom_swarm_id = factory.create_swarm_from_inventory(custom_swarm_config)
```

## 🎨 UI Integration

### Standalone HTML Dashboard

Open `ui/agent_factory_dashboard.html` in a browser for a complete dashboard experience:

```html
<!-- Fully functional dashboard with no dependencies -->
<script src="ui/agent_factory_dashboard.html"></script>
```

### React Components

```jsx
import {
  AgentFactoryDashboard,
  useAgentFactory,
} from "./ui/AgentFactoryComponents";
import "./ui/AgentFactoryStyles.css";

function App() {
  return (
    <AgentFactoryDashboard
      defaultTab="inventory"
      onSwarmCreated={(result) => console.log("Swarm created:", result)}
      onAgentSelected={(agent, selected) =>
        console.log("Agent selected:", agent.name)
      }
    />
  );
}
```

### Individual Components

```jsx
import {
  AgentCard,
  SwarmTemplateCard,
  AgentGrid,
} from "./ui/AgentFactoryComponents";

// Use individual components
<AgentGrid
  agents={agents}
  selectedAgents={selected}
  onAgentSelect={handleSelect}
  onAgentViewDetails={handleDetails}
/>;
```

## 🔧 API Endpoints

The factory automatically exposes comprehensive REST API endpoints:

### Agent Inventory

```http
# List agents with filtering
GET /api/factory/inventory/agents?specialty=developer&capabilities=coding

# Get specific agent
GET /api/factory/inventory/agents/{agent_id}

# Create custom agent
POST /api/factory/inventory/agents
{
  "name": "Custom Agent",
  "specialty": "developer",
  "capabilities": ["coding", "testing"],
  "description": "My custom agent"
}

# Create agent instance
POST /api/factory/inventory/agents/{agent_id}/create
```

### Swarm Management

```http
# List swarm templates
GET /api/factory/inventory/swarm-templates

# Create swarm from template
POST /api/factory/inventory/swarms/from-template/{template_id}

# Create custom swarm
POST /api/factory/inventory/swarms/create
{
  "name": "My Team",
  "required_specialties": ["architect", "developer"],
  "max_agents": 3
}

# Get swarm details
GET /api/factory/inventory/swarms/{swarm_id}/details
```

### Analytics and Stats

```http
# Inventory statistics
GET /api/factory/inventory/stats

# Available specialties
GET /api/factory/inventory/specialties

# Available capabilities
GET /api/factory/inventory/capabilities

# Health check
GET /api/factory/health
```

## 🧑‍💻 Pre-built Agent Catalog

The system includes a comprehensive catalog of specialized agents:

### Development Team

- **Senior Software Architect** - System design and architecture decisions
- **Senior Full-Stack Developer** - End-to-end application development
- **Frontend Specialist** - UI/UX implementation expert
- **Backend Specialist** - API and infrastructure expert
- **DevOps Engineer** - Infrastructure automation and deployment
- **QA Engineer** - Quality assurance and testing expert
- **Security Specialist** - Application and infrastructure security

### Business Intelligence Team

- **Business Analyst** - Requirements and process analysis
- **Data Scientist** - Advanced analytics and machine learning
- **Product Manager** - Product strategy and roadmap management

Each agent includes:

- **Detailed Capabilities** - Specific skills and expertise areas
- **Personality Traits** - Interaction styles and approaches
- **Performance Metrics** - Success rates and usage statistics
- **Optimized Configurations** - Model settings and parameters
- **System Prompts** - Specialized instructions and context

## 🏭 Swarm Templates

Pre-configured swarm templates for common use cases:

### Software Development Team

- **Required**: Architect, Developer, Tester
- **Optional**: DevOps, Security
- **Execution**: Hierarchical
- **Best for**: Full-stack application development

### Business Intelligence Team

- **Required**: Business Analyst, Data Scientist
- **Optional**: Product Manager
- **Execution**: Parallel analysis
- **Best for**: Data-driven insights and decision making

### Security Assessment Team

- **Required**: Security Specialist, Analyst
- **Optional**: Architect
- **Execution**: Linear assessment
- **Best for**: Comprehensive security analysis

## 📊 Database Schema

Comprehensive data models for production deployment:

```python
# Core tables
- agent_blueprints      # Agent definitions and metadata
- swarm_templates      # Reusable swarm configurations
- swarm_instances      # Created swarm instances
- swarm_executions     # Execution history and results
- agent_executions     # Individual agent performance
- user_preferences     # User customizations and favorites

# Features
- Full audit trail
- Performance metrics
- Cost tracking
- User personalization
- Template versioning
```

## ⚙️ Configuration

### Environment Variables

```bash
# API Configuration
AGENT_API_PORT=8003
SOPHIA_ENV=production

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/agent_factory

# Authentication (optional)
ENABLE_API_KEY_AUTH=true
```

### Factory Configuration

```python
# Custom catalog path
factory = AgentFactory(catalog_path="/custom/path/to/catalog")

# Load existing catalog
factory._load_catalog_from_file(Path("my_catalog.json"))

# Save current state
factory._save_comprehensive_catalog()
```

## 🔒 Security Features

- **API Authentication** - Token-based access control
- **Input Validation** - Comprehensive request validation
- **Rate Limiting** - Protection against abuse
- **Audit Logging** - Complete operation tracking
- **Access Control** - Role-based permissions
- **Data Encryption** - Secure data storage

## 📈 Monitoring and Analytics

### Performance Metrics

- Agent success rates and response times
- Swarm execution statistics
- Cost tracking and optimization
- Usage patterns and trends

### Dashboards

- Real-time inventory status
- Performance analytics
- Cost analysis
- User activity monitoring

## 🧪 Testing

```python
# Run factory tests
python -m pytest app/factory/tests/

# Test API endpoints
python -m pytest app/factory/tests/test_api.py

# Test UI components
npm test
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim
COPY app/factory /app/factory
RUN pip install -r requirements.txt
EXPOSE 8003
CMD ["uvicorn", "app.factory.agent_factory:router", "--host", "0.0.0.0", "--port", "8003"]
```

### Production Setup

1. **Database Setup** - Initialize PostgreSQL with schema
2. **Environment Configuration** - Set production environment variables
3. **Load Balancer** - Configure for high availability
4. **Monitoring** - Set up logging and metrics collection
5. **Backup Strategy** - Regular database backups

## 🔮 Future Enhancements

### Phase 2: Advanced Features

- **AI-Powered Agent Recommendations** - ML-based agent selection
- **Dynamic Agent Learning** - Agents that improve over time
- **Advanced Swarm Patterns** - More sophisticated execution modes
- **Visual Swarm Builder** - Drag-and-drop swarm creation
- **Integration Marketplace** - Third-party agent extensions

### Phase 3: Enterprise Features

- **Multi-tenant Support** - Organization-level isolation
- **Advanced Analytics** - Predictive performance modeling
- **Compliance Framework** - SOC2, GDPR compliance
- **Enterprise SSO** - SAML, OAuth integration
- **Advanced Workflow Engine** - Complex multi-swarm orchestration

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch** - `git checkout -b feature/amazing-feature`
3. **Add Tests** - Ensure comprehensive test coverage
4. **Update Documentation** - Keep README and docs current
5. **Submit Pull Request** - Detailed description of changes

## 📚 Additional Resources

- [Agent Configuration Guide](../core/agent_config.py)
- [Swarm Base Architecture](../swarms/core/swarm_base.py)
- [API Documentation](./api_docs.md)
- [UI Component Guide](./ui/README.md)
- [Database Migration Guide](./migrations/README.md)

## 📝 License

This project is part of the Sophia Intelligence AI platform.

---

**Built with ❤️ for the AI-powered future**

_The Agent Factory system represents a new paradigm in AI agent management, providing the foundation for scalable, intelligent swarm orchestration._

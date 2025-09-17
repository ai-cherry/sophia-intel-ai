# Sophia Intel AI - Next Phase Implementation Plan

## Executive Summary

Following comprehensive audit of the current Sophia Intel AI dashboard architecture, integration status, and framework capabilities, this document outlines a three-phase implementation plan focusing on:

1. **Unified Sophia Chat Enhancement** - Full business data connectivity
2. **Project Management Dashboard Enrichment** - OKR alignment with Gong/Slack context
3. **Sales Coach Agent Implementation** - Dedicated Agno v2-powered coaching system

## Current State Analysis

### 🔄 Microsoft Integration Status
- **Environment**: Client secret VALUE now configured correctly (`k5X8Q~DssQV1BTrJ2bw5cqjcuW_7RZyThcKMmbf2`)
- **Missing**: Tenant ID required to complete authentication
- **Client ID**: Using `768ceef7-f028-4825-8b17-3f635cd98287` (from secret ID - needs verification)
- **Status**: Ready for testing once tenant ID provided

### 📊 Airtable Integration Inventory

**Current Configuration** (`airtable_config.json`):
- **Base ID**: `appBOVJqGE166onrD`
- **API Key**: Configured (`patuojzcFCHtcwkH3.2d1b20fd467f58319534f2abb02899d32390e1db02ffa226aa08c084bd21ce5d`)
- **Tables Mapped**:
  - Knowledge Base
  - Insights
  - Conversations

**OKR Alignment Structure** (`app/foundational_knowledge/airtable_sync.py`):
- **Employee Roster**: Name, Role, Department, Email + integration IDs (Linear, Asana, Gong)
- **Strategic Initiatives**: Initiative, Description, Owner, Status, Priority, Target Date
- **Executive Decisions**: Decision, Context, Rationale, Impact, Stakeholders

**Data Classification Levels**:
- CONFIDENTIAL (Employee data)
- PROPRIETARY (Strategic initiatives)
- RESTRICTED (Executive decisions)

### 🤖 Agno v2 Framework Assessment

**Current Capabilities** (`config/agents/agno_workspaces.json`):
- **Platform Hardening Agent** (v2.3.0): Infrastructure compliance
- **DataOps Schema Migrator** (v1.4.1): Database migrations
- **Experiment Launcher** (v1.1.0): Feature flag management

**Orchestrator** (`app/agno/orchestrator.py`):
- Sales pipeline workflows
- Financial analysis workflows
- Customer success workflows
- Built-in workflow tracking and error handling

## Implementation Plan

### Phase A: Sophia Chat Hardening (Weeks 1-2)
**Priority**: HIGH - Foundation for all other enhancements

#### Backend Enhancement
1. **Data Source Integration**
   - **File**: `app/api/services/unified_chat.py`
   - **Actions**:
     - Connect Gong API for call transcripts
     - Integrate Slack message history
     - Link Airtable OKR data
     - Add Microsoft Graph (emails/calendar) once tenant ID provided

2. **Memory & Context Management**
   - **File**: `services/chat-service/`
   - **Actions**:
     - Implement conversation persistence
     - Add cross-session memory
     - Enable context switching between data sources

3. **API Hardening**
   - **File**: `pages/api/chat/query.ts`
   - **Actions**:
     - Replace fallback responses with live data
     - Add WebSocket support for real-time streaming
     - Implement citation system for data sources

#### Frontend Enhancement
1. **Chat Interface** (`src/components/sophia/UnifiedSophiaChat.tsx`)
   - Remove fallback mode indicators
   - Add data source badges
   - Implement citation display
   - Add typing indicators and status

2. **Environment Dependencies**
   ```env
   # Required for Phase A
   GONG_ACCESS_KEY=<provided>
   GONG_CLIENT_SECRET=<provided>
   SLACK_BOT_TOKEN=<configured>
   AIRTABLE_API_KEY=<configured>
   MICROSOFT_TENANT_ID=<needed>
   ```

### Phase B: Project Management Alignment (Weeks 3-4)
**Priority**: MEDIUM - Strategic value delivery

#### OKR Integration Enhancement
1. **Enhanced Project Overview** (`app/api/routers/projects.py`)
   - Map projects to Strategic Initiatives table
   - Calculate OKR alignment scores
   - Identify misalignment warnings
   - Add project health metrics

2. **Context Enrichment**
   - **Gong Integration** (`app/connectors/gong.py`):
     - Extract customer mentions per project
     - Sentiment analysis on project-related calls
     - Deal stage correlation

   - **Slack Integration** (`app/connectors/slack.py`):
     - Project channel activity metrics
     - Team engagement indicators
     - Issue escalation detection

3. **Frontend Updates** (`src/components/tabs/ProjectManagementTab.tsx`)
   - **New Columns**:
     - OKR Alignment Score
     - Customer Sentiment
     - Team Activity
     - Risk Indicators

   - **Detail Drawers**:
     - Related Gong calls
     - Slack discussion threads
     - Airtable OKR connections
     - Misalignment alerts

#### Data Pipeline
```mermaid
graph LR
    A[Airtable OKRs] --> D[Alignment Engine]
    B[Project Data] --> D
    C[Gong Calls] --> D
    E[Slack Messages] --> D
    D --> F[Project Dashboard]
```

### Phase C: Sales Coach Agent (Weeks 5-6)
**Priority**: MEDIUM - Team performance optimization

#### Agno v2 Sales Coach Architecture
1. **New Agent Definition** (`config/agents/agno_workspaces.json`)
   ```json
   {
     "id": "AGN_SALES_COACH_v2",
     "name": "AI Sales Coach",
     "description": "Analyzes sales activities across Gong, Microsoft, and Slack for coaching insights",
     "owner": "Sales Operations",
     "tags": ["sales", "coaching", "performance"],
     "version": "2.0.0",
     "data_sources": ["gong", "microsoft365", "slack"],
     "coaching_modes": ["individual", "team", "account"]
   }
   ```

2. **Backend Implementation**
   - **File**: `/api/sales-coach/query`
   - **Actions**:
     - Gong call analysis (talk time, questions, objections)
     - Email sentiment and response timing
     - Calendar optimization suggestions
     - Slack collaboration patterns

3. **Frontend Implementation**
   - **New Component**: `src/components/coach/SalesCoachChat.tsx`
   - **Features**:
     - Separate chat interface from Sophia
     - Performance summary cards
     - Individual vs team coaching modes
     - Action item tracking

#### Coaching Insights Engine
```python
# Coaching Analysis Framework
class SalesCoachingEngine:
    def analyze_individual_performance(self, rep_id: str):
        # Gong: Talk ratios, demo skills, objection handling
        # Microsoft: Email response times, meeting prep
        # Slack: Collaboration, help-seeking behavior

    def analyze_team_dynamics(self, team_id: str):
        # Cross-rep collaboration patterns
        # Knowledge sharing metrics
        # Support request patterns

    def generate_coaching_plan(self, analysis_data):
        # Positive reinforcement items
        # Development opportunities
        # Skill-building recommendations
```

## Quick Wins Identified

### 1. Environment Documentation
- **Issue**: Missing consolidated env var documentation
- **Solution**: Create `docs/ENVIRONMENT_VARIABLES.md`
- **Impact**: Faster onboarding, fewer configuration errors

### 2. Health Endpoints Enhancement
- **Issue**: Basic fallback responses in health checks
- **Solution**: Add detailed service status in `/api/*/health`
- **Impact**: Better monitoring and debugging

### 3. Error Handling Standardization
- **Issue**: Inconsistent error response formats
- **Solution**: Implement unified error handler
- **Impact**: Better client error handling

## Risk Assessment & Mitigation

### Phase A Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Missing Microsoft Tenant ID | HIGH | MEDIUM | Request from user, implement graceful degradation |
| API Rate Limits | MEDIUM | LOW | Implement caching, request throttling |
| Data Privacy Concerns | HIGH | LOW | Implement proper data classification, audit logs |

### Phase B Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OKR Schema Changes | MEDIUM | MEDIUM | Version Airtable mappings, implement migration |
| Complex Alignment Logic | MEDIUM | HIGH | Start with simple scoring, iterate |

### Phase C Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Agno v2 Integration Complexity | HIGH | MEDIUM | Prototype first, use existing orchestrator |
| Sales Team Adoption | MEDIUM | MEDIUM | Start with opt-in, gather feedback |

## Recommended Sequencing

### Week 1-2: Foundation
1. Complete Microsoft Graph setup (pending tenant ID)
2. Implement Sophia chat data source connections
3. Add WebSocket streaming infrastructure

### Week 3-4: Strategic Value
1. Enhance project-OKR alignment engine
2. Build context enrichment from Gong/Slack
3. Update PM dashboard with new insights

### Week 5-6: Performance Optimization
1. Implement sales coach agent framework
2. Build coaching insights engine
3. Deploy separate sales coach interface

### Validation Checkpoints
- **End of Week 2**: Sophia chat showing live business data
- **End of Week 4**: Project dashboard with OKR alignment scores
- **End of Week 6**: Sales coach providing actionable insights

## Success Metrics

### Sophia Chat Enhancement
- Response accuracy with business data: >90%
- User engagement increase: >40%
- Query resolution time: <3 seconds

### Project Management Enhancement
- OKR alignment visibility: 100% of projects
- Context enrichment coverage: >80% of active projects
- Misalignment detection accuracy: >85%

### Sales Coach Implementation
- Coaching insight generation: Daily for all reps
- Actionable recommendations: >5 per rep per week
- User adoption rate: >70% within 30 days

---

**Next Actions**:
1. Obtain Microsoft Tenant ID for Graph API completion
2. Prioritize Phase A implementation based on business impact
3. Set up development environment validation checkpoints
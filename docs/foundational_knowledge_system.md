# Foundational Knowledge System Documentation

## Overview

The Foundational Knowledge System is a comprehensive infrastructure for managing, classifying, and synchronizing core business knowledge in the Sophia Intel AI platform. It distinguishes between **foundational** (core business-critical) and **operational** (day-to-day) knowledge, providing versioning, caching, and bidirectional synchronization with Airtable.

## Architecture

### Core Components

#### 1. Knowledge Models (`app/knowledge/models.py`)
- **KnowledgeEntity**: Core data model for knowledge items
- **KnowledgeVersion**: Version tracking for historical changes
- **PayReadyContext**: Business context for Pay.com integration
- **SyncConflict**: Conflict resolution for Airtable sync

#### 2. Foundational Manager (`app/knowledge/foundational_manager.py`)
- CRUD operations with automatic classification
- Redis caching with TTL support
- Version management and rollback capabilities
- Pay-Ready context generation

#### 3. Classification Engine (`app/knowledge/classification_engine.py`)
- AI-powered classification using OpenAI
- Pattern-based classification fallback
- Confidence scoring and thresholds
- Auto-classification on entity creation

#### 4. Storage Adapter (`app/knowledge/storage_adapter.py`)
- Database-agnostic storage layer
- Support for SQLite (local) and PostgreSQL (cloud)
- Thread-safe connections for SQLite
- Batch operations and transactions

#### 5. Versioning Engine (`app/knowledge/versioning_engine.py`)
- Automatic version tracking
- Diff generation between versions
- Rollback to specific versions
- Version history and comparison

#### 6. Airtable Sync (`app/sync/airtable_sync.py`)
- Bidirectional synchronization
- Conflict detection and resolution
- Incremental and full sync modes
- CEO Knowledge Base table mapping

#### 7. Embeddings Integration (`app/knowledge/embeddings_integration.py`)
- Multi-modal embedding generation
- Semantic search across knowledge base
- Meta-tag integration
- Hierarchical embedding structure

## API Endpoints

### CRUD Operations

#### Create Knowledge
```http
POST /api/knowledge/
Authorization: Bearer <token>

{
  "name": "Payment Processing SLA",
  "category": "compliance",
  "classification": "payment_processing",
  "priority": 5,
  "content": {
    "sla_target": "99.9%",
    "response_time": "< 200ms"
  }
}
```

#### Get Knowledge
```http
GET /api/knowledge/{knowledge_id}
```

#### Update Knowledge
```http
PUT /api/knowledge/{knowledge_id}
Authorization: Bearer <token>

{
  "priority": 4,
  "content": {
    "sla_target": "99.95%"
  }
}
```

#### Delete Knowledge
```http
DELETE /api/knowledge/{knowledge_id}
Authorization: Admin API Key
```

### Search & List

#### List All Knowledge
```http
GET /api/knowledge/
  ?classification=payment_processing
  &category=compliance
  &is_active=true
  &limit=100
  &offset=0
```

#### Search Knowledge
```http
GET /api/knowledge/search
  ?query=payment+processing
  &include_operational=false
```

#### List Foundational Knowledge
```http
GET /api/knowledge/foundational
```

### Context & Versioning

#### Get Pay-Ready Context
```http
GET /api/knowledge/context/pay-ready
Authorization: Bearer <token>
```

Response:
```json
{
  "company_info": {...},
  "business_metrics": {...},
  "payment_systems": {...},
  "integrations": {...},
  "compliance": {...}
}
```

#### Get Version History
```http
GET /api/knowledge/{knowledge_id}/versions
```

#### Restore Version
```http
POST /api/knowledge/{knowledge_id}/restore
Authorization: Admin API Key

{
  "version_number": 3
}
```

#### Compare Versions
```http
GET /api/knowledge/{knowledge_id}/compare?v1=2&v2=5
```

### Synchronization

#### Trigger Sync
```http
POST /api/knowledge/sync?sync_type=incremental
Authorization: Admin API Key
```

#### Get Sync Status
```http
GET /api/knowledge/sync/status
```

### Health & Statistics

#### Health Check
```http
GET /health/
```

#### Detailed Health
```http
GET /health/detailed
Authorization: Bearer <token>
```

#### Statistics
```http
GET /api/knowledge/statistics
```

## Knowledge Classifications

### Types
1. **COMPANY_INFO**: Core company information
2. **BUSINESS_METRICS**: Key business metrics and KPIs
3. **PAYMENT_PROCESSING**: Payment system configurations
4. **INTEGRATION_CONFIG**: External service configurations
5. **OPERATIONAL**: Day-to-day operational data
6. **SYSTEM_CONFIG**: System settings and preferences

### Priority Levels
1. **CRITICAL** (5): Mission-critical, immediate attention
2. **HIGH** (4): Important for core operations
3. **MEDIUM** (3): Standard priority
4. **LOW** (2): Nice to have
5. **MINIMAL** (1): Informational only

## Integration with Other Systems

### Embedding System
The foundational knowledge system integrates with the multi-modal embedding system to:
- Generate semantic embeddings for all knowledge entities
- Enable semantic search across the knowledge base
- Support hierarchical embedding structures
- Cache embeddings for performance

### Meta-Tagging System
Integration with meta-tagging provides:
- Automatic semantic role classification
- Complexity assessment
- Risk analysis for modifications
- Capability detection

### Airtable Synchronization
Bidirectional sync with Airtable CEO Knowledge Base:
- Maps to tables: `Company Info`, `Business Metrics`, `Payment Systems`, `Integrations`
- Conflict resolution with version tracking
- Scheduled incremental syncs
- Full sync capability for recovery

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///data/knowledge.db  # or postgresql://...

# Redis Cache
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600

# Airtable
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id

# OpenAI (for classification)
OPENAI_API_KEY=your_api_key

# Authentication
REQUIRE_AUTH=true
JWT_SECRET=your_jwt_secret
ADMIN_API_KEY=your_admin_key

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=60
```

### Database Setup

Run migrations:
```bash
python -m app.database.migrations.002_foundational_knowledge
```

## Usage Examples

### Python SDK

```python
from app.knowledge import FoundationalKnowledgeManager
from app.knowledge.models import KnowledgeEntity, KnowledgeClassification

# Initialize manager
manager = FoundationalKnowledgeManager()

# Create foundational knowledge
entity = KnowledgeEntity(
    name="Payment Gateway Config",
    category="integrations",
    classification=KnowledgeClassification.PAYMENT_PROCESSING,
    content={
        "gateway": "stripe",
        "api_version": "2023-10-16",
        "webhook_secret": "whsec_..."
    },
    is_foundational=True
)

created = await manager.create(entity)

# Search knowledge
results = await manager.search(
    "payment gateway",
    include_operational=False
)

# Get Pay-Ready context
context = await manager.get_pay_ready_context()
print(f"Processing ${context['business_metrics']['total_rent_processed']}")

# Version management
history = await manager.get_version_history(entity.id)
for version in history:
    print(f"v{version.version_number}: {version.change_summary}")
```

### Embeddings Integration

```python
from app.knowledge.embeddings_integration import get_knowledge_embeddings

# Get integration instance
integration = get_knowledge_embeddings()

# Generate embeddings for all foundational knowledge
embeddings = await integration.embed_all_foundational(
    batch_size=10,
    force_regenerate=False
)

# Semantic search
results = await integration.semantic_search(
    query="How much rent has Pay.com processed?",
    top_k=5,
    classification_filter=KnowledgeClassification.BUSINESS_METRICS
)

for entity, score in results:
    print(f"{entity.name}: {score:.3f}")

# Integrate with meta-tagging
meta_tag = await integration.integrate_with_meta_tags(entity)
print(f"Semantic role: {meta_tag.semantic_role.value}")
```

### REST API Client

```javascript
// JavaScript/TypeScript client example
const API_BASE = 'http://localhost:8000/api/knowledge';
const token = 'your_jwt_token';

// Create knowledge
const response = await fetch(API_BASE + '/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Q4 Revenue Target',
    category: 'metrics',
    classification: 'business_metrics',
    priority: 4,
    content: {
      target: 50000000,
      currency: 'USD'
    }
  })
});

const created = await response.json();

// Search knowledge
const searchResponse = await fetch(
  API_BASE + '/search?query=revenue+target',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const results = await searchResponse.json();
```

## Testing

### Run Tests
```bash
# Run all knowledge system tests
python -m pytest tests/test_foundational_knowledge.py -v

# Run specific test categories
python -m pytest tests/test_foundational_knowledge.py::TestKnowledgeModels -v
python -m pytest tests/test_foundational_knowledge.py::TestStorageAdapter -v
python -m pytest tests/test_foundational_knowledge.py::TestClassificationEngine -v
```

### Test Coverage
The test suite covers:
- Model validation and serialization
- Storage CRUD operations
- Classification accuracy
- Version management
- API endpoints
- Authentication and rate limiting
- Airtable synchronization
- Embedding generation

## Monitoring & Maintenance

### Health Checks
- `/health/` - Basic health status
- `/health/detailed` - Component-level health
- `/health/ready` - Readiness probe
- `/health/live` - Liveness probe

### Metrics
Monitored metrics include:
- Total knowledge entries
- Foundational vs operational ratio
- Classification accuracy
- Sync success rate
- Cache hit rate
- API response times

### Maintenance Tasks

#### Daily
- Monitor sync status
- Check error logs
- Review classification accuracy

#### Weekly
- Analyze version history
- Review and resolve sync conflicts
- Update embeddings for modified entities

#### Monthly
- Full Airtable sync
- Cache cleanup
- Performance analysis
- Security audit

## Troubleshooting

### Common Issues

#### Classification Failures
```python
# Fallback to manual classification
entity.classification = KnowledgeClassification.OPERATIONAL
entity.is_foundational = False
```

#### Sync Conflicts
```python
# Resolve conflicts manually
conflicts = await sync_service.get_conflicts()
for conflict in conflicts:
    await sync_service.resolve_conflict(
        conflict.id,
        resolution_strategy="local"  # or "remote"
    )
```

#### Thread Safety (SQLite)
The system uses thread locking for SQLite:
```python
with self._connection_lock:
    # Database operations
```

## Security Considerations

### Authentication
- JWT tokens for standard users
- API keys for service accounts
- Admin keys for privileged operations

### Authorization
- Role-based access control
- Entity-level permissions
- Audit logging for all modifications

### Data Protection
- Encryption at rest (database)
- Encryption in transit (HTTPS)
- Sensitive data masking in logs
- Version history for audit trail

## Performance Optimization

### Caching Strategy
- Redis caching with configurable TTL
- Embedding cache for semantic search
- In-memory cache for frequently accessed entities

### Database Optimization
- Indexed columns for search
- Connection pooling
- Batch operations
- Async processing

### API Optimization
- Rate limiting per endpoint
- Request batching
- Response pagination
- Conditional caching headers

## Roadmap

### Planned Features
1. **GraphQL API** - Alternative to REST for flexible queries
2. **Real-time Sync** - WebSocket-based live updates
3. **ML-Enhanced Classification** - Custom model training
4. **Multi-tenant Support** - Organization-level isolation
5. **Workflow Automation** - Trigger-based knowledge updates
6. **Advanced Analytics** - Knowledge usage patterns and insights

## Support

For issues or questions:
- Check the [API Documentation](/docs/api/foundational_knowledge.yaml)
- Review [Test Cases](/tests/test_foundational_knowledge.py)
- Contact the development team

---

**Last Updated**: 2024-09-05  
**Version**: 1.0.0  
**Status**: Production Ready

# Prompt Library System

A comprehensive prompt management system with Git-like versioning, A/B testing capabilities, and business context awareness for mythology agents in sophia-intel-ai.

## Features

### 🔄 Git-like Version Control
- **Branching**: Create, merge, and manage prompt branches
- **Versioning**: Track all changes with semantic versioning
- **Diffing**: Compare prompt versions with detailed diff views
- **History**: Complete audit trail of all prompt modifications
- **Merging**: Fast-forward, three-way, and manual merge strategies

### 🧪 A/B Testing Framework
- **Test Creation**: Easy setup of prompt A/B tests
- **Traffic Splitting**: Configurable traffic distribution
- **Statistical Analysis**: Automated significance testing
- **Performance Tracking**: Real-time success rate monitoring
- **Winner Selection**: Automated promotion of winning variants

### 🎭 Mythology Agent Integration
- **Centralized Prompts**: All mythology agent prompts in one place
- **Business Context Variants**: PayReady, Gong, market intelligence contexts
- **Template System**: Structured prompts with variable substitution
- **Performance Optimization**: Data-driven prompt improvements

### 📊 Analytics & Insights
- **Performance Metrics**: Success rates, response quality scores
- **Leaderboards**: Top performing prompts by domain/agent
- **Usage Analytics**: Most used prompts and contexts
- **Optimization Suggestions**: AI-driven improvement recommendations

## Architecture

```
app/prompts/
├── __init__.py              # Package exports
├── prompt_library.py        # Core versioning engine
├── mythology_prompts.py     # Agent prompt templates
└── README.md               # This file

app/api/routes/
└── prompt_library.py        # FastAPI endpoints

agent-ui/src/
├── components/prompt-library/
│   ├── PromptLibraryDashboard.tsx  # Main UI
│   └── index.ts                    # Component exports
└── hooks/
    └── usePromptLibrary.ts         # React hook
```

## Core Components

### PromptLibrary
The main engine providing:
- Version control operations (branch, merge, diff)
- A/B test management
- Performance tracking
- Import/export functionality
- Storage abstraction

### MythologyPromptManager
Specialized manager for mythology agents:
- Template-based prompt generation
- Business context awareness
- Performance optimization
- Agent-specific insights

### API Endpoints
RESTful API providing:
- CRUD operations for prompts
- Version control operations
- A/B test management
- Performance analytics
- Search and filtering

### React Dashboard
Comprehensive UI featuring:
- Monaco code editor
- Version history visualization
- A/B test management
- Performance analytics
- Real-time collaboration

## Quick Start

### Backend Setup

1. **Initialize the prompt library:**
```python
from app.prompts import PromptLibrary, MythologyPromptManager

library = PromptLibrary()
manager = MythologyPromptManager(library)
```

2. **Create a new prompt:**
```python
from app.prompts.prompt_library import PromptMetadata

metadata = PromptMetadata(
    domain="sophia",
    agent_name="hermes",
    task_type="market_analysis",
    business_context=["pay_ready"],
    performance_tags=["market_intelligence"]
)

prompt = library.create_prompt(
    prompt_id="hermes_market_analysis_v1",
    content="Your Hermes market analysis prompt here...",
    metadata=metadata,
    commit_message="Initial Hermes market analysis prompt"
)
```

3. **Create branches and variants:**
```python
# Create branch for PayReady context
branch = library.create_branch(
    prompt_id="hermes_market_analysis_v1",
    branch_name="payready-focus",
    description="PayReady-specific market analysis"
)

# Create context variant
variant = manager.create_business_context_variant(
    base_prompt_id="hermes_market_analysis_v1",
    business_context=BusinessContext.PAY_READY,
    context_modifications="Focus on embedded payments and fintech partnerships"
)
```

### Frontend Usage

1. **Use the React hook:**
```typescript
import { usePromptLibrary } from '../hooks/usePromptLibrary';

const MyComponent = () => {
  const {
    prompts,
    createPrompt,
    searchPrompts,
    loading,
    error
  } = usePromptLibrary();
  
  // Component logic here
};
```

2. **Integrate the dashboard:**
```typescript
import { PromptLibraryDashboard } from '../components/prompt-library';

<PromptLibraryDashboard />
```

## API Reference

### Key Endpoints

#### Prompts
- `POST /api/v1/prompts/create` - Create new prompt
- `GET /api/v1/prompts/{prompt_id}` - Get prompt version
- `PUT /api/v1/prompts/{prompt_id}/update` - Update prompt
- `DELETE /api/v1/prompts/{prompt_id}` - Archive prompt
- `GET /api/v1/prompts/{prompt_id}/history` - Get version history
- `POST /api/v1/prompts/search` - Search prompts

#### Version Control
- `POST /api/v1/prompts/{prompt_id}/branches` - Create branch
- `GET /api/v1/prompts/{prompt_id}/branches` - List branches
- `POST /api/v1/prompts/{prompt_id}/merge` - Merge branches
- `GET /api/v1/prompts/{prompt_id}/diff` - Compare versions

#### A/B Testing
- `POST /api/v1/prompts/ab-tests` - Create A/B test
- `POST /api/v1/prompts/ab-tests/{test_id}/results` - Record result
- `GET /api/v1/prompts/ab-tests/{test_id}/results` - Get test results
- `GET /api/v1/prompts/ab-tests` - List active tests

#### Analytics
- `POST /api/v1/prompts/{version_id}/metrics` - Update metrics
- `GET /api/v1/prompts/performance/leaderboard` - Get top performers
- `GET /api/v1/prompts/mythology/{agent_name}/performance` - Agent insights

#### Mythology Specific
- `GET /api/v1/prompts/mythology/{agent}/context/{context}` - Get context prompt
- `POST /api/v1/prompts/mythology/{prompt_id}/context-variant` - Create variant
- `GET /api/v1/prompts/mythology/{prompt_id}/suggestions` - Get optimization tips

## Business Contexts

The system supports specialized business contexts:

- **PAY_READY**: Embedded payments and fintech focus
- **GONG_INTEGRATION**: Sales conversation intelligence
- **MARKET_INTELLIGENCE**: Competitive analysis and trends
- **TECHNICAL_EXCELLENCE**: Code quality and architecture
- **STRATEGIC_PLANNING**: Long-term business strategy

## Performance Tracking

### Metrics
- **success_rate**: Percentage of successful interactions
- **response_quality**: Subjective quality score (1-10)
- **user_satisfaction**: User feedback score
- **execution_time**: Average response generation time
- **token_efficiency**: Tokens per successful interaction

### A/B Testing
- Statistical significance testing
- Confidence interval calculation
- Winner determination
- Automated traffic shifting
- Performance alerts

## Best Practices

### Prompt Development
1. Start with base mythology agent prompts
2. Create business context variants as needed
3. Use semantic versioning (major.minor.patch)
4. Write descriptive commit messages
5. Test prompts before promoting to production

### Version Control
1. Use branches for experimental changes
2. Merge successful experiments to main
3. Tag stable versions for production use
4. Keep commit history clean and meaningful

### A/B Testing
1. Define clear success metrics upfront
2. Ensure sufficient sample sizes
3. Run tests for statistically significant periods
4. Document test results and learnings

### Performance Optimization
1. Monitor prompt performance regularly
2. Act on optimization suggestions
3. A/B test significant changes
4. Maintain prompt performance baselines

## Integration Points

### With Mythology Agents
- Automatic prompt extraction during agent initialization
- Dynamic prompt loading based on context
- Performance feedback integration
- Template variable substitution

### With Business Systems
- PayReady context integration
- Gong conversation analysis prompts
- Market intelligence data integration
- Customer success metrics

### With Analytics
- Performance dashboard integration
- Usage analytics
- ROI tracking
- Business impact measurement

## Future Enhancements

### Planned Features
- [ ] Collaborative editing with conflict resolution
- [ ] Advanced diff algorithms (semantic, not just textual)
- [ ] AI-powered prompt optimization suggestions
- [ ] Integration with external prompt libraries
- [ ] Multi-language prompt support
- [ ] Prompt effectiveness prediction models

### Scalability
- [ ] Distributed storage backends
- [ ] Caching layers for high-traffic prompts
- [ ] Async processing for large operations
- [ ] Horizontal scaling for A/B tests

## Contributing

1. Follow existing code patterns and conventions
2. Add tests for new functionality
3. Update documentation for changes
4. Use type hints in Python code
5. Follow React/TypeScript best practices for frontend

## License

Part of the sophia-intel-ai platform. Internal use only.
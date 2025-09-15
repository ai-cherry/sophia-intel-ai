# Blended Mode Architecture

## Overview

The blended mode architecture integrates multiple custom modes into a cohesive system for advanced code optimization and refinement. This architecture combines the strengths of individual modes (Genetic Algorithm, Prophecy, Socratic, Cascade) through a shared framework, enabling complex multi-step workflows and cross-mode orchestration.

## Core Components

### 1. ModeFramework Base Class
- **Purpose**: Provides shared infrastructure for all custom modes
- **Key Features**:
  - Sequential workflow execution engine
  - Model routing based on workflow phases
  - Unified MCP (Model Context Protocol) client
  - State management across phases
  - Standardized error handling and logging

### 2. Evolutionary Components
- **Purpose**: Reusable genetic algorithm primitives for optimization modes
- **Key Classes**:
  - `Gene`: Basic unit of optimization (algorithm choice, data structure, etc.)
  - `Chromosome`: Complete solution candidate
  - `Population`: Set of candidate solutions for evolution
  - `FitnessFunction`: Configurable evaluation metrics
  - `EvolutionResult`: Standardized result structure

### 3. Mode Factory
- **Purpose**: Generates configurations and creates mode instances
- **Key Features**:
  - Template-based configuration generation
  - JSON serialization/deserialization
  - Mode validation and error checking
  - Multi-mode orchestration capabilities

## Implemented Modes

### Genetic Algorithm Mode
- **Focus**: Evolutionary optimization through genetic principles
- **Workflow**: Initialization → Evaluation → Evolution → Optimization → Synthesis
- **Key Innovation**: Uses population-based optimization with mutation/crossover
- **Model Routing**: Claude (init/synthesis), Deepseek (evaluation), Grok (evolution), Google (optimization)
- **Use Case**: Performance tuning, algorithm selection, parameter optimization

### Prophecy Mode
- **Focus**: Predictive optimization through trend analysis and scenario simulation
- **Workflow**: Trend Analysis → Pattern Recognition → Prediction Generation → Scenario Simulation → Recommendation Synthesis
- **Key Innovation**: Proactive optimization based on historical data patterns
- **Model Routing**: Llama (trend analysis), Deepseek (pattern recognition), Grok (prediction), Google (simulation), Claude (synthesis)
- **Use Case**: Anticipating bottlenecks, planning architectural changes

### Socratic Mode
- **Focus**: Iterative refinement through simulated Socratic dialogue
- **Workflow**: Question Generation → Dialogue Simulation → Response Analysis → Refinement Iteration → Validation Synthesis
- **Key Innovation**: Self-reflective improvement through question-driven analysis
- **Model Routing**: Claude (question/validation), Grok (dialogue), Deepseek (analysis), Grok (refinement)
- **Use Case**: Code review, design refinement, knowledge extraction

### Cascade Mode
- **Focus**: Multi-layer refinement from coarse to ultra-fine optimization
- **Workflow**: Coarse Analysis → Fine-Grained Refinement → Ultra-Fine Tuning → Cross-Layer Validation → Integrated Synthesis
- **Key Innovation**: Layered approach ensuring compatibility across optimization levels
- **Model Routing**: Grok (coarse/fine), Google (ultra-fine), Deepseek (validation), Claude (synthesis)
- **Use Case**: Complex system optimization, multi-objective refinement

## Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Mode Factory  │────│   ModeFramework   │────│   MCP Integration │
│                 │    │  (Base Class)     │    │   (Memory/FS/Git)│
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
         │                         │                        │
         │                         │                        │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│Genetic Algorithm│    │   Prophecy Mode  │    │  Socratic Mode  │
│   (Evolution)   │    │ (Prediction)     │    │(Dialogue/Refine)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                         │                        │
         │                         │                        │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│  Cascade Mode   │◄───┐Multi-Mode Orchestration◄──┘
│ (Layered Refine)│
└─────────────────┘
```

## Multi-Mode Orchestration

The ModeFactory enables complex workflows by chaining modes:

### Example: Complete Optimization Pipeline
1. **Socratic Mode**: Initial analysis through questioning
2. **Prophecy Mode**: Predict future requirements based on insights
3. **Genetic Algorithm Mode**: Evolve optimal solutions for predicted scenarios
4. **Cascade Mode**: Layered refinement of evolved solutions

```python
# Example orchestration
orchestration_result = ModeFactory.orchestrate_modes(
    primary_mode_id="socratic",
    secondary_modes=["prophecy", "genetic-algorithm", "cascade"],
    task_data={
        "code_snippet": "def slow_function(): ...",
        "context": "performance_optimization"
    }
)
```

## Integration Testing

Comprehensive integration tests verify:

- **Data Flow**: Results from one mode properly feed into subsequent modes
- **MCP Persistence**: State maintained across mode boundaries
- **Error Handling**: Graceful degradation when individual modes fail
- **Configuration Validation**: Proper setup and parameter passing
- **Workflow Execution**: Sequential and parallel mode coordination

## Deployment and Usage

### Installation
```bash
# Install core framework
pip install -e .

# Generate mode configurations
python -m agents.core.mode_factory generate_config_json \
    --mode-id genetic-algorithm \
    --output-path modes/genetic_algorithm_mode.json

# Run integration tests
pytest tests/integration/multi_mode_tests.py -v
```

### Usage Patterns

1. **Single Mode Execution**:
```python
from agents.core.mode_factory import ModeFactory

# Create and run single mode
config = ModeFactory.generate_config("genetic-algorithm", "GA Mode")
agent = ModeFactory.create_mode_agent(config)
result = await agent._process_task_impl("task1", {"code_snippet": "def test(): pass"})
```

2. **Multi-Mode Pipeline**:
```python
# Orchestrated workflow
result = ModeFactory.orchestrate_modes(
    primary_mode_id="socratic",
    secondary_modes=["prophecy", "cascade"],
    task_data={"target": "performance"}
)
```

3. **Dynamic Mode Creation**:
```python
# Generate custom mode on-the-fly
custom_config = ModeFactory.generate_config(
    mode_id="custom-optimization",
    workflow_steps=["analyze", "optimize", "validate"],
    model_phases={"analyze": "claude-opus-4.1", "optimize": "grok-5"}
)
agent = ModeFactory.create_mode_agent(custom_config)
```

## Benefits of Blended Architecture

1. **Modularity**: Each mode focuses on specific optimization aspect
2. **Reusability**: Shared components reduce duplication
3. **Scalability**: Parallel execution of compatible modes
4. **Maintainability**: Clear separation of concerns and standardized interfaces
5. **Extensibility**: Easy to add new modes using factory pattern
6. **Validation**: Comprehensive testing across mode boundaries
7. **Persistence**: MCP integration ensures state management
8. **Observability**: Built-in logging and monitoring across all modes

## Future Enhancements

- **Dynamic Model Selection**: ML-based model routing based on runtime conditions
- **Adaptive Workflows**: Self-modifying workflows based on intermediate results
- **Distributed Execution**: Multi-process execution across multiple machines
- **A/B Testing Integration**: Built-in experimentation framework
- **Real-time Monitoring**: Live mode switching based on performance metrics
- **Auto-Configuration**: Automatic mode selection based on code characteristics

---

*Last Updated: 2025-09-15*
*Version: 1.0.0*
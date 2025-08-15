# SOPHIA Agent Swarm Execution Rules

## Core Principles

### 1. Deterministic Workflow
- **Linear progression**: Architect → Senior Dev → Code Review → DevOps → Testing → Documentation
- **No parallel execution** unless explicitly designed for the task
- **Clear handoffs** between agents with structured outputs
- **Rollback capability** if any agent rejects the work

### 2. Quality Gates
- Each agent must **explicitly approve** or **reject** the work from the previous agent
- **No silent failures** - all issues must be documented and addressed
- **Evidence-based decisions** - all approvals must include reasoning
- **Continuous validation** - each step validates the entire pipeline

### 3. Output Standards
- **Structured JSON** for all inter-agent communication
- **Complete artifacts** - no partial or placeholder implementations
- **Verifiable results** - all outputs must be testable/runnable
- **Documentation included** - every deliverable includes usage docs

## Agent Responsibilities

### Architect Agent
**Role**: System design and technical planning
**Inputs**: Mission requirements, constraints, existing codebase
**Outputs**: 
- Technical architecture document
- Implementation plan with phases
- Risk assessment and mitigation strategies
- Interface specifications

**Quality Criteria**:
- Architecture is scalable and maintainable
- All requirements are addressed
- Technical decisions are justified
- Integration points are clearly defined

### Senior Developer (Backend)
**Role**: Backend implementation and API development
**Inputs**: Architecture document, API specifications
**Outputs**:
- Complete backend code implementation
- Database schemas and migrations
- API documentation
- Unit tests for all functions

**Quality Criteria**:
- Code follows established patterns
- All APIs are properly documented
- Error handling is comprehensive
- Performance considerations are addressed

### Senior Developer (Frontend)
**Role**: Frontend implementation and user interface
**Inputs**: UI/UX requirements, API specifications
**Outputs**:
- Complete frontend implementation
- Component library and documentation
- Integration with backend APIs
- Responsive design implementation

**Quality Criteria**:
- UI matches design specifications
- All user interactions are implemented
- Code is modular and reusable
- Accessibility standards are met

### Code Reviewer
**Role**: Code quality assurance and security review
**Inputs**: All code implementations from previous agents
**Outputs**:
- Code review report with findings
- Security vulnerability assessment
- Performance optimization recommendations
- Approved/rejected status with detailed reasoning

**Quality Criteria**:
- All code is reviewed for security issues
- Performance bottlenecks are identified
- Code style and standards are enforced
- Documentation quality is verified

### DevOps Engineer
**Role**: Deployment and infrastructure management
**Inputs**: Approved code, infrastructure requirements
**Outputs**:
- Deployment scripts and configurations
- Infrastructure as Code (IaC) templates
- Monitoring and alerting setup
- CI/CD pipeline configuration

**Quality Criteria**:
- Deployments are automated and repeatable
- Infrastructure is scalable and secure
- Monitoring covers all critical metrics
- Rollback procedures are tested

### Testing Engineer
**Role**: Comprehensive testing and quality validation
**Inputs**: Complete implementation, test requirements
**Outputs**:
- Comprehensive test suite
- Test execution reports
- Performance benchmarks
- Quality assurance sign-off

**Quality Criteria**:
- Test coverage meets minimum thresholds
- All critical paths are tested
- Performance meets requirements
- Security tests are included

### Documentation Specialist
**Role**: Technical documentation and user guides
**Inputs**: Complete implementation, all previous outputs
**Outputs**:
- Technical documentation
- User guides and tutorials
- API documentation
- Deployment guides

**Quality Criteria**:
- Documentation is complete and accurate
- Examples are working and tested
- Information is well-organized
- Updates are synchronized with code changes

## Execution Flow

### Phase 1: Planning and Architecture
1. **Mission Analysis**: Parse requirements and constraints
2. **Architecture Design**: Create technical design document
3. **Planning Council**: Multi-agent debate on approach (if complex)
4. **Approval Gate**: Architecture must be approved before proceeding

### Phase 2: Implementation
1. **Backend Development**: Implement core services and APIs
2. **Frontend Development**: Implement user interface and interactions
3. **Integration**: Ensure frontend and backend work together
4. **Code Review**: Comprehensive review of all implementations

### Phase 3: Deployment and Testing
1. **DevOps Setup**: Configure deployment and infrastructure
2. **Testing**: Execute comprehensive test suite
3. **Performance Validation**: Verify performance requirements
4. **Security Review**: Final security assessment

### Phase 4: Documentation and Delivery
1. **Documentation**: Create all required documentation
2. **Final Review**: Complete system review
3. **Delivery**: Package and deliver final solution
4. **Handoff**: Transfer to operations team

## Error Handling

### Rejection Protocol
1. **Immediate Stop**: If any agent rejects work, the pipeline stops
2. **Root Cause Analysis**: Identify why the rejection occurred
3. **Remediation Plan**: Create plan to address the issues
4. **Restart Point**: Determine where to restart the pipeline

### Quality Failures
1. **Automatic Rollback**: Return to last known good state
2. **Issue Documentation**: Record all quality failures
3. **Process Improvement**: Update rules to prevent recurrence
4. **Re-execution**: Restart from appropriate point

### Communication Failures
1. **Structured Retry**: Attempt communication with backoff
2. **Escalation**: Escalate to human oversight if needed
3. **Fallback Mode**: Use simplified communication if needed
4. **Recovery**: Resume normal operations when possible

## Success Criteria

### Mission Completion
- All agents have approved their respective deliverables
- Complete implementation is tested and verified
- Documentation is complete and accurate
- Deployment is successful and monitored

### Quality Metrics
- Code coverage > 80%
- Security scan passes with no high-severity issues
- Performance meets or exceeds requirements
- All acceptance criteria are met

### Delivery Standards
- All artifacts are production-ready
- Documentation enables independent operation
- Monitoring and alerting are functional
- Rollback procedures are tested and documented


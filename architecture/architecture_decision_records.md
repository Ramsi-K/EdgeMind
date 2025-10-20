# Architecture Decision Records (ADRs)

## ADR-001: Strands Framework Selection for Multi-Agent Coordination

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

EdgeMind requires a multi-agent framework for MEC orchestration with sub-100ms decision-making capabilities. The system needs to coordinate between specialized agents for threshold monitoring, load balancing, and consensus decisions.

### Decision

Use Strands Agents framework as the primary multi-agent coordination system.

### Rationale

- **Native Swarm Support**: Built-in swarm coordination with consensus algorithms
- **MCP Integration**: Native Model Context Protocol support for infrastructure tools
- **Performance Controls**: Configurable timeouts and execution limits for real-time requirements
- **Async Execution**: Full async/await support for non-blocking operations
- **Agent Specialization**: Clear patterns for creating specialized agent roles
- **Production Ready**: Mature framework with comprehensive documentation

### Consequences

**Positive**:

- Standardized multi-agent patterns
- Built-in safety mechanisms (timeouts, handoff limits)
- Excellent MCP tool integration capabilities
- Strong async performance characteristics

**Negative**:

- Framework learning curve for team
- Dependency on external framework updates
- API call overhead in demo mode (mitigated in production with local SLMs)

### Implementation Status

✅ **Completed**: Framework integrated with proper Agent and Swarm initialization

---

## ADR-002: Five-Agent Specialization Architecture

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

MEC orchestration requires multiple specialized capabilities: threshold monitoring, load balancing, resource monitoring, cache management, and decision coordination. Need to determine optimal agent specialization strategy.

### Decision

Implement five specialized agents with distinct responsibilities:

1. **OrchestratorAgent**: Threshold monitoring and swarm triggering
2. **LoadBalancerAgent**: MEC site selection and load distribution
3. **DecisionCoordinatorAgent**: Swarm consensus and final decisions
4. **ResourceMonitorAgent**: Performance metrics and anomaly detection
5. **CacheManagerAgent**: Model caching and predictive preloading

### Rationale

- **Separation of Concerns**: Each agent has a single, well-defined responsibility
- **Parallel Processing**: Agents can work concurrently on different aspects
- **Expertise Modeling**: Each agent can be optimized for its specific domain
- **Fault Isolation**: Failure in one agent doesn't compromise others
- **Scalability**: Individual agents can be scaled based on workload

### Consequences

**Positive**:

- Clear responsibility boundaries
- Easier testing and validation
- Modular system architecture
- Enables specialized system prompts and tools

**Negative**:

- Increased coordination complexity
- More inter-agent communication overhead
- Potential for consensus delays

### Implementation Status

✅ **Completed**: All five agents implemented with specialized system prompts

---

## ADR-003: MCP Tool Architecture for Infrastructure Interaction

**Date**: 2025-01-20
**Status**: Accepted (Implementation Pending)
**Deciders**: EdgeMind Development Team

### Context

Agents need to interact with MEC infrastructure (Kubernetes, monitoring systems, caching layers) in a standardized, testable way. Need to support both simulation and production modes.

### Decision

Use Model Context Protocol (MCP) tools for all infrastructure interactions:

- **metrics_monitor.mcp**: MEC site monitoring and health checks
- **container_ops.mcp**: Kubernetes/Docker scaling operations
- **telemetry.mcp**: Structured logging and metrics collection
- **inference.mcp**: Model caching and execution simulation
- **memory_sync.mcp**: Swarm state coordination and consensus

### Rationale

- **Standardization**: MCP provides consistent tool interface
- **Testability**: Easy to mock and test tool interactions
- **Modularity**: Tools can be developed and deployed independently
- **Simulation Support**: Same interface works for simulation and production
- **Strands Integration**: Native MCP support in Strands framework

### Consequences

**Positive**:

- Clean separation between agent logic and infrastructure
- Easy to switch between simulation and production modes
- Comprehensive testing capabilities
- Standardized tool development patterns

**Negative**:

- Additional development overhead for tool servers
- Network latency for tool calls (mitigated with local deployment)
- Complexity in tool server management

### Implementation Status

❌ **Pending**: Currently using placeholder implementations - **CRITICAL for Phase 2**

---

## ADR-004: Weighted Consensus Algorithm for Swarm Decisions

**Date**: 2025-01-20
**Status**: Accepted (Partially Implemented)
**Deciders**: EdgeMind Development Team

### Context

Swarm decisions need to balance input from different agent specializations. Some agents (LoadBalancer) have more relevant expertise for site selection than others (CacheManager).

### Decision

Implement weighted consensus algorithm with the following weights:

- **LoadBalancerAgent**: 30% (primary site selection expertise)
- **ResourceMonitorAgent**: 25% (performance data authority)
- **OrchestratorAgent**: 25% (overall system context)
- **CacheManagerAgent**: 20% (model availability considerations)

**Consensus Rules**:

- Minimum 60% consensus required for decision
- Minimum 3 agents must participate
- Tie-breaking defers to LoadBalancer recommendation
- Timeout after 5 seconds with fallback to highest-weighted agent

### Rationale

- **Expertise-Based Weighting**: Agents with more relevant knowledge have more influence
- **Fault Tolerance**: System can operate with partial agent participation
- **Performance**: Clear timeout and fallback mechanisms
- **Transparency**: Weighted voting provides auditable decisions

### Consequences

**Positive**:

- Decisions reflect agent expertise levels
- Clear conflict resolution mechanisms
- Auditable decision process
- Fault-tolerant operation

**Negative**:

- Complexity in weight tuning
- Potential for gaming if weights are inappropriate
- Additional consensus calculation overhead

### Implementation Status

⚠️ **Partially Implemented**: System prompts define consensus rules, but actual weighted voting logic needs implementation

---

## ADR-005: Threshold-Based Swarm Activation Strategy

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

System needs to determine when to activate expensive swarm coordination vs. handling situations with single agents or simple logic.

### Decision

Implement threshold-based activation with the following triggers:

- **CPU/GPU Utilization**: >80%
- **Response Time**: >100ms
- **Queue Depth**: >50 requests
- **Network Latency**: >20ms between MEC sites
- **Memory Utilization**: >85%

**Activation Logic**:

- Single threshold breach: Activate swarm with normal priority
- Multiple breaches: Activate swarm with high priority
- Critical breaches (>120% of threshold): Immediate activation
- Severity-based timeout adjustment

### Rationale

- **Performance**: Avoid unnecessary swarm overhead for minor issues
- **Responsiveness**: Ensure critical issues get immediate attention
- **Resource Efficiency**: Balance between responsiveness and computational cost
- **Configurability**: Thresholds can be adjusted based on operational experience

### Consequences

**Positive**:

- Efficient resource utilization
- Predictable activation behavior
- Configurable sensitivity
- Clear escalation paths

**Negative**:

- Risk of delayed response if thresholds are too high
- Potential for threshold oscillation
- Complexity in threshold tuning

### Implementation Status

✅ **Completed**: ThresholdMonitor implements all specified thresholds with proper severity classification

---

## ADR-006: Async/Await Pattern for Real-Time Performance

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

MEC orchestration requires sub-100ms response times. Synchronous operations would block the system and prevent meeting performance targets.

### Decision

Use async/await patterns throughout the system:

- All agent interactions are async
- Swarm coordination uses `invoke_async`
- Threshold monitoring supports async callbacks
- MCP tool calls will be async when implemented

### Rationale

- **Performance**: Non-blocking operations enable concurrent processing
- **Scalability**: System can handle multiple simultaneous requests
- **Responsiveness**: UI and monitoring remain responsive during operations
- **Framework Alignment**: Strands framework is designed for async operation

### Consequences

**Positive**:

- Excellent performance characteristics
- Concurrent request handling
- Responsive system behavior
- Future-proof architecture

**Negative**:

- Increased code complexity
- Async debugging challenges
- Potential for race conditions
- Learning curve for async patterns

### Implementation Status

✅ **Completed**: All major system components use proper async/await patterns

---

## ADR-007: Simulation-First Development Approach

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

Need to develop and demonstrate MEC orchestration capabilities without requiring full MEC infrastructure deployment.

### Decision

Implement simulation-first approach with clear production migration path:

- **Phase 1**: Full simulation with realistic data patterns
- **Phase 2**: Functional MCP tools with real infrastructure APIs
- **Phase 3**: Production deployment with local SLMs

**Simulation Components**:

- Synthetic MEC metrics generation
- Simulated threshold breaches and recovery
- Mock MCP tool responses
- Realistic performance characteristics

### Rationale

- **Development Velocity**: Can develop and test without infrastructure dependencies
- **Demonstration**: Enables stakeholder demos without complex setup
- **Risk Reduction**: Validate logic before production deployment
- **Cost Efficiency**: Avoid infrastructure costs during development

### Consequences

**Positive**:

- Rapid development and iteration
- Easy demonstration and testing
- Lower development costs
- Risk mitigation

**Negative**:

- Gap between simulation and production behavior
- Potential for simulation-specific bugs
- Need for careful production migration planning

### Implementation Status

✅ **Completed**: Comprehensive simulation environment with realistic patterns

---

## ADR-008: Performance Target Definition

**Date**: 2025-01-20
**Status**: Accepted
**Deciders**: EdgeMind Development Team

### Context

MEC orchestration requires specific performance characteristics to be viable for real-time applications.

### Decision

Define the following performance targets:

- **Total Orchestration Decision**: <100ms (95th percentile)
- **Threshold Detection**: <50ms
- **Swarm Consensus**: <50ms (production with local SLMs)
- **MCP Tool Calls**: <10ms each (local deployment)
- **Graceful Degradation**: <150ms under high load

**Demo vs Production Expectations**:

- **Demo Mode**: 2-5 seconds (acceptable for API calls)
- **Production Mode**: <100ms (with local SLMs and MCP tools)

### Rationale

- **Real-Time Requirements**: MEC applications need sub-100ms response times
- **Competitive Advantage**: Significantly faster than cloud-dependent alternatives
- **User Experience**: Responsive system behavior
- **Technical Feasibility**: Achievable with proper architecture

### Consequences

**Positive**:

- Clear performance expectations
- Competitive positioning
- User satisfaction
- Technical validation

**Negative**:

- Aggressive performance requirements
- Need for careful optimization
- Potential architecture constraints

### Implementation Status

✅ **Partially Met**: Demo mode meets relaxed targets, production optimization pending

---

## ADR-009: Error Handling and Fault Tolerance Strategy

**Date**: 2025-01-20
**Status**: Accepted (Implementation Ongoing)
**Deciders**: EdgeMind Development Team

### Context

MEC orchestration system must be highly available and resilient to various failure modes including agent failures, network issues, and infrastructure problems.

### Decision

Implement comprehensive fault tolerance strategy:

- **Circuit Breaker Pattern**: For MEC site health monitoring
- **Graceful Degradation**: Fallback to single-agent decisions
- **Timeout Management**: Configurable timeouts at all levels
- **Retry Logic**: Exponential backoff for transient failures
- **Failover Mechanisms**: Automatic MEC site failover

### Rationale

- **Availability**: System must continue operating during partial failures
- **Reliability**: Predictable behavior under stress
- **Maintainability**: Clear error handling patterns
- **Operational Excellence**: Reduced manual intervention requirements

### Consequences

**Positive**:

- High system availability
- Predictable failure behavior
- Reduced operational overhead
- Better user experience

**Negative**:

- Increased code complexity
- Additional testing requirements
- Performance overhead for error handling

### Implementation Status

⚠️ **Partially Implemented**: Basic error handling in place, comprehensive fault tolerance pending

---

## Summary of Implementation Status

| ADR     | Decision              | Status      | Priority     |
| ------- | --------------------- | ----------- | ------------ |
| ADR-001 | Strands Framework     | ✅ Complete | -            |
| ADR-002 | Agent Specialization  | ✅ Complete | -            |
| ADR-003 | MCP Tool Architecture | ❌ Pending  | **CRITICAL** |
| ADR-004 | Weighted Consensus    | ⚠️ Partial  | High         |
| ADR-005 | Threshold Activation  | ✅ Complete | -            |
| ADR-006 | Async/Await Patterns  | ✅ Complete | -            |
| ADR-007 | Simulation-First      | ✅ Complete | -            |
| ADR-008 | Performance Targets   | ⚠️ Partial  | High         |
| ADR-009 | Fault Tolerance       | ⚠️ Partial  | Medium       |

## Next Steps for Phase 2

1. **Implement MCP Tools** (ADR-003) - Critical blocker
2. **Complete Weighted Consensus** (ADR-004) - High priority
3. **Performance Optimization** (ADR-008) - Production readiness
4. **Enhanced Fault Tolerance** (ADR-009) - Operational excellence

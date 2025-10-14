# Design Document

## Overview

EdgeMind implements a three-layer intelligence architecture with Strands agent swarms deployed at MEC sites near 5G RAN controllers. The system uses threshold-based orchestration to trigger autonomous swarm coordination, ensuring sub-100ms decision making for real-time applications without cloud dependency.

## Architecture

### System Architecture Overview

```
Device Layer (SLM) → MEC Orchestration → Swarm Decision
                           ↓
    ┌─────────────────────────────────────────────┐
    │         MEC Site Intelligence               │
    │  ┌─────────────┐  ┌─────────────────────┐   │
    │  │Orchestrator │  │   Strands Swarm     │   │
    │  │   Agent     │  │ ┌─────┐ ┌─────┐     │   │
    │  │             │  │ │Agent│ │Agent│ ... │   │
    │  │• Thresholds │  │ └─────┘ └─────┘     │   │
    │  │• Triggers   │  │                     │   │
    │  └─────────────┘  └─────────────────────┘   │
    │                                             │
    │  ┌─────────────────────────────────────┐   │
    │  │         MCP Integration Layer       │   │
    │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ │   │
    │  │ │metrics_ │ │container│ │telemetry│ │   │
    │  │ │monitor  │ │_ops     │ │         │ │   │
    │  │ │.mcp     │ │.mcp     │ │.mcp     │ │   │
    │  │ └─────────┘ └─────────┘ └─────────┘ │   │
    │  │ ┌─────────┐ ┌─────────┐             │   │
    │  │ │inference│ │memory_  │             │   │
    │  │ │.mcp     │ │sync.mcp │             │   │
    │  │ └─────────┘ └─────────┘             │   │
    │  └─────────────────────────────────────┘   │
    └─────────────────────────────────────────────┘
                           ↓
              Cloud (Passive Observer)
           - Monitoring & Analytics Only
           - No Real-Time Decisions
```

### Design Principles

**All Strands agents use Model Context Protocol (MCP) connectors to interact with infrastructure, enabling modular tool invocation and shared context across the swarm.**

Key principles:
- Agents are tool-augmented entities, not closed boxes
- Each Strands agent hosts its own MCP client instance, but swarm consensus allows cross-node MCP tool invocation when needed
- Inter-MEC communication occurs over the low-latency network, while tool invocation happens through local MCP interfaces
- MCP tools provide real functionality with synthetic data in simulation environment
- Each agent has a defined manifest.json specifying available tools and capabilities

### Three-Layer Intelligence Model

#### Layer 1: Device Intelligence
- **Purpose**: First-line processing and MEC triggering
- **Technology**: Small Language Models (SLMs), ONNX Runtime
- **Latency Target**: <50ms
- **Capabilities**: Basic inference, immediate response, complexity detection
- **Deployment**: Pre-installed on mobile devices, IoT sensors, edge devices

#### Layer 2: MEC Intelligence (Primary)
- **Purpose**: Real-time orchestration and swarm coordination
- **Technology**: Strands agent swarms in Docker containers
- **Latency Target**: <100ms
- **Capabilities**: Complex reasoning, load balancing, autonomous decision making
- **Deployment**: Kubernetes clusters at MEC sites near RAN controllers

#### Layer 3: Cloud Observability (Passive)
- **Purpose**: Long-term analytics and pattern recognition
- **Technology**: Data aggregation and analytics platforms
- **Latency**: Not critical (observability only)
- **Capabilities**: Historical analysis, compliance reporting, trend monitoring
- **Deployment**: Traditional cloud data centers

### MCP Integration Layer

Each Strands agent is backed by an MCP client that provides access to domain-specific tools:

#### Core MCP Tools

Five MCP tools provide infrastructure access: `metrics_monitor.mcp` (latency/CPU monitoring), `container_ops.mcp` (scaling/deployment), `telemetry.mcp` (logging/reporting), `inference.mcp` (model execution), and `memory_sync.mcp` (swarm coordination). Each tool's configuration (endpoint, functions, simulation mode) is defined in mcp-tools-config.json.

#### Agent MCP Manifests

Each agent has a manifest.json defining its MCP tool access:

```json
{
  "agents": {
    "orchestrator": {
      "tools": ["metrics_monitor", "container_ops", "telemetry", "memory_sync"],
      "capabilities": ["threshold_monitoring", "swarm_triggering"]
    },
    "load_balancer": {
      "tools": ["metrics_monitor", "container_ops", "memory_sync"],
      "capabilities": ["load_distribution", "failover_coordination"]
    },
    "resource_monitor": {
      "tools": ["metrics_monitor", "telemetry", "memory_sync"],
      "capabilities": ["metrics_collection", "anomaly_detection"]
    },
    "cache_manager": {
      "tools": ["inference", "telemetry", "memory_sync"],
      "capabilities": ["model_caching", "predictive_preloading"]
    },
    "decision_coordinator": {
      "tools": ["memory_sync", "telemetry", "metrics_monitor"],
      "capabilities": ["swarm_consensus", "pattern_learning"]
    }
  }
}
```

### Agent-MCP Interaction Flow

**Unified Swarm Coordination Pattern**:
```
Trigger Event → MCP Tool Query → Swarm Sync → Action Execution → Telemetry Logging
```

**Example: Threshold Breach Response**:
1. **Orchestrator** detects breach via `metrics_monitor.get_mec_metrics()`
2. **Orchestrator** triggers swarm via `memory_sync.sync_swarm_state(trigger_data)`
3. **Load Balancer** receives trigger, queries `metrics_monitor.check_site_health()`
4. **Load Balancer** executes `container_ops.scale_containers(target_site)`
5. **Decision Coordinator** logs via `telemetry.log_decision(outcome)`
6. **Cache Manager** adapts via `inference.preload_models(predicted_load)`

**Cross-MEC Tool Invocation**: When swarm consensus requires cross-node coordination, agents use `memory_sync.mcp` to share tool invocation context, enabling distributed MCP operations while maintaining local tool execution.

## Components and Interfaces

### 1. Orchestrator Agent

**Purpose**: Primary controller that monitors thresholds and triggers swarm consensus

**Core Functions & Interfaces**:
- Real-time threshold monitoring (latency, CPU/GPU, queue depth)
- Swarm consensus trigger decision making
- MEC site health assessment
- Performance pattern recognition
```python
class OrchestratorAgent:
    def __init__(self, mcp_client: MCPClient):
        self.metrics_monitor = mcp_client.get_tool("metrics_monitor")
        self.container_ops = mcp_client.get_tool("container_ops")
        self.telemetry = mcp_client.get_tool("telemetry")
        self.memory_sync = mcp_client.get_tool("memory_sync")

    def monitor_thresholds(self) -> OrchestrationDecision:
        metrics = self.metrics_monitor.get_mec_metrics()
        return self._evaluate_thresholds(metrics)

    def trigger_swarm_coordination(self, trigger_reason: str) -> SwarmActivation:
        swarm_state = {"trigger": trigger_reason, "timestamp": time.now()}
        return self.memory_sync.sync_swarm_state(swarm_state)

    def assess_mec_health(self, site_id: str) -> HealthStatus:
        return self.metrics_monitor.check_site_health(site_id)
```

**Deployment**: One primary instance per MEC site with backup instances for failover

### 2. Load Balancer Agent

**Purpose**: Distributes workload across MEC sites using swarm intelligence

**Core Functions & Interfaces**: Dynamic load distribution, MEC site selection, failover coordination, performance optimization
```python
class LoadBalancerAgent:
    def __init__(self, mcp_client: MCPClient):
        self.metrics_monitor = mcp_client.get_tool("metrics_monitor")
        self.container_ops = mcp_client.get_tool("container_ops")
        self.memory_sync = mcp_client.get_tool("memory_sync")

    def balance_load(self, request: InferenceRequest) -> MECSite:
        available_sites = self.metrics_monitor.get_healthy_sites()
        site_scores = {site: self._calculate_site_score(site, request) for site in available_sites}
        selected_site = max(site_scores, key=site_scores.get)
        self.container_ops.scale_containers(selected_site, request.resource_requirements)
        return selected_site

    def handle_failover(self, failed_site: MECSite) -> FailoverPlan:
        backup_sites = self.metrics_monitor.get_backup_sites(failed_site)
        return self.container_ops.deploy_model(backup_sites[0], failed_site.active_models)
```

**Decision Matrix**: MEC site latency (50%), current load capacity (30%), network proximity (15%), site availability (5%)

### 3. Resource Monitor Agent

**Purpose**: Tracks real-time metrics across MEC infrastructure

**Core Functions & Interfaces**: MEC site capacity monitoring, inter-MEC latency tracking, device connectivity assessment, cache performance monitoring
```python
class ResourceMonitorAgent:
    def __init__(self, mcp_client: MCPClient):
        self.metrics_monitor = mcp_client.get_tool("metrics_monitor")
        self.telemetry = mcp_client.get_tool("telemetry")
        self.memory_sync = mcp_client.get_tool("memory_sync")

    def collect_mec_metrics(self, site_id: str) -> MECMetrics:
        metrics = self.metrics_monitor.get_mec_metrics(site_id)
        self.telemetry.send_metrics(metrics)
        return metrics

    def monitor_inter_mec_latency(self, source: str, target: str) -> LatencyMetrics:
        latency = self.metrics_monitor.ping_mec_site(source, target)
        if latency > THRESHOLD:
            self.memory_sync.share_decision_context({"alert": "high_latency", "sites": [source, target]})
        return latency
```

### 4. Cache Manager Agent

**Purpose**: Manages local caching and predictive preloading at MEC sites

**Core Functions & Interfaces**: Local model caching (15-min refresh), response caching, predictive preloading, cache optimization
```python
class CacheManagerAgent:
    def __init__(self, mcp_client: MCPClient):
        self.inference = mcp_client.get_tool("inference")
        self.telemetry = mcp_client.get_tool("telemetry")
        self.memory_sync = mcp_client.get_tool("memory_sync")

    def cache_model(self, model_id: str, mec_site: str) -> CacheStatus:
        cache_result = self.inference.cache_response(model_id, mec_site)
        self.telemetry.log_decision(f"Cached model {model_id} at {mec_site}")
        return cache_result

    def predict_preload(self, usage_patterns: UsagePatterns) -> PreloadPlan:
        swarm_context = self.memory_sync.get_swarm_context()
        predicted_models = self._analyze_patterns(usage_patterns, swarm_context)
        return self.inference.preload_models(predicted_models)
```

### 5. Decision Coordinator Agent

**Purpose**: Coordinates swarm consensus and implements learning algorithms

**Core Functions & Interfaces**: Swarm consensus protocols, pattern recognition, threshold adjustment, anomaly detection
```python
class DecisionCoordinatorAgent:
    def __init__(self, mcp_client: MCPClient):
        self.memory_sync = mcp_client.get_tool("memory_sync")
        self.telemetry = mcp_client.get_tool("telemetry")
        self.metrics_monitor = mcp_client.get_tool("metrics_monitor")

    def coordinate_swarm_decision(self, decision_request: DecisionRequest) -> SwarmConsensus:
        swarm_state = self.memory_sync.get_swarm_context()
        consensus = self.memory_sync.update_consensus(decision_request, swarm_state)
        self.telemetry.log_decision(consensus)
        return consensus

    def detect_anomalies(self, performance_data: PerformanceData) -> AnomalyReport:
        anomalies = self._analyze_performance(performance_data)
        if anomalies:
            self.telemetry.report_anomaly(anomalies)
            self.memory_sync.share_decision_context({"anomalies": anomalies})
        return anomalies
```

**Consensus Algorithm**: Modified Raft protocol with weighted voting, timeout-based decisions, performance-based conflict resolution

## Data Models

### Core Data Structures

```python
@dataclass
class InferenceRequest:
    request_id: str
    content: str
    complexity_score: float
    latency_requirement: int  # milliseconds
    privacy_level: PrivacyLevel
    device_capabilities: DeviceCapabilities
    timestamp: datetime

@dataclass
class MECMetrics:
    site_id: str
    cpu_utilization: float
    gpu_utilization: float
    memory_usage: float
    queue_depth: int
    network_latency: Dict[str, float]  # latency to other MEC sites
    timestamp: datetime

@dataclass
class SwarmDecision:
    decision_id: str
    selected_mec_site: str
    reasoning: str
    confidence_score: float
    fallback_sites: List[str]
    execution_time_ms: int
    timestamp: datetime

@dataclass
class ThresholdConfig:
    latency_threshold_ms: int = 100
    cpu_threshold_percent: float = 80.0
    gpu_threshold_percent: float = 80.0
    queue_depth_threshold: int = 50
    network_latency_threshold_ms: int = 20
```

### Data Flow Architecture

```
Device SLM → Complexity Assessment → MEC Trigger
    ↓
Orchestrator Agent → Threshold Check → Swarm Activation
    ↓
Resource Monitor → Capacity Assessment → Load Balancer
    ↓
Cache Manager → Model Availability → Decision Coordinator
    ↓
Swarm Consensus → MEC Site Selection → Response Execution
    ↓
Performance Logging → Pattern Learning → Threshold Optimization
```

## Error Handling

### Fault Tolerance Strategy

**Circuit Breaker Pattern**:
- Monitor MEC site health with 10-second intervals
- Open circuit after 3 consecutive failures
- Half-open state for gradual recovery testing
- Automatic failover to healthy MEC sites

**Graceful Degradation**:
- Fallback to device-only processing when MEC unavailable
- Cached response serving during MEC site failures
- Reduced functionality mode with core features only
- Automatic recovery when MEC sites return online

**Error Recovery Protocols**:
```python
class ErrorHandler:
    def handle_mec_site_failure(self, failed_site: str) -> RecoveryPlan
    def implement_graceful_degradation(self, failure_type: FailureType) -> DegradationStrategy
    def recover_from_network_partition(self, partition_info: PartitionInfo) -> RecoveryAction
    def handle_swarm_consensus_failure(self, consensus_error: ConsensusError) -> FallbackDecision
```

### Monitoring and Alerting

**Real-time Monitoring**:
- Sub-100ms decision time tracking
- MEC site availability monitoring
- Swarm coordination success rates
- Threshold breach detection and alerting

**Performance Metrics**:
- 95th percentile response times
- MEC site utilization rates
- Cache hit ratios
- Failover frequency and recovery times

## Testing Strategy

### Unit Testing
- Individual agent functionality testing
- Threshold detection algorithm validation
- Swarm consensus protocol testing
- Cache management logic verification

### Integration Testing
- End-to-end swarm coordination testing
- MEC site failover scenario testing
- Device-to-MEC integration validation
- Performance benchmark testing

### Load Testing
- Concurrent request handling (1000+ requests/second)
- MEC site capacity limit testing
- Network partition resilience testing
- Threshold breach response time validation

### Chaos Engineering
- Random MEC site failure injection
- Network latency variation testing
- Agent failure and recovery testing
- Swarm coordination stress testing

## Security Considerations

### Data Protection
- End-to-end encryption for inter-MEC communication
- Local data encryption at rest on MEC sites
- Regional data residency compliance
- Secure key management and rotation

### Access Control
- Role-based access control for MEC site management
- Agent authentication and authorization
- Secure container deployment and runtime
- Audit logging for all orchestration decisions

### Compliance
- GDPR compliance for European deployments
- HIPAA compliance for healthcare use cases
- SOC 2 Type II compliance for enterprise customers
- Regional data sovereignty requirements

## Deployment Architecture

### Container Orchestration with MCP Integration
```yaml
# Kubernetes deployment example with MCP tools
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestrator-agent
  template:
    metadata:
      labels:
        app: orchestrator-agent
    spec:
      containers:
      - name: orchestrator
        image: edgemind/orchestrator:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: MEC_SITE_ID
          value: "mec-site-001"
        - name: MCP_MANIFEST_PATH
          value: "/app/manifests/orchestrator_manifest.json"
        - name: MCP_TOOLS_CONFIG
          valueFrom:
            configMapKeyRef:
              name: mcp-tools-config
              key: tools.json
        volumeMounts:
        - name: mcp-manifests
          mountPath: /app/manifests
        - name: mcp-tools
          mountPath: /app/mcp-tools
      volumes:
      - name: mcp-manifests
        configMap:
          name: agent-manifests
      - name: mcp-tools
        configMap:
          name: mcp-tools-config
```

### MCP Tools Configuration
```json
{
  "mcp_tools": {
    "metrics_monitor": {
      "endpoint": "http://metrics-service:8080",
      "functions": ["get_mec_metrics", "check_site_health", "monitor_thresholds"],
      "synthetic_data": true,
      "simulation_mode": "realistic"
    },
    "container_ops": {
      "endpoint": "http://k8s-api:8080",
      "functions": ["scale_containers", "deploy_model", "restart_failed_agents"],
      "synthetic_data": true,
      "simulation_mode": "kubernetes_mock"
    },
    "telemetry": {
      "endpoint": "http://telemetry-service:8080",
      "functions": ["log_decision", "send_metrics", "report_anomaly"],
      "synthetic_data": true,
      "simulation_mode": "cloud_observer"
    },
    "inference": {
      "endpoint": "http://inference-service:8080",
      "functions": ["run_local_inference", "cache_response", "preload_models"],
      "synthetic_data": true,
      "simulation_mode": "model_simulation"
    },
    "memory_sync": {
      "endpoint": "http://memory-sync:8080",
      "functions": ["sync_swarm_state", "update_consensus", "share_decision_context"],
      "synthetic_data": true,
      "simulation_mode": "distributed_state"
    }
  }
}
```

### MEC Site Infrastructure
- Docker containers for each Strands agent
- Kubernetes for container orchestration and scaling
- Local Redis for caching and inter-agent communication
- Prometheus for metrics collection and monitoring
- Grafana for real-time dashboard visualization

### Network Architecture
- Direct MEC-to-MEC communication using dedicated network links
- 5G network integration for device connectivity
- Edge-optimized routing protocols for minimal latency
- Redundant network paths for fault tolerance

## Performance Optimization

### Latency Optimization
- Agent co-location on the same MEC site for minimal communication overhead
- Pre-compiled decision trees for common scenarios
- Asynchronous processing for non-critical operations
- Connection pooling for inter-MEC communication

### Resource Optimization
- Dynamic container scaling based on load patterns
- Memory-efficient data structures for real-time processing
- CPU affinity optimization for agent processes
- GPU acceleration for complex inference tasks

### Cache Optimization
- Intelligent cache warming based on usage predictions
- Hierarchical caching with local and regional tiers
- Cache coherence protocols for multi-site deployments
- Adaptive TTL based on content volatility

Through MCP-enabled orchestration, EdgeMind transforms Strands agents into active infrastructure participants capable of autonomous reasoning and real-time adaptation.

## Streamlit Dashboard Interface

### Purpose
Provides real-time visibility into MEC orchestration, swarm consensus, and threshold monitoring for demonstration and stakeholder engagement.

### Dashboard Layout

#### Left Sidebar - Control Interface
**Simulation Controls**:
- Latency slider (0-200ms)
- CPU Load slider (0-100%)
- GPU Load slider (0-100%)
- Queue Depth slider (0-100 requests)
- Network Quality selector (Excellent/Good/Poor/Degraded)

**Action Buttons**:
- "Trigger Swarm Consensus" - Manual swarm activation
- "Simulate MEC Failure" - Test failover scenarios
- "Reset to Normal" - Return to baseline metrics

**Mode Selector**:
- Normal Operation
- Threshold Breach Simulation
- Swarm Consensus Active
- MEC Site Failover

#### Main Dashboard - Four Panel Layout

**Panel 1: Real-Time Metrics**
- Line charts showing latency, CPU/GPU load, queue depth over time
- Threshold breach indicators (red flashing markers when exceeded)
- Current vs target performance metrics
- Color-coded status indicators (green=normal, yellow=warning, red=breach)

**Panel 2: Swarm Visualization**
- Interactive network graph of MEC sites (A, B, C) using `st.graphviz_chart`
- Node colors: green=active, gray=standby, red=overloaded, blue=consensus_leader
- Edge thickness represents inter-MEC communication volume
- Animated consensus flow when swarm activates
- Agent status indicators for each MEC site

**Panel 3: Agent Activity Stream**
- Real-time log stream of agent actions and MCP calls:
```
[12:34:01] Orchestrator -> metrics_monitor.mcp: threshold_exceeded(latency=120ms)
[12:34:02] Orchestrator -> memory_sync.mcp: sync_swarm_state(trigger="latency_breach")
[12:34:03] LoadBalancer -> metrics_monitor.mcp: get_healthy_sites()
[12:34:04] LoadBalancer -> container_ops.mcp: scale_containers(site="MEC_B", +2)
[12:34:05] DecisionCoordinator -> telemetry.mcp: log_decision(consensus="MEC_B_selected")
```
- Filterable by agent type and MCP tool
- Color-coded by action type (info=blue, warning=yellow, error=red)

**Panel 4: Observer Cloud Dashboard**
- Aggregated performance metrics (avg latency, uptime %, swarm efficiency)
- Comparison charts: "Edge vs Cloud Response Times"
- Historical trend analysis
- Cost optimization metrics
- Compliance and audit trail summary

#### Interactive Features
- **Scenario Buttons**: Gaming, Automotive, Healthcare, IoT use case simulations
- **Performance Comparison**: Toggle between MEC-orchestrated vs cloud-dependent response times
- **Threshold Configuration**: Adjustable threshold sliders with real-time impact visualization
- **Export Functionality**: Download performance reports and metrics data

#### Technical Implementation
```python
# Streamlit app structure
import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from streamlit_agraph import agraph, Node, Edge

def main():
    st.set_page_config(page_title="EdgeMind MEC Orchestration", layout="wide")

    # Sidebar controls
    with st.sidebar:
        render_simulation_controls()
        render_action_buttons()
        render_mode_selector()

    # Main dashboard
    col1, col2 = st.columns(2)
    with col1:
        render_metrics_panel()
        render_agent_activity_stream()
    with col2:
        render_swarm_visualization()
        render_observer_dashboard()

def render_swarm_visualization():
    # NetworkX graph for MEC sites
    nodes = [
        Node(id="MEC_A", label="MEC Site A", color="green"),
        Node(id="MEC_B", label="MEC Site B", color="gray"),
        Node(id="MEC_C", label="MEC Site C", color="red")
    ]
    edges = [Edge(source="MEC_A", target="MEC_B", width=2)]
    agraph(nodes=nodes, edges=edges, config={"height": 400})
```

This dashboard provides comprehensive visibility into the MEC orchestration system, enabling real-time demonstration of swarm consensus, threshold monitoring, and autonomous edge intelligence for stakeholders and judges.

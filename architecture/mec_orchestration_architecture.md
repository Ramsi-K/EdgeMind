# MEC Orchestration Architecture

**Note**: This file contains the old incorrect architecture. Please refer to `generated-diagrams/mec_orchestration_architecture.mmd` for the correct 5G-MEC architecture diagram showing:

- 3 identical MEC sites at 5G radio towers
- Complete Strands agent sets at each site
- Swarm coordination between Decision Coordinators
- AWS Cloud with only AgentCore Memory + Orchestration

## Architecture Overview

This diagram shows the correct 5G-MEC orchestration architecture with **multiple identical MEC sites** at 5G radio towers, each containing complete Strands agent sets.

### Key Components

#### 🌐 User Devices (5G Connected)

- **Mobile Apps**: Consumer applications requiring low-latency responses
- **IoT Sensors**: Industrial sensors with real-time data requirements
- **Gaming Clients**: Interactive applications with strict latency constraints
- **Autonomous Vehicles**: V2X communication requiring ultra-low latency

#### 📡 MEC Sites (Multiple Identical Sites at 5G Radio Towers)

Each MEC site contains:

**Complete Strands Agent Set**:

- **Orchestrator Agent**: Threshold monitoring and request handling
- **Load Balancer Agent**: Workload distribution decisions
- **Resource Monitor Agent**: Performance metrics tracking
- **Decision Coordinator Agent**: Swarm consensus coordination
- **Cache Manager Agent**: Local model and data caching

**Local MCP Tools** (running locally at each site):

- **metrics_monitor**: MEC site performance monitoring
- **container_ops**: Local container scaling operations
- **inference_engine**: Model caching and execution
- **telemetry_logger**: Structured event logging
- **memory_sync**: Swarm state synchronization

**Local Edge Compute**:

- **Containers**: Docker/Kubernetes local deployment
- **Model Cache**: Local storage for frequently used models

#### ☁️ AWS Cloud (Passive Observer Only)

- **AgentCore Memory**: Swarm state storage and learning
- **AgentCore Orchestration**: Agent coordination services

### Request Flow

1. **All user devices** connect via 5G to **MEC Site A (Primary)**
2. **Orchestrator Agent** at Site A processes requests using local MCP tools
3. **Local MCP tools** interact with local containers and model cache
4. **Decision Coordinator Agent** monitors thresholds and triggers swarm when needed
5. **Swarm coordination** activates Sites B & C as fallbacks via Decision Coordinators
6. **Memory sync** stores swarm state in AWS AgentCore Memory
7. **Responses** returned with sub-100ms latency through MEC proximity

### Key Features

- **Sub-100ms Response Times**: Direct 5G-MEC site processing
- **Intelligent Swarm Coordination**: Decision Coordinators manage cross-site coordination
- **MEC Site Redundancy**: Sites B & C provide intelligent fallback
- **Local Processing**: All agents and tools run locally at MEC sites
- **AWS Integration**: Only AgentCore Memory + Orchestration for enterprise services

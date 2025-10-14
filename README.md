# EdgeMind: 5G-MEC Intelligence Orchestration

> 🏆 **5G Edge Computing Showcase**
> Real-time AI orchestration at telecom edge with Strands agent swarms

## 🎯 Project Overview

**Problem**: Current AI systems force a choice between speed and intelligence. Device processing is fast but limited, while cloud processing is powerful but introduces unacceptable latency for real-time applications like autonomous vehicles, industrial control, and gaming.

**Solution**: EdgeMind deploys intelligent Strands agent swarms directly at MEC (Multi-access Edge Computing) sites near 5G RAN controllers. These agents make split-second decisions about workload distribution, triggered by real-time threshold monitoring, ensuring optimal performance without cloud dependency.

## 🚀 Key Innovation

- **Threshold-Based Orchestration**: Monitors latency, CPU/GPU load, and queue depth to trigger intelligent swarm responses
- **MEC-Native Intelligence**: Strands agents deployed directly at telecom edge sites near RAN controllers
- **Swarm Coordination**: Agents collaborate across MEC sites to balance load without cloud involvement
- **Real-Time Decision Making**: Sub-100ms routing decisions for time-critical applications

## 🏗️ Architecture

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
    └─────────────────────────────────────────────┘
                           ↓
              Cloud (Passive Observer)
           - Monitoring & Analytics Only
           - No Real-Time Decisions
```

## 🎮 Business Use Cases

### Gaming & Esports

- **Real-time NPC dialogue**: Device SLM for instant responses
- **Game state analysis**: MEC swarm coordination for regional multiplayer
- **Performance analytics**: Cloud observability (passive)

### Autonomous Vehicles

- **Collision detection**: Device SLM for ultra-low latency safety
- **Traffic coordination**: MEC orchestrator manages regional traffic flow
- **Fleet analytics**: Cloud monitoring and long-term insights

### Smart Cities & IoT

- **Sensor processing**: Device SLM for immediate responses
- **City-wide coordination**: MEC swarm balances infrastructure load
- **Urban planning**: Cloud analytics from aggregated MEC data

## 🤖 MEC Agent Architecture

| Agent                          | Role                                    | Deployment           |
| ------------------------------ | --------------------------------------- | -------------------- |
| **Orchestrator Agent**         | Threshold monitoring & swarm triggering | MEC Site Controller  |
| **Load Balancer Agent**        | Distribute workload across MEC sites    | Strands Swarm Member |
| **Resource Monitor Agent**     | Track CPU/GPU/latency metrics           | Strands Swarm Member |
| **Decision Coordinator Agent** | Coordinate swarm consensus              | Strands Swarm Member |
| **Cache Manager Agent**        | Local model and data caching            | Strands Swarm Member |

## 🛠️ Technology Stack

- **Edge Agents**: Strands framework with containerized deployment
- **MEC Infrastructure**: Docker/Kubernetes on edge compute nodes
- **Device Layer**: Small Language Models (SLMs) for local inference
- **Orchestration**: Threshold-based swarm coordination
- **Observability**: Cloud-based monitoring and analytics (passive)
- **Communication**: Direct MEC-to-MEC networking

## 📊 Expected Outcomes

- **Sub-100ms decision making** for real-time applications
- **Autonomous load balancing** without cloud dependency
- **99.9% availability** through MEC site redundancy
- **Intelligent swarm coordination** adapting to network conditions

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/mec-inference-routing.git
cd mec-inference-routing

# Set up UV environment and install dependencies
uv sync

# Start Streamlit dashboard
uv run streamlit run src/dashboard/app.py

# Run MEC orchestration demo
uv run python src/orchestrator/mec_orchestrator.py

# Test swarm coordination
uv run python src/swarm/swarm_coordinator.py
```

## 📁 Project Structure

```
mec-inference-routing/
├── README.md
├── pyproject.toml          # UV project configuration
├── requirements.txt        # Dependencies
├── docs/                   # MEC architecture documentation
├── architecture/           # MEC topology diagrams (Mermaid)
├── src/
│   ├── orchestrator/      # Threshold monitoring & swarm triggering
│   ├── swarm/             # Strands agent implementations
│   ├── device/            # Edge device integration layer
│   └── dashboard/         # Streamlit MEC monitoring UI
├── tests/                 # Swarm coordination tests
└── demo/                  # Real-time demo scenarios
```

## 🏆 5G Edge Computing Showcase

- **Live Demo**: Real-time MEC orchestration dashboard
- **Video Demo**: Swarm coordination in action
- **Architecture**: See `/architecture` folder for MEC topology
- **MEC Deployment**: Containerized Strands agents on edge infrastructure
- **Performance Analysis**: Sub-100ms decision metrics in `/docs/`

## 📞 Contact

**Team**: EdgeMind Development Team
**Focus**: 5G-MEC Intelligence & Strands Agent Orchestration
**Demo**: Real-time threshold-based swarm coordination

---

_Showcasing the future of 5G-MEC intelligence - where real decisions happen at the edge, not in the cloud_

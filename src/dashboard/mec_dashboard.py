"""
MEC Orchestration Dashboard - Streamlit Interface
"""

import random
import time
from datetime import UTC, datetime, timedelta

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def main():
    """Main dashboard function"""
    st.title("🏢 MEC Orchestration Dashboard")
    st.markdown("**Real-time Multi-access Edge Computing Intelligence**")

    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Control Panel")

        # Simulation mode
        mode = st.selectbox(
            "Operation Mode",
            [
                "Normal Operation",
                "Threshold Breach",
                "Swarm Active",
                "Failover Test",
            ],
        )

        # Refresh rate
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 3)

        # MEC site selection
        selected_sites = st.multiselect(
            "Active MEC Sites",
            ["MEC-Site-A", "MEC-Site-B", "MEC-Site-C"],
            default=["MEC-Site-A", "MEC-Site-B"],
        )

        # Threshold settings
        st.subheader("⚠️ Thresholds")
        latency_threshold = st.slider("Latency Threshold (ms)", 50, 200, 100)
        cpu_threshold = st.slider("CPU Threshold (%)", 60, 95, 80)

    # Main dashboard layout - 4 panels
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Real-time Metrics")
        metrics_container = st.container()

        st.subheader("🤝 Swarm Visualization")
        swarm_container = st.container()

    with col2:
        st.subheader("🚨 Agent Activity Stream")
        activity_container = st.container()

        st.subheader("📈 Performance Analytics")
        analytics_container = st.container()

    # Auto-refresh logic
    placeholder = st.empty()

    while True:
        with placeholder.container():
            # Generate mock data based on mode
            metrics_data = generate_metrics_data(mode)
            swarm_data = generate_swarm_data(selected_sites, mode)
            activity_data = generate_activity_data(mode)

            # Update metrics panel
            with metrics_container:
                display_metrics(metrics_data, latency_threshold, cpu_threshold)

            # Update swarm visualization
            with swarm_container:
                display_swarm_network(swarm_data)

            # Update activity stream
            with activity_container:
                display_activity_stream(activity_data)

            # Update analytics
            with analytics_container:
                display_analytics()

        time.sleep(refresh_rate)


def generate_metrics_data(mode):
    """Generate mock metrics data"""
    base_latency = 45
    base_cpu = 65
    base_gpu = 70
    base_queue = 25

    if mode == "Threshold Breach":
        base_latency = 120
        base_cpu = 85
        base_queue = 60
    elif mode == "Swarm Active":
        base_latency = 35
        base_cpu = 55
        base_queue = 15

    return {
        "latency": base_latency + random.randint(-10, 10),
        "cpu_usage": base_cpu + random.randint(-5, 15),
        "gpu_usage": base_gpu + random.randint(-10, 20),
        "queue_depth": base_queue + random.randint(-5, 25),
        "timestamp": datetime.now(UTC),
    }


def generate_swarm_data(sites, mode):
    """Generate mock swarm coordination data"""
    swarm_data = {}

    for site in sites:
        status = "active"
        if mode == "Threshold Breach" and site == "MEC-Site-A":
            status = "overloaded"
        elif mode == "Failover Test" and site == "MEC-Site-B":
            status = "failed"

        swarm_data[site] = {
            "status": status,
            "load": random.randint(20, 90),
            "connections": random.randint(5, 25),
        }

    return swarm_data


def generate_activity_data(mode):
    """Generate mock agent activity data"""
    now = datetime.now(UTC)

    if mode == "Threshold Breach":
        activities = [
            {
                "time": now,
                "agent": "Orchestrator",
                "action": "THRESHOLD_BREACH_DETECTED",
                "level": "warning",
            },
            {
                "time": now - timedelta(seconds=5),
                "agent": "SwarmCoordinator",
                "action": "SWARM_ACTIVATION",
                "level": "info",
            },
            {
                "time": now - timedelta(seconds=10),
                "agent": "LoadBalancer",
                "action": "ROUTE_OPTIMIZATION",
                "level": "info",
            },
        ]
    elif mode == "Swarm Active":
        activities = [
            {
                "time": now,
                "agent": "SwarmCoordinator",
                "action": "CONSENSUS_ACHIEVED",
                "level": "success",
            },
            {
                "time": now - timedelta(seconds=3),
                "agent": "LoadBalancer",
                "action": "LOAD_DISTRIBUTED",
                "level": "info",
            },
            {
                "time": now - timedelta(seconds=7),
                "agent": "ResourceMonitor",
                "action": "METRICS_UPDATED",
                "level": "info",
            },
        ]
    else:
        activities = [
            {
                "time": now,
                "agent": "Orchestrator",
                "action": "REQUEST_PROCESSED",
                "level": "info",
            },
            {
                "time": now - timedelta(seconds=2),
                "agent": "CacheManager",
                "action": "CACHE_HIT",
                "level": "success",
            },
            {
                "time": now - timedelta(seconds=5),
                "agent": "ResourceMonitor",
                "action": "HEALTH_CHECK",
                "level": "info",
            },
        ]

    return activities


def display_metrics(data, latency_threshold, cpu_threshold):
    """Display real-time metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Latency",
            f"{data['latency']}ms",
            delta=f"{random.randint(-5, 5)}ms",
        )

    with col2:
        st.metric(
            "CPU Usage",
            f"{data['cpu_usage']}%",
            delta=f"{random.randint(-3, 8)}%",
        )

    with col3:
        st.metric(
            "GPU Usage",
            f"{data['gpu_usage']}%",
            delta=f"{random.randint(-5, 10)}%",
        )

    with col4:
        st.metric(
            "Queue Depth",
            f"{data['queue_depth']}",
            delta=f"{random.randint(-2, 5)}",
        )


def display_swarm_network(swarm_data):
    """Display swarm network visualization"""
    # Create a simple network graph
    graph = nx.Graph()

    # Add nodes for each MEC site
    for site, data in swarm_data.items():
        graph.add_node(site, status=data["status"], load=data["load"])

    # Add edges between sites
    sites = list(swarm_data.keys())
    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            graph.add_edge(sites[i], sites[j])

    # Create positions for visualization
    pos = nx.spring_layout(graph)

    # Create plotly figure
    fig = go.Figure()

    # Add edges
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line={"width": 2, "color": "gray"},
                showlegend=False,
            ),
        )

    # Add nodes
    for node in graph.nodes():
        x, y = pos[node]
        status = swarm_data[node]["status"]
        color = {"active": "green", "overloaded": "red", "failed": "gray"}[status]

        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker={"size": 20, "color": color},
                text=[node],
                textposition="middle center",
                showlegend=False,
            ),
        )

    fig.update_layout(
        title="MEC Site Network Status",
        showlegend=False,
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_activity_stream(activities):
    """Display agent activity stream"""
    for activity in activities[:10]:  # Show last 10 activities
        level_colors = {
            "info": "🔵",
            "success": "🟢",
            "warning": "🟡",
            "error": "🔴",
        }

        icon = level_colors.get(activity["level"], "⚪")
        time_str = activity["time"].strftime("%H:%M:%S")

        st.write(f"{icon} **{time_str}** - {activity['agent']}: {activity['action']}")


def display_analytics():
    """Display performance analytics"""
    # Generate some time series data for demo
    now = datetime.now(UTC)
    times = [now - timedelta(minutes=x) for x in range(30, 0, -1)]
    latencies = [45 + random.randint(-10, 15) for _ in times]

    df = pd.DataFrame({"Time": times, "Latency": latencies})

    fig = px.line(df, x="Time", y="Latency", title="Latency Trend (30 min)")
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="red",
        annotation_text="Threshold",
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.elastic.agent import Agent
from diagrams.generic.blank import Blank
from diagrams.generic.device import Mobile

with Diagram("Agent Core MEC Inference Routing", show=False, direction="TB"):
    user = Mobile("User Device")
    api = APIGateway("API Gateway")

    # Agent Core - the central orchestrator
    agent_core = Agent("Agent Core\n(Central Orchestrator)")

    # Individual Agents managed by Agent Core
    with Cluster("Managed Agents"):
        context_agent = Blank("Context\nAgent")
        router_agent = Blank("Router\nAgent")
        resource_agent = Blank("Resource\nAgent")
        cache_agent = Blank("Cache\nAgent")
        monitor_agent = Blank("Monitor\nAgent")

    # AWS Services
    dynamo = Dynamodb("Agent State\n& Rules")
    s3 = S3("Model Storage")
    cloudwatch = Cloudwatch("Metrics")

    # Inference Endpoints
    with Cluster("Inference Endpoints"):
        device = Mobile("Device\n<50ms")
        mec = EC2("MEC\n<200ms")
        cloud = Lambda("Cloud\n1-3s")

    # Main flow - everything goes through Agent Core
    user >> api >> agent_core

    # Agent Core manages all agents
    (
        agent_core
        >> Edge(label="manages")
        >> [context_agent, router_agent, resource_agent, cache_agent, monitor_agent]
    )

    # Agent Core makes routing decisions (not router agent)
    agent_core >> Edge(label="routes to", color="red") >> [device, mec, cloud]

    # Agents interact with AWS services
    [context_agent, router_agent] >> dynamo
    cache_agent >> s3
    [resource_agent, monitor_agent] >> cloudwatch

    # Feedback to Agent Core
    [device, mec, cloud] >> Edge(label="feedback", style="dashed") >> agent_core

print("✅ Done! Check: agent_core_mec_inference_routing.png")

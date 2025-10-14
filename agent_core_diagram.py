#!/usr/bin/env python3
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.generic.compute import Rack
from diagrams.generic.device import Mobile

with Diagram(
    "AWS MEC Inference Routing - Agent Core Architecture", show=False, direction="TB"
):
    user = Mobile("User Device")
    api = APIGateway("API Gateway")

    # Central Agent Core
    agent_core = Bedrock("Agent Core\n(Orchestration Hub)")

    # MCP Servers around Agent Core
    with Cluster("MCP Server Layer"):
        mcp_aws = Rack("AWS MCP Server")
        mcp_inference = Rack("Inference MCP Server")
        mcp_monitoring = Rack("Monitoring MCP Server")
        mcp_cache = Rack("Cache MCP Server")

    # AWS Services
    dynamo = Dynamodb("Agent State\n& Routing Rules")
    s3 = S3("Model Storage\n& Cache")
    cloudwatch = Cloudwatch("Metrics\n& Logs")

    # Inference Endpoints
    with Cluster("Compute Endpoints"):
        device = Mobile("Device\n(TinyLLM, <50ms)")
        mec = EC2("MEC Edge\n(Llama 7B, <200ms)")
        cloud = Lambda("Cloud\n(GPT-4/Claude, 1-3s)")

    # Main flow
    user >> api >> agent_core

    # Agent Core to MCP Servers
    (
        agent_core
        >> Edge(label="Orchestrates")
        >> [mcp_aws, mcp_inference, mcp_monitoring, mcp_cache]
    )

    # MCP to AWS Services
    mcp_aws >> dynamo
    mcp_cache >> s3
    mcp_monitoring >> cloudwatch

    # Inference routing
    mcp_inference >> Edge(label="Routes to") >> [device, mec, cloud]

    # Feedback loop
    (
        [device, mec, cloud]
        >> Edge(label="Performance Data", style="dashed")
        >> mcp_monitoring
    )

print("✅ Done! Check: aws_mec_inference_routing_agent_core_architecture.png")

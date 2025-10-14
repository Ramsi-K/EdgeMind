#!/usr/bin/env python3
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.generic.compute import Rack
from diagrams.generic.device import Mobile

with Diagram("AWS MEC Inference Routing with MCP", show=False, direction="TB"):
    user = Mobile("User Device")
    api = APIGateway("API Gateway")

    # Single Lambda with Multi-Agent System
    with Cluster("Lambda Runtime"):
        agents_lambda = Lambda(
            "Multi-Agent System\n(Context, Router, Resource,\nCache, Monitor Agents)"
        )

        with Cluster("MCP Servers"):
            mcp_aws = Rack("AWS MCP Server")
            mcp_inference = Rack("Inference MCP Server")
            mcp_monitoring = Rack("Monitoring MCP Server")

    # AWS Services
    dynamo = Dynamodb("Routing Rules\n& Agent State")
    s3 = S3("Model Storage\n& Cache")
    cloudwatch = Cloudwatch("Metrics\n& Logs")

    # Compute Endpoints
    with Cluster("Inference Endpoints"):
        device = Mobile("Device\n(TinyLLM, <50ms)")
        mec = EC2("MEC Edge\n(Llama 7B, <200ms)")
        cloud = Lambda("Cloud\n(GPT-4/Claude, 1-3s)")

    # Connections
    user >> api >> agents_lambda

    # MCP Server connections
    agents_lambda >> Edge(label="MCP Protocol") >> mcp_aws
    agents_lambda >> Edge(label="MCP Protocol") >> mcp_inference
    agents_lambda >> Edge(label="MCP Protocol") >> mcp_monitoring

    # AWS Service connections via MCP
    mcp_aws >> dynamo
    mcp_aws >> s3
    mcp_monitoring >> cloudwatch

    # Inference routing
    mcp_inference >> Edge(label="Route Decision") >> [device, mec, cloud]

    # Feedback loop
    (
        [device, mec, cloud]
        >> Edge(label="Performance Data", style="dashed")
        >> mcp_monitoring
    )

print("✅ Done! Check: aws_mec_inference_routing_with_mcp.png")

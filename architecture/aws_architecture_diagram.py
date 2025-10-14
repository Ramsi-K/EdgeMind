#!/usr/bin/env python3
"""
AWS MEC Inference Routing System Architecture Diagram
Generated for AWS Agents Hackathon 2025
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.analytics import KinesisDataStreams
from diagrams.aws.compute import EC2, ECS, Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.generic.device import Mobile
from diagrams.onprem.client import User


def create_architecture_diagram():
    """Create the MEC inference routing system architecture diagram"""

    with Diagram("AWS MEC Inference Routing System", show=False, direction="TB"):

        # User layer
        user = User("User Request")

        with Cluster("Device Layer"):
            device = Mobile("Edge Device\n(TinyLLM)\n<50ms")

        with Cluster("AWS Infrastructure"):
            # API Gateway
            api_gw = APIGateway("API Gateway")

            # Multi-Agent System
            with Cluster("Multi-Agent System"):
                context_agent = Lambda("Context Agent\n(Analysis)")
                router_agent = Lambda("Router Agent\n(Decisions)")
                resource_agent = Lambda("Resource Agent\n(Monitoring)")
                cache_agent = Lambda("Cache Agent\n(Management)")
                monitor_agent = Lambda("Monitor Agent\n(Learning)")

            # Storage & Data
            with Cluster("Data Layer"):
                dynamodb = DynamodbTable("DynamoDB\n(Routing Rules)")
                s3 = S3("S3\n(Models)")
                cloudwatch = Cloudwatch("CloudWatch\n(Metrics)")
                kinesis = KinesisDataStreams("Kinesis\n(Events)")

            # Compute Tiers
            with Cluster("MEC Edge"):
                mec_compute = ECS("ECS\n(Llama 7B/13B)\n<200ms")

            with Cluster("Cloud"):
                cloud_compute = EC2("EC2\n(GPT-4/Claude)\n1-3s")

        # Connections
        user >> api_gw
        api_gw >> context_agent
        context_agent >> router_agent

        router_agent >> Edge(label="route") >> [device, mec_compute, cloud_compute]

        resource_agent >> cloudwatch
        cache_agent >> s3
        monitor_agent >> kinesis

        router_agent >> dynamodb
        [context_agent, resource_agent, cache_agent, monitor_agent] >> cloudwatch


if __name__ == "__main__":
    create_architecture_diagram()
    print("Architecture diagram generated: aws_mec_inference_routing_system.png")

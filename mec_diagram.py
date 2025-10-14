#!/usr/bin/env python3
from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.generic.device import Mobile

with Diagram("AWS MEC Inference Routing System", show=False, direction="LR"):
    user = Mobile("User Device")
    api = APIGateway("API Gateway")

    with Cluster("Multi-Agent System"):
        context_agent = Lambda("Context Agent")
        router_agent = Lambda("Router Agent")
        resource_agent = Lambda("Resource Agent")
        cache_agent = Lambda("Cache Agent")
        monitor_agent = Lambda("Monitor Agent")

    dynamo = Dynamodb("Routing Rules")
    s3 = S3("Model Storage")
    cloudwatch = Cloudwatch("Metrics")

    with Cluster("Device Layer"):
        device = EC2("Edge Device")

    with Cluster("MEC Layer"):
        mec = EC2("MEC Instance")

    with Cluster("Cloud Layer"):
        cloud = Lambda("Cloud Models")

    user >> api >> context_agent
    context_agent >> router_agent
    router_agent >> [device, mec, cloud]

    context_agent >> dynamo
    router_agent >> dynamo
    cache_agent >> s3
    resource_agent >> cloudwatch
    monitor_agent >> cloudwatch

print("✅ Done! Check: aws_mec_inference_routing_system.png")

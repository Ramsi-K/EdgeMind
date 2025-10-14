#!/usr/bin/env python3
"""
MEC Inference Routing System - CDK Application Entry Point
"""

import os

import aws_cdk as cdk

from infrastructure.mec_routing_stack import MECRoutingStack

app = cdk.App()

# Get environment configuration
account = os.environ.get("CDK_DEFAULT_ACCOUNT", os.environ.get("AWS_ACCOUNT_ID"))
region = os.environ.get("CDK_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

env = cdk.Environment(account=account, region=region)

# Create the main stack
MECRoutingStack(
    app,
    "MECRoutingStack",
    env=env,
    description="MEC Inference Routing System - Multi-agent AI routing platform",
)

app.synth()

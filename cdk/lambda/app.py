"""
MEC Inference Routing System - Lambda Handler
Strands Agents deployment for AWS Lambda
"""

import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time

# AWS clients
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

# Environment variables
ROUTING_DECISIONS_TABLE = os.environ.get("ROUTING_DECISIONS_TABLE")
AGENT_BUCKET = os.environ.get("AGENT_BUCKET")


@tool
def store_routing_decision(
    request_id: str,
    user_id: str,
    selected_tier: str,
    reasoning: str,
    estimated_cost: float,
    estimated_latency: int,
) -> str:
    """Store routing decision in DynamoDB"""
    table = dynamodb.Table(ROUTING_DECISIONS_TABLE)

    item = {
        "request_id": request_id,
        "timestamp": int(datetime.now().timestamp()),
        "user_id": user_id,
        "selected_tier": selected_tier,
        "reasoning": reasoning,
        "estimated_cost": estimated_cost,
        "estimated_latency": estimated_latency,
    }

    table.put_item(Item=item)
    return f"Stored routing decision for {request_id}: {selected_tier}"


@tool
def get_compute_tier_costs() -> dict:
    """Get current pricing for different compute tiers"""
    return {
        "device_tier": {
            "cost_per_hour": 0.0,
            "latency_ms": 20,
            "description": "Local processing, no cost, ultra-low latency",
        },
        "edge_tier": {
            "cost_per_hour": 0.0416,
            "latency_ms": 50,
            "description": "Regional MEC processing, moderate cost and latency",
        },
        "cloud_tier": {
            "cost_per_1k_tokens": 0.0008,
            "latency_ms": 200,
            "description": "Bedrock Nova models, pay per token, highest capability",
        },
    }


@tool
def analyze_request_complexity(content: str) -> dict:
    """Analyze request complexity to determine optimal routing"""
    token_estimate = len(content.split()) * 1.3

    if token_estimate < 50:
        complexity = "simple"
        recommended_tier = "device"
    elif token_estimate < 200:
        complexity = "moderate"
        recommended_tier = "edge"
    else:
        complexity = "complex"
        recommended_tier = "cloud"

    return {
        "estimated_tokens": int(token_estimate),
        "complexity": complexity,
        "recommended_tier": recommended_tier,
        "analysis": f"Request has ~{int(token_estimate)} tokens, classified as {complexity}",
    }


def get_agent_object(key: str):
    """Load agent state from S3"""
    try:
        response = s3.get_object(Bucket=AGENT_BUCKET, Key=key)
        content = response["Body"].read().decode("utf-8")
        state = json.loads(content)

        return Agent(
            messages=state["messages"],
            system_prompt=state["system_prompt"],
            tools=[
                current_time,
                store_routing_decision,
                get_compute_tier_costs,
                analyze_request_complexity,
            ],
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        else:
            raise


def put_agent_object(key: str, agent: Agent):
    """Save agent state to S3"""
    state = {"messages": agent.messages, "system_prompt": agent.system_prompt}

    content = json.dumps(state)
    s3.put_object(
        Bucket=AGENT_BUCKET,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="application/json",
    )


def create_agent():
    """Create new MEC routing agent"""
    model = BedrockModel(model_id="amazon.nova-pro-v1:0", temperature=0.1)

    system_prompt = """
    You are the MEC Inference Routing Agent. Your job is to intelligently route AI inference requests
    to the optimal compute tier (device, edge/MEC, or cloud) based on multiple factors.

    COMPUTE TIERS:
    - Device: Local processing, 0 cost, ~20ms latency, limited capability (simple queries only)
    - Edge/MEC: Regional processing, ~$0.04/hour, ~50ms latency, moderate capability
    - Cloud: Bedrock Nova models, ~$0.0008/1K tokens, ~200ms latency, full AI capability

    ROUTING DECISION PROCESS:
    1. Use analyze_request_complexity() to understand the request
    2. Use get_compute_tier_costs() to get current pricing
    3. Consider user constraints (latency requirements, cost budget)
    4. Select optimal tier and store decision using store_routing_decision()
    5. Provide clear reasoning for the decision

    ROUTING GUIDELINES:
    - Simple queries (< 50 tokens): Prefer device tier for speed
    - Complex analysis (> 200 tokens): Prefer cloud tier for accuracy
    - Cost-sensitive users: Prefer device/edge when possible
    - Latency-critical: Prefer device/edge tiers

    Always explain your reasoning clearly and store decisions for monitoring.
    """

    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            current_time,
            store_routing_decision,
            get_compute_tier_costs,
            analyze_request_complexity,
        ],
    )


def handler(event: Dict[str, Any], context) -> str:
    """Lambda handler for MEC routing agent"""

    prompt = event.get("prompt")
    session_id = event.get("session_id", "default")

    try:
        agent = get_agent_object(key=f"sessions/{session_id}.json")

        if not agent:
            agent = create_agent()

        response = agent(prompt)
        content = str(response)

        put_agent_object(key=f"sessions/{session_id}.json", agent=agent)

        return content

    except Exception as e:
        raise str(e)

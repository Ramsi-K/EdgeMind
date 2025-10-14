"""
MEC Inference Routing System - Main Lambda Handler
Following Strands Agents deployment pattern
"""

import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time

# AWS clients
dynamodb = boto3.resource("dynamodb")
bedrock_runtime = boto3.client("bedrock-runtime")
pricing = boto3.client("pricing", region_name="us-east-1")
s3 = boto3.client("s3")

# Environment variables
ROUTING_DECISIONS_TABLE = os.environ.get("ROUTING_DECISIONS_TABLE")
RESOURCE_METRICS_TABLE = os.environ.get("RESOURCE_METRICS_TABLE")
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
    # Simple heuristics for demo
    token_estimate = len(content.split()) * 1.3  # Rough token estimation

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


@tool
def get_recent_routing_decisions(limit: int = 10) -> list:
    """Get recent routing decisions for analysis"""
    table = dynamodb.Table(ROUTING_DECISIONS_TABLE)

    response = table.scan(
        Limit=limit,
        ProjectionExpression="request_id, selected_tier, estimated_cost, estimated_latency, reasoning",
    )

    return response.get("Items", [])


def get_agent_state(session_id: str):
    """Load agent state from S3"""
    try:
        response = s3.get_object(Bucket=AGENT_BUCKET, Key=f"sessions/{session_id}.json")
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
                get_recent_routing_decisions,
            ],
        )
    except Exception:
        return None


def save_agent_state(session_id: str, agent: Agent):
    """Save agent state to S3"""
    state = {"messages": agent.messages, "system_prompt": agent.system_prompt}

    content = json.dumps(state)
    s3.put_object(
        Bucket=AGENT_BUCKET,
        Key=f"sessions/{session_id}.json",
        Body=content.encode("utf-8"),
        ContentType="application/json",
    )


def create_routing_agent():
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
    4. Select optimal tier based on:
       - Request complexity vs tier capability
       - Latency requirements vs tier latency
       - Cost budget vs tier costs
       - Availability and reliability needs
    5. Store decision using store_routing_decision()
    6. Provide clear reasoning for the decision

    ROUTING GUIDELINES:
    - Simple queries (< 50 tokens): Prefer device tier for speed
    - Complex analysis (> 200 tokens): Prefer cloud tier for accuracy
    - Cost-sensitive users: Prefer device/edge when possible
    - Latency-critical: Prefer device/edge tiers
    - High accuracy needs: Prefer cloud tier

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
            get_recent_routing_decisions,
        ],
    )


def create_monitoring_agent():
    """Create monitoring agent for system metrics"""
    model = BedrockModel(model_id="amazon.nova-pro-v1:0", temperature=0.1)

    system_prompt = """
    You are the MEC Monitoring Agent. Your job is to analyze system performance and provide insights.

    Use get_recent_routing_decisions() to analyze patterns and provide:
    - Routing decision trends
    - Cost efficiency analysis
    - Latency performance metrics
    - Tier utilization statistics
    - Optimization recommendations

    Focus on actionable insights and clear metrics.
    """

    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            current_time,
            get_recent_routing_decisions,
            get_compute_tier_costs,
        ],
    )


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main Lambda handler"""

    # Parse request
    request_type = event.get("request_type", "inference")
    session_id = event.get("session_id", "default")

    try:
        if request_type == "inference":
            # Handle inference routing request
            agent = get_agent_state(session_id) or create_routing_agent()

            prompt = f"""
            Route this inference request optimally:

            Content: "{event.get('content', '')}"
            User ID: {event.get('user_id', 'anonymous')}
            Request ID: {event.get('request_id', context.aws_request_id)}
            Latency Requirement: {event.get('latency_requirement', 'normal')}
            Cost Budget: ${event.get('cost_budget', 'unlimited')}
            Device Info: {event.get('device_info', {})}

            Analyze the request and make an optimal routing decision.
            """

            response = agent(prompt)
            save_agent_state(session_id, agent)

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "request_id": event.get("request_id", context.aws_request_id),
                        "routing_decision": str(response),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }

        elif request_type == "metrics":
            # Handle metrics request
            agent = create_monitoring_agent()

            prompt = """
            Generate a comprehensive system metrics report:

            1. Analyze recent routing decisions
            2. Calculate performance metrics
            3. Identify trends and patterns
            4. Provide optimization recommendations
            """

            response = agent(prompt)

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "metrics": str(response),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }

        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid request_type"}),
            }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# For local testing
if __name__ == "__main__":
    test_event = {
        "request_type": "inference",
        "content": "Analyze customer sentiment from this support ticket",
        "user_id": "test-user",
        "request_id": "test-123",
        "latency_requirement": "low",
        "cost_budget": 0.01,
        "session_id": "test-session",
    }

    class MockContext:
        aws_request_id = "test-request-id"

    result = handler(test_event, MockContext())
    print(json.dumps(result, indent=2))

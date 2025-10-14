"""
MEC Inference Routing System - Simplified CDK Stack
Focus on Bedrock AgentCore + Nova + Basic AWS Services
"""

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class MECRoutingStack(Stack):
    """Simplified CDK stack focused on AgentCore integration"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        self.routing_decisions_table = self._create_routing_decisions_table()
        self.resource_metrics_table = self._create_resource_metrics_table()

        # Create Lambda functions for agent implementations
        self.agent_functions = self._create_agent_functions()

        # Create API Gateway
        self.api_gateway = self._create_api_gateway()

    def _create_routing_decisions_table(self) -> dynamodb.Table:
        """Create DynamoDB table for routing decisions"""
        return dynamodb.Table(
            self,
            "RoutingDecisionsTable",
            table_name="mec-routing-decisions",
            partition_key=dynamodb.Attribute(
                name="request_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def _create_resource_metrics_table(self) -> dynamodb.Table:
        """Create DynamoDB table for resource metrics"""
        return dynamodb.Table(
            self,
            "ResourceMetricsTable",
            table_name="mec-resource-metrics",
            partition_key=dynamodb.Attribute(
                name="tier_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

    def _create_agent_functions(self) -> dict:
        """Create Lambda functions for agents with minimal IAM"""
        functions = {}

        # Simple execution role with Bedrock and DynamoDB access
        execution_role = iam.Role(
            self,
            "AgentExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "AgentPolicy": iam.PolicyDocument(
                    statements=[
                        # Bedrock access for Nova models and AgentCore
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                                "bedrock-agent:*",
                                "bedrock-agent-runtime:*",
                            ],
                            resources=["*"],
                        ),
                        # DynamoDB access
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:Query",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                            ],
                            resources=[
                                self.routing_decisions_table.table_arn,
                                self.resource_metrics_table.table_arn,
                                f"{self.routing_decisions_table.table_arn}/index/*",
                                f"{self.resource_metrics_table.table_arn}/index/*",
                            ],
                        ),
                    ]
                )
            },
        )

        # Common Lambda configuration
        common_config = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "timeout": Duration.minutes(5),
            "memory_size": 512,
            "role": execution_role,
            "environment": {
                "ROUTING_DECISIONS_TABLE": self.routing_decisions_table.table_name,
                "RESOURCE_METRICS_TABLE": self.resource_metrics_table.table_name,
                "AWS_REGION": self.region,
                "NOVA_MODEL_ID": "amazon.nova-pro-v1:0",
            },
        }

        # Main routing function (handles all agent coordination via AgentCore)
        functions["main"] = _lambda.Function(
            self,
            "MainRoutingFunction",
            function_name="mec-main-routing",
            code=_lambda.Code.from_asset("src"),
            handler="main.handler",
            **common_config,
        )

        return functions

    def _create_api_gateway(self) -> apigateway.RestApi:
        """Create simple API Gateway"""
        api = apigateway.RestApi(
            self,
            "MECRoutingAPI",
            rest_api_name="MEC Inference Routing API",
            description="API for MEC inference routing system",
        )

        # POST /inference - Submit inference request
        inference_resource = api.root.add_resource("inference")
        inference_integration = apigateway.LambdaIntegration(
            self.agent_functions["main"]
        )
        inference_resource.add_method("POST", inference_integration)

        # GET /metrics - Get system metrics
        metrics_resource = api.root.add_resource("metrics")
        metrics_integration = apigateway.LambdaIntegration(self.agent_functions["main"])
        metrics_resource.add_method("GET", metrics_integration)

        return api

#!/usr/bin/env python3
from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ELB, Route53
from diagrams.aws.storage import S3

with Diagram("3-Tier Web Application", show=False, direction="LR"):
    user = Route53("DNS")
    lb = ELB("Load Balancer")

    with Cluster("Web Tier"):
        web_servers = [EC2("Web-1"), EC2("Web-2"), EC2("Web-3")]

    with Cluster("App Tier"):
        app_servers = [Lambda("API-1"), Lambda("API-2")]

    with Cluster("Data Tier"):
        cache = ElastiCache("Redis Cache")
        database = RDS("PostgreSQL")
        storage = S3("Static Assets")

    user >> lb >> web_servers >> app_servers
    app_servers >> cache
    app_servers >> database
    web_servers >> storage

print("✅ Done! Check: 3_tier_web_application.png")

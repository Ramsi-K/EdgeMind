FROM python:3.11-slim

RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
RUN pip install awslabs.aws-diagram-mcp-server

CMD ["python", "-m", "awslabs.aws_diagram_mcp_server"]

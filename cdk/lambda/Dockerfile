FROM public.ecr.aws/lambda/python:3.13

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy function code
COPY app.py ./

# Command to run the handler
CMD ["app.handler"]

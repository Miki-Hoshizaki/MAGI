FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the magi package
COPY . /app/

# Install magi package and its dependencies
RUN pip install -e .

# Install eliza_service dependencies
COPY examples/eliza_service/requirements.txt /app/examples/eliza_service/
RUN pip install -r examples/eliza_service/requirements.txt

# Copy eliza_service files
COPY examples/eliza_service /app/examples/eliza_service/

# Set working directory to eliza_service
WORKDIR /app/examples/eliza_service

# Create results directory
RUN mkdir -p results

# Expose the port
EXPOSE 8000

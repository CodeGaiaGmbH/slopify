FROM ubuntu:24.04

WORKDIR /app

# Set environment variables
ENV JIRA_VERSION=1.6.0 \
    JIRA_ARCH=arm64 \
    PATH="/app/bin:/app/.venv/bin:${PATH}"

# Install required packages
RUN apt-get update && \
    apt-get install -y wget curl git jq fzf gh python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv --break-system-packages

# Install siesta
RUN uv venv && \
    uv pip install git+https://github.com/ihucos/siesta.git

# Download, extract and install Jira CLI
RUN cd /tmp && \
    wget https://github.com/ankitpokhrel/jira-cli/releases/download/v${JIRA_VERSION}/jira_${JIRA_VERSION}_linux_${JIRA_ARCH}.tar.gz && \
    tar -xvf *.tar.gz && \
    cp /tmp/*/bin/jira /usr/local/bin/jira

COPY . /app

SHELL [ "bash" ]

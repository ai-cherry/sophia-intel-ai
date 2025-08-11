FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt
RUN uv pip install --system -r /workspace/requirements.txt

# Default command for Codespaces terminal sessions
CMD ["bash"]
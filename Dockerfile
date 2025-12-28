FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/

# Set Python path
ENV PYTHONPATH=/app

# Run as non-root user
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

CMD ["python", "-m", "pytest"]

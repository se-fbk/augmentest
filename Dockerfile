# --- Stage 1: Get Java 11 ---
FROM eclipse-temurin:11-jdk AS java-provider

# --- Stage 2: Build the Python 3.12 Environment ---
FROM python:3.12-slim

# 1. Copy Java 11
COPY --from=java-provider /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# 2. Python Setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Critical: Set PYTHONPATH to /app so imports work regardless of WORKDIR
ENV PYTHONPATH=/app

# 3. System Dependencies
RUN apt-get update && apt-get install -y \
    maven \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4. Setup Application
WORKDIR /app

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# 5. Set Entrypoint
# We set the entrypoint to python, pointing to the specific script path
ENTRYPOINT ["python", "src/run_augmentestagentic.py"]
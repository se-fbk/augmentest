#!/usr/bin/env bash
set -euo pipefail

###############################
# Config (edit if you want)
###############################

#MODEL_DIR="${MODEL_DIR:-$HOME/Documents/LLMs}"
MODEL_DIR="${MODEL_DIR:-$(pwd)/LLMs}"
#MODEL_NAME="gpt-oss-20b-mxfp4.gguf"
#MODEL_URL="https://huggingface.co/ggml-org/gpt-oss-20b-GGUF/resolve/main/gpt-oss-20b-mxfp4.gguf"
MODEL_NAME="qwen2.5-coder-7b-instruct-q2_k.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q2_k.gguf?download=true"
IMAGE_NAME="ghcr.io/ggml-org/llama.cpp:server"
CONTAINER_NAME="llm-server"
PORT="${PORT:-8000}"
N_TOKENS="${N_TOKENS:-512}"

###############################
# 1. Prepare model directory
###############################

echo "📁 Using model directory: $MODEL_DIR"
mkdir -p "$MODEL_DIR"

MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

###############################
# 2. Download model if missing
###############################

if [ ! -f "$MODEL_PATH" ]; then
  echo "⬇️  Model not found at $MODEL_PATH"
  echo "   Downloading from:"
  echo "   $MODEL_URL"
  curl -L "$MODEL_URL" -o "$MODEL_PATH"
else
  echo "✅ Model already present at $MODEL_PATH"
fi

###############################
# 3. Pull Docker image
###############################

echo "🐳 Pulling Docker image: $IMAGE_NAME"
docker pull "$IMAGE_NAME"

###############################
# 4. Stop existing container (if any)
###############################

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "🛑 Stopping existing container: $CONTAINER_NAME"
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

###############################
# 5. Run server container
###############################

echo "🚀 Starting LLM server on port $PORT..."
echo ""
echo "✅ LLM server is starting."
echo "   URL: http://localhost:$PORT"
echo "   Container: $CONTAINER_NAME"

docker run \
  --name "$CONTAINER_NAME" \
  -v "$MODEL_DIR":/models \
  -p "$PORT":8000 \
  "$IMAGE_NAME" \
  -m "/models/$MODEL_NAME" \
  --port 8000 \
  --host 0.0.0.0 \
  -n "$N_TOKENS"


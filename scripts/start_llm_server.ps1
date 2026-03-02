$ErrorActionPreference = "Stop"

###############################
# Config (edit if needed)
###############################

if (-not $env:MODEL_DIR) {
    $MODEL_DIR = Join-Path (Get-Location) "LLMs"
} else {
    $MODEL_DIR = $env:MODEL_DIR
}

$MODEL_NAME = "qwen2.5-coder-7b-instruct-q2_k.gguf"
$MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q2_k.gguf?download=true"
$IMAGE_NAME = "ghcr.io/ggml-org/llama.cpp:server"
$CONTAINER_NAME = "llm-server"
$PORT = if ($env:PORT) { $env:PORT } else { "8000" }
$N_TOKENS = if ($env:N_TOKENS) { $env:N_TOKENS } else { "512" }

Write-Host "Using model directory: $MODEL_DIR"
New-Item -ItemType Directory -Force -Path $MODEL_DIR | Out-Null

$MODEL_PATH = Join-Path $MODEL_DIR $MODEL_NAME

if (!(Test-Path $MODEL_PATH)) {
    Write-Host "Downloading model..."
    Invoke-WebRequest -Uri $MODEL_URL -OutFile $MODEL_PATH
} else {
    Write-Host "Model already present."
}

Write-Host "Pulling Docker image..."
docker pull $IMAGE_NAME

if (docker ps -a --format "{{.Names}}" | Select-String "^$CONTAINER_NAME$") {
    docker rm -f $CONTAINER_NAME | Out-Null
}

Write-Host "Starting LLM server on port $PORT..."

docker run `
  --name $CONTAINER_NAME `
  -v "${MODEL_DIR}:/models" `
  -p "${PORT}:8000" `
  $IMAGE_NAME `
  -m "/models/$MODEL_NAME" `
  --port 8000 `
  --host 0.0.0.0 `
  -n $N_TOKENS
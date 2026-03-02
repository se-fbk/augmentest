@echo off
setlocal enabledelayedexpansion

set MODEL_DIR=%CD%\LLMs
set MODEL_NAME=qwen2.5-coder-7b-instruct-q2_k.gguf
set MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q2_k.gguf?download=true
set IMAGE_NAME=ghcr.io/ggml-org/llama.cpp:server
set CONTAINER_NAME=llm-server
set PORT=8000
set N_TOKENS=512

echo Using model directory: %MODEL_DIR%
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

set MODEL_PATH=%MODEL_DIR%\%MODEL_NAME%

if not exist "%MODEL_PATH%" (
    echo Downloading model...
    curl -L "%MODEL_URL%" -o "%MODEL_PATH%"
) else (
    echo Model already present.
)

echo Pulling Docker image...
docker pull %IMAGE_NAME%

for /f %%i in ('docker ps -a --format "{{.Names}}"') do (
    if "%%i"=="%CONTAINER_NAME%" (
        docker rm -f %CONTAINER_NAME%
    )
)

echo Starting LLM server on port %PORT%...

docker run ^
  --name %CONTAINER_NAME% ^
  -v "%MODEL_DIR%:/models" ^
  -p %PORT%:8000 ^
  %IMAGE_NAME% ^
  -m "/models/%MODEL_NAME%" ^
  --port 8000 ^
  --host 0.0.0.0 ^
  -n %N_TOKENS%
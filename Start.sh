#!/bin/bash
# WenForge startup script for bash (Git Bash / WSL)

echo "============================================"
echo "  WenForge - AI网文创作助手"
echo "  正在启动..."
echo "============================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start Python sidecar
echo "[1/3] 启动 AI 引擎..."
cd "$SCRIPT_DIR/python"
python -m uvicorn main:app --host 127.0.0.1 --port 8765 &
PYTHON_PID=$!
cd "$SCRIPT_DIR"

# Wait for Python
echo "[2/3] 等待 AI 引擎就绪..."
for i in $(seq 1 15); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health')" 2>/dev/null; then
    echo "  AI 引擎就绪!"
    break
  fi
  sleep 1
done

# Start Electron
echo "[3/3] 启动桌面应用..."
npx electron . &
ELECTRON_PID=$!

echo ""
echo "WenForge 已启动！"
echo "AI 引擎 PID: $PYTHON_PID"
echo ""

# Cleanup on exit
trap "kill $PYTHON_PID 2>/dev/null; exit" INT TERM
wait $ELECTRON_PID
kill $PYTHON_PID 2>/dev/null

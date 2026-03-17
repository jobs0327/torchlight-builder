#!/bin/bash

# 检查3000端口是否被占用
PORT=3000
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
  echo "端口 $PORT 被占用，进程ID: $PID"
  echo "正在停止占用端口的进程..."
  kill -9 $PID
  if [ $? -eq 0 ]; then
    echo "进程已成功停止"
  else
    echo "停止进程失败，请手动检查"
  fi
else
  echo "端口 $PORT 未被占用"
fi

# 启动开发服务器
echo "正在启动开发服务器..."
cd "$(dirname "$0")"
npm run dev

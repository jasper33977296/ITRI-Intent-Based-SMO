#!/bin/bash

function remove_container_if_exists() {
  local container_name="$1"
  if [ "$(docker ps -aq -f name=${container_name})" ]; then
    echo "Stopping and removing existing container: ${container_name}"
    docker stop "${container_name}" 2>/dev/null
    docker rm "${container_name}" 2>/dev/null
  fi
}

remove_container_if_exists "itri-intent-backend-dev"


source .env

docker build --no-cache -t itri-intent-backend-dev -f Dockerfile.dev .

# 啟動 意圖後端系統 容器
docker run -d \
    --name itri-intent-backend-dev \
    -p 30000:30000 \
    -v $(pwd):/app \
    itri-intent-backend-dev \
    /bin/sh -c "pip install -r requirements/base.txt && python manage.py makemigrations && python manage.py runserver 0.0.0.0:30000"
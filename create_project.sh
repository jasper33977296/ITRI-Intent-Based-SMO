#!/bin/bash
# create_django_project.sh
# 專案名稱
echo -n "Please enter your Django app name: "
read PROJECT_NAME

# 檢查是否提供專案名稱
if [ -z "$PROJECT_NAME" ]; then
  echo "Project name cannot be empty!"
  exit 1
fi

# 檢查是否安裝 Django
if ! python3 -m django --version > /dev/null 2>&1; then
  echo "Django 未安裝，請先安裝 Django，再執行此腳本。"
  exit 1
fi

# 確保在專案主目錄下執行腳本
if [ ! -d "$PWD" ]; then
  echo "請先創建專案主目錄，確保專案名稱與目錄相同並在該目錄下執行此腳本。"
  exit 1
fi

# 建立目錄結構
mkdir -p logs
mkdir -p main/apps
mkdir -p main/settings
mkdir -p main/utils
mkdir -p requirements
mkdir -p shell

chmod 777 logs

# 建立必要的檔案
touch .dockerignore
cat > .env <<EOF
# 環境變數範例
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@db:5432/database
EOF

touch .env.sample
cp .env .env.sample

touch .gitignore
cat > .gitignore <<EOF
# Python
__pycache__/
*.py[cod]
*.sqlite3

# Virtualenv
.env

# Logs
logs/

# Docker
docker-compose.override.yml
EOF

touch docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env

  db:
    image: postgres:latest
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: database
    ports:
      - "5432:5432"
EOF

cat > Dockerfile <<EOF
FROM python:3.11

WORKDIR /app

COPY requirements /app/requirements

RUN pip install --no-cache-dir -r requirements/base.txt

COPY . /app

CMD ["gunicorn", "main.wsgi:application", "--bind", "0.0.0.0:8000"]
EOF

# 建立 Django 項目
django-admin startproject main .

# 調整 settings 檔案
mv main/settings.py main/settings/base.py
cat > main/settings/__init__.py <<EOF
from .base import *
EOF

touch main/settings/local.py
cat > main/settings/local.py <<EOF
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']
EOF

touch main/settings/production.py
cat > main/settings/production.py <<EOF
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
EOF

touch main/settings/test.py
cat > main/settings/test.py <<EOF
from .base import *

DEBUG = False
ALLOWED_HOSTS = []
TESTING = True
EOF

# 建立必要的空文件
touch main/apps/__init__.py
touch main/utils/__init__.py

# 更新 requirements
cat > requirements/base.txt <<EOF
Django==4.1.3
EOF

touch requirements/local.txt
cat > requirements/local.txt <<EOF
-r base.txt
django-debug-toolbar
EOF

touch requirements/production.txt
cat > requirements/production.txt <<EOF
-r base.txt
gunicorn
EOF

touch requirements/test.txt
cat > requirements/test.txt <<EOF
-r base.txt
pytest
django-pytest
EOF

echo "$PROJECT_NAME 專案結構建立完成。"

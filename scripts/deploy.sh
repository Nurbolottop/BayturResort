#!/bin/bash
# Деплой Baytur Resort & Spa на сервер.
#
# ВАЖНО: app/media исключена из синхронизации намеренно.
# Файлы туда кладут через админку на сервере, а имена им присваивает Django
# (logo_bGALXKK.png и т.п.). Если синхронизировать media с --delete, серверные
# файлы удаляются, а в базе остаются ссылки на них — сайт остаётся без картинок.
#
# Использование:  ./scripts/deploy.sh [user@host] [путь]

set -e

TARGET="${1:-root@213.171.15.215}"
REMOTE_DIR="${2:-/root/Baitur}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ Синхронизация кода в $TARGET:$REMOTE_DIR"
rsync -az --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='.claude' \
  --exclude='.env' \
  --exclude='app/media' \
  --exclude='app/staticfiles' \
  "$LOCAL_DIR/" "$TARGET:$REMOTE_DIR/"

echo "→ Пересборка и перезапуск"
ssh "$TARGET" "cd $REMOTE_DIR && \
  docker compose -f docker/docker-compose.prod.yml up -d --build && \
  sleep 20 && \
  docker exec django_web_baitur python manage.py migrate --noinput && \
  docker exec django_web_baitur python manage.py compilemessages && \
  docker exec django_web_baitur python manage.py collectstatic --noinput"

echo "→ Готово: https://bautur.zeastudio.su"

#!/bin/bash
# Деплой Baytur Resort & Spa: коммит → GitHub → сервер тянет и пересобирается.
#
# Сервер держит рабочую копию в /root/Baitur и обновляется через git reset
# --hard: локальных правок там быть не должно, источник правды — репозиторий.
#
# Не в репозитории и остаётся на сервере нетронутым:
#   .env         — прод-настройки и пароли
#   app/media    — загруженные файлы; имена им присваивает Django, локальных
#                  копий нет, поэтому синхронизировать их нельзя
#
# Использование:  ./scripts/deploy.sh ["текст коммита"]

set -e

TARGET="${DEPLOY_TARGET:-root@213.171.15.215}"
REMOTE_DIR="${DEPLOY_DIR:-/root/Baitur}"
BRANCH="${DEPLOY_BRANCH:-main}"
MESSAGE="${1:-}"

cd "$(dirname "$0")/.."

if [ -n "$(git status --porcelain)" ]; then
    if [ -z "$MESSAGE" ]; then
        echo "Есть незакоммиченные изменения. Передай текст коммита:"
        echo "  ./scripts/deploy.sh \"что изменилось\""
        exit 1
    fi
    echo "→ Коммит"
    git add -A
    git commit -q -m "$MESSAGE"
fi

echo "→ Push в origin/$BRANCH"
git push -q origin "$BRANCH"

echo "→ Сервер: git pull и пересборка"
ssh "$TARGET" "set -e
  cd $REMOTE_DIR
  git fetch -q origin $BRANCH
  git reset -q --hard origin/$BRANCH
  docker compose -f docker/docker-compose.prod.yml up -d --build
  sleep 20
  docker exec django_web_baitur python manage.py migrate --noinput
  docker exec django_web_baitur python manage.py compilemessages
  docker exec django_web_baitur python manage.py collectstatic --noinput --clear
  # Обязательный перезапуск: имена файлов статики содержат хеш, а gunicorn
  # держит их карту в памяти с момента старта. Без перезапуска страницы
  # ссылаются на старые имена и остаются без стилей.
  docker restart django_web_baitur"

echo "→ Готово: https://bautur.zeastudio.su"

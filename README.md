# Baytur Resort & Spa — новый сайт с онлайн-бронированием

Django-проект по ТЗ «Разработка нового сайта с онлайн-бронированием Baytur Resort & Spa».
Собственный модуль бронирования, интеграция с PMS Shelter, оплата через FreedomPay,
три языка (ru / en / ky), встроенное SEO.

## Стек

- Django 5.2, PostgreSQL 14, Redis
- django-modeltranslation — переводы контента
- django-ckeditor, django-resized — контент и оптимизация изображений
- Docker / docker-compose (dev и prod)
- Вёрстка: чистые HTML/CSS/JS, без внешних библиотек и шрифтов (для PageSpeed)

## Структура

```
app/
├── core/                  настройки, маршруты
│   └── settings/          base / dev / prod
├── apps/
│   ├── base/              настройки сайта, главная, SEO-миксин, sitemap, шаблонные теги
│   ├── rooms/             категории номеров, удобства, фото
│   ├── booking/           бронирование, оплата, интеграции
│   │   ├── integrations/shelter.py       клиент PMS Shelter
│   │   ├── integrations/freedompay.py    оплата и подпись запросов
│   │   ├── services.py    сценарий брони: поиск → расчёт → оплата → запись в PMS
│   │   └── notifications.py письма гостю и администратору
│   ├── services/          услуги курорта и конференц-залы
│   ├── offers/            спецпредложения и промокоды
│   ├── gallery/           фотоальбомы, видео, 3D-туры
│   ├── blog/              новости и отзывы
│   ├── contacts/          формы обратной связи, заявки, подписка
│   └── cms/               текстовые и служебные страницы
├── templates/             base, include, pages, emails, seo
└── static/                css, js, img
```

## Запуск в разработке

```bash
cp .envtest .env          # и заполнить значения
docker compose -f docker/docker-compose.yml up --build
```

Сайт: http://127.0.0.1:8085 · Админка: http://127.0.0.1:8085/admin/

Все команды Django выполняются внутри контейнера:

```bash
docker exec -it django_web_baitur python manage.py createsuperuser
docker exec -it django_web_baitur python manage.py makemigrations
docker exec -it django_web_baitur python manage.py migrate
docker exec -it django_web_baitur python manage.py seed_demo        # демо-контент
docker compose -f docker/docker-compose.yml logs -f web_baitur      # логи
```

Порты dev-окружения: сайт `8085`, postgres `5434`, redis `6390`
(8084/5433/6389 заняты другим проектом на этой машине).

## Прод

```bash
docker compose -f docker/docker-compose.prod.yml up --build -d
```

Gunicorn слушает внутри контейнера `:8000`, наружу проброшен `127.0.0.1:8091` —
перед ним ставится nginx с сертификатом для `resort.baytur.kg`.

## Переменные окружения

Основное — в `.envtest`. Ключевые блоки:

| Блок | Что настраивается |
|---|---|
| `SHELTER_*` | адрес API PMS, ключ, ID отеля. `SHELTER_ENABLED=0` → работает локальный резервный расчёт наличия |
| `FREEDOMPAY_*` | merchant id, секретный ключ, тестовый режим, `PREPAY_PERCENT` (100 — полная предоплата, 30 — частичная) |
| `EMAIL_*`, `BOOKING_ADMIN_EMAILS` | письма о бронях и заявках. Пустой `EMAIL_HOST` → письма печатаются в консоль |
| `TELEGRAM_*` | дублирование уведомлений в Telegram (опционально) |

## Как работает бронирование

1. Гость выбирает даты и гостей → сайт спрашивает наличие и цены у **Shelter**.
2. Выбирает категорию → на шаге оформления цена **пересчитывается заново**
   (нельзя оплатить устаревшую цену или занятый номер).
3. Заполняет данные → создаётся бронь в статусе «ожидает оплаты».
4. Оплата на стороне **FreedomPay**, данные карт на сайте не хранятся.
5. Серверный колбэк `/booking/payment/result/` — единственный источник правды об оплате,
   проверяется подпись `pg_sig`.
6. После успешной оплаты бронь **записывается в Shelter**, статус → «подтверждена»,
   уходят письма гостю и администратору.

Если Shelter недоступна в момент записи, бронь остаётся оплаченной с текстом ошибки,
администратор получает отдельное письмо и заводит бронь в PMS вручную —
деньги гостя не теряются. В админке есть действие «Повторить запись брони в Shelter».

## Что нужно от Заказчика / Shelter

- Документация и доступы к API Shelter. Эндпоинты в `integrations/shelter.py` — заготовка,
  сверяется с их контрактом: `ENDPOINT_AVAILABILITY`, `ENDPOINT_RESERVATION`, методы `_parse_*`.
- Коды категорий номеров в Shelter — заполняются в админке в поле «Код категории в Shelter».
- Договор эквайринга FreedomPay: merchant id и секретный ключ.
- Логотип, фото/видео, тексты, цены, реквизиты, переводы на en/ky.

## Фаза 2 — переход на Oracle Opera (весна 2027)

Модуль бронирования не меняется. Нужно написать `OperaClient` с тем же контрактом
(`get_availability` / `create_reservation` / `cancel_reservation`) и переключить
`get_shelter_client()` — остальной код сайта трогать не придётся.

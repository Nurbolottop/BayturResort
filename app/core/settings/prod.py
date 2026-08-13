from core.settings.base import *

DEBUG = False

# Пока сайт открыт по IP без сертификата, secure-куки ставить нельзя —
# браузер их не отдаст и не пустит в админку. После подключения домена
# и Let's Encrypt в .env выставляется SECURE_COOKIES=1.
SESSION_COOKIE_SECURE = env_bool('SECURE_COOKIES', True)
CSRF_COOKIE_SECURE = env_bool('SECURE_COOKIES', True)

# Запросы приходят через nginx, схему берём из его заголовка
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# nginx кеширует статику на 30 дней. Без хеша в имени файла браузер держит
# старый CSS после каждой правки дизайна — именно так «поменянные цвета»
# не доезжали до пользователя. ManifestStaticFilesStorage подставляет в имя
# хеш содержимого (main.4f2a1c.css), поэтому новая версия подхватывается
# сразу, а долгий кеш становится безопасным.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

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

# Редирект на https делает и nginx, но он не спасает от перехвата самого
# первого запроса по http. HSTS говорит браузеру ходить на домен только по
# https ещё до отправки запроса — за той же переменной, что и secure-куки,
# чтобы сайт можно было поднять по голому IP без сертификата.
SECURE_SSL_REDIRECT = env_bool('SECURE_COOKIES', True)
SECURE_HSTS_SECONDS = 31536000  # год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Страницы сайта не должны открываться внутри чужого фрейма: так подделывают
# клики по кнопкам в админке. Исключение сделано только для файлового
# менеджера CKEditor (см. core/urls.py) — он сам работает во фрейме.
X_FRAME_OPTIONS = 'DENY'

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

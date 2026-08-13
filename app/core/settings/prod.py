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

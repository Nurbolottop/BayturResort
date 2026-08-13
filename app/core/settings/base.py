"""
Baytur Resort & Spa — базовые настройки Django.

Содержимое сайта многоязычное (ru / en / ky) через django-modeltranslation,
интерфейс — через стандартный i18n Django.
"""

from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None or value == '':
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


# =============================================================================
# PATHS (ПУТИ)
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY (БЕЗОПАСНОСТЬ)
# =============================================================================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise Exception("SECRET_KEY не задан в переменных окружения")

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Публичный адрес сайта — нужен для канонических URL, sitemap и колбэков оплаты
SITE_URL = os.getenv('SITE_URL', 'https://resort.baytur.kg').rstrip('/')

# =============================================================================
# APPLICATIONS (ПРИЛОЖЕНИЯ)
# =============================================================================

INSTALLED_APPS = [
    # modeltranslation должен идти до django.contrib.admin
    'modeltranslation',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # Third-party
    'ckeditor',
    'ckeditor_uploader',
    'django_resized',

    # Local apps
    'apps.base',
    'apps.rooms',
    'apps.booking',
    'apps.services',
    'apps.offers',
    'apps.gallery',
    'apps.blog',
    'apps.contacts',
    'apps.cms',
]

# =============================================================================
# MIDDLEWARE (ПРОМЕЖУТОЧНЫЕ ОБРАБОТЧИКИ)
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =============================================================================
# URLS & WSGI (МАРШРУТЫ И WSGI)
# =============================================================================

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'


# =============================================================================
# TEMPLATES (ШАБЛОНЫ)
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.base.context_processors.site_settings',
            ],
        },
    },
]

# =============================================================================
# DATABASE (БАЗА ДАННЫХ)
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': int(os.getenv('POSTGRES_PORT', 5432)),
    }
}

# =============================================================================
# PASSWORD VALIDATION (ВАЛИДАЦИЯ ПАРОЛЕЙ)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# INTERNATIONALIZATION (ИНТЕРНАЦИОНАЛИЗАЦИЯ)
# =============================================================================

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru')
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Bishkek')
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('ru', 'Русский'),
    ('en', 'English'),
    ('ky', 'Кыргызча'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# django-modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'ru'
MODELTRANSLATION_LANGUAGES = ('ru', 'en', 'ky')
MODELTRANSLATION_FALLBACK_LANGUAGES = ('ru', 'en', 'ky')

# =============================================================================
# STATIC & MEDIA FILES (СТАТИЧЕСКИЕ И МЕДИА ФАЙЛЫ)
# =============================================================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
# EMAIL (ПОЧТА — ПОДТВЕРЖДЕНИЯ БРОНЕЙ)
# =============================================================================

EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', True)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', False)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Baytur Resort <noreply@baytur.kg>')

# Кому дублировать уведомления о новых бронях и заявках
BOOKING_ADMIN_EMAILS = env_list('BOOKING_ADMIN_EMAILS')

if not EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# ИНТЕГРАЦИЯ С PMS SHELTER
# =============================================================================

SHELTER = {
    'ENABLED': env_bool('SHELTER_ENABLED', False),
    'BASE_URL': os.getenv('SHELTER_BASE_URL', '').rstrip('/'),
    'API_KEY': os.getenv('SHELTER_API_KEY', ''),
    'HOTEL_ID': os.getenv('SHELTER_HOTEL_ID', ''),
    'TIMEOUT': int(os.getenv('SHELTER_TIMEOUT', 15)),
}

# =============================================================================
# ИМПОРТ ОТЗЫВОВ ИЗ ВНЕШНИХ СЕРВИСОВ
# =============================================================================
# Google Places отдаёт не больше 5 отзывов на точку — это ограничение самого
# Google. 2ГИС отзывы по открытому API не отдаёт: ключ выдаётся партнёрам,
# поэтому импорт включается только когда ключ реально есть.

REVIEWS_IMPORT = {
    'GOOGLE_API_KEY': os.getenv('GOOGLE_PLACES_API_KEY', ''),
    'GOOGLE_PLACE_ID': os.getenv('GOOGLE_PLACE_ID', ''),
    'TWOGIS_API_KEY': os.getenv('TWOGIS_REVIEWS_KEY', ''),
    'TWOGIS_BRANCH_ID': os.getenv('TWOGIS_BRANCH_ID', ''),
    'TIMEOUT': int(os.getenv('REVIEWS_IMPORT_TIMEOUT', 20)),
}

# =============================================================================
# ОНЛАЙН-ОПЛАТА FREEDOMPAY
# =============================================================================

FREEDOMPAY = {
    'ENABLED': env_bool('FREEDOMPAY_ENABLED', False),
    'MERCHANT_ID': os.getenv('FREEDOMPAY_MERCHANT_ID', ''),
    'SECRET_KEY': os.getenv('FREEDOMPAY_SECRET_KEY', ''),
    'TESTING_MODE': env_bool('FREEDOMPAY_TESTING_MODE', True),
    'PREPAY_PERCENT': int(os.getenv('FREEDOMPAY_PREPAY_PERCENT', 100)),
    'INIT_URL': 'https://api.freedompay.kg/init_payment.php',
    'CURRENCY': 'KGS',
}

# =============================================================================
# TELEGRAM-УВЕДОМЛЕНИЯ (ОПЦИОНАЛЬНО)
# =============================================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# =============================================================================
# DEFAULTS (ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ)
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# =============================================================================
# CKEDITOR (РЕДАКТОР CKEDITOR)
# =============================================================================

CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

# =============================================================================
# LOGGING (ЛОГИРОВАНИЕ ИНТЕГРАЦИЙ)
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'baitur': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

"""
Онлайн-оплата FreedomPay (п. 5.3 и 6.3 ТЗ).

Платёж инициируется на сайте, а карта вводится на стороне провайдера —
данные карт на сайте не хранятся и не проходят через него.

Схема подписи FreedomPay (наследие Paybox):
    md5( script_name ; значения_параметров_отсортированные_по_ключу ; secret_key )
Параметр pg_sig в подпись не входит.

Порядок:
  1. init_payment.php  -> получаем pg_redirect_url, ведём гостя туда;
  2. FreedomPay дергает наш result_url (серверный колбэк) — это единственный
     источник правды об успехе оплаты;
  3. гость возвращается на success_url / failure_url (только отображение).
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from decimal import Decimal

import requests
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('baitur.freedompay')


class FreedomPayError(Exception):
    """Ошибка при обращении к FreedomPay."""


def make_signature(script_name, params, secret_key):
    """Подпись запроса/колбэка FreedomPay."""
    clean = {k: v for k, v in params.items() if k != 'pg_sig' and v is not None}
    values = [str(clean[key]) for key in sorted(clean)]
    raw = ';'.join([script_name, *values, secret_key])
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def verify_signature(script_name, params, secret_key):
    """Проверяет pg_sig во входящем колбэке. Без этого колбэк принимать нельзя."""
    received = params.get('pg_sig', '')
    expected = make_signature(script_name, params, secret_key)
    return bool(received) and received == expected


class FreedomPayClient:
    INIT_SCRIPT = 'init_payment.php'

    def __init__(self, config=None):
        config = config or settings.FREEDOMPAY
        self.merchant_id = config['MERCHANT_ID']
        self.secret_key = config['SECRET_KEY']
        self.testing_mode = config['TESTING_MODE']
        self.init_url = config['INIT_URL']
        self.currency = config['CURRENCY']

        if not self.merchant_id or not self.secret_key:
            raise FreedomPayError(_('Не заданы FREEDOMPAY_MERCHANT_ID / FREEDOMPAY_SECRET_KEY.'))

    def init_payment(self, *, order_id, amount, description, success_url, failure_url,
                     result_url, phone='', email='', language='ru'):
        """Создаёт платёж и возвращает dict с payment_id и redirect_url."""
        params = {
            'pg_merchant_id': self.merchant_id,
            'pg_order_id': str(order_id),
            'pg_amount': str(Decimal(amount).quantize(Decimal('0.01'))),
            'pg_currency': self.currency,
            'pg_description': description[:255],
            'pg_salt': get_random_string(16),
            'pg_success_url': success_url,
            'pg_failure_url': failure_url,
            'pg_result_url': result_url,
            'pg_request_method': 'POST',
            'pg_success_url_method': 'GET',
            'pg_failure_url_method': 'GET',
            'pg_testing_mode': '1' if self.testing_mode else '0',
            'pg_language': 'ru' if language == 'ky' else language,
        }
        if phone:
            params['pg_user_phone'] = phone
        if email:
            params['pg_user_contact_email'] = email

        params['pg_sig'] = make_signature(self.INIT_SCRIPT, params, self.secret_key)

        try:
            response = requests.post(self.init_url, data=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error('FreedomPay init_payment — сеть недоступна: %s', exc)
            raise FreedomPayError(_('Платёжный сервис недоступен. Попробуйте позже.')) from exc

        data = self._parse_xml(response.text)

        if data.get('pg_status') != 'ok':
            message = data.get('pg_error_description') or _('Не удалось создать платёж.')
            logger.error('FreedomPay init_payment отклонён: %s', data)
            raise FreedomPayError(message)

        return {
            'payment_id': data.get('pg_payment_id', ''),
            'redirect_url': data.get('pg_redirect_url', ''),
            'raw': data,
            'request': {k: v for k, v in params.items() if k != 'pg_sig'},
        }

    @staticmethod
    def _parse_xml(text):
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            logger.error('FreedomPay: ответ не XML: %s', text[:500])
            raise FreedomPayError(_('Некорректный ответ платёжного сервиса.')) from exc
        return {child.tag: (child.text or '') for child in root}

    @staticmethod
    def build_callback_response(script_name, *, status, description, secret_key, salt=''):
        """XML-ответ провайдеру на его колбэк — он ждёт подписанный ответ."""
        params = {
            'pg_status': status,
            'pg_description': description,
            'pg_salt': salt or get_random_string(16),
        }
        params['pg_sig'] = make_signature(script_name, params, secret_key)
        body = ''.join(f'<{k}>{v}</{k}>' for k, v in params.items())
        return f'<?xml version="1.0" encoding="utf-8"?><response>{body}</response>'


def get_freedompay_client():
    return FreedomPayClient()


def calculate_prepay_amount(total_amount):
    """Сумма к онлайн-оплате: полная или частичная предоплата (настройка Заказчика)."""
    percent = Decimal(settings.FREEDOMPAY['PREPAY_PERCENT'])
    amount = (Decimal(total_amount) * percent / Decimal('100')).quantize(Decimal('0.01'))
    return min(amount, Decimal(total_amount))

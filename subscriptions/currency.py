from decimal import Decimal

from django.conf import settings


def convert_to_base(amount: Decimal, currency: str) -> Decimal:
    rate = Decimal(str(settings.EXCHANGE_RATES.get(currency.upper(), 1)))
    if rate == 0:
        return Decimal("0")
    return amount * rate

""" Constants for the Yandex.Lavka integration. """

import enum

DOMAIN = 'yandex_lavka'
DEFAULT_NAME = "Yandex.Lavka"

BASE_URL = "https://lavka.yandex.ru"

class DepotType(enum.StrEnum):
	SUPERMARKET = 'supermarket'
DEPOT_TYPES = frozenset(map(str, DepotType))

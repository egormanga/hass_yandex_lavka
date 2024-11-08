import asyncio
import logging

from ..yandex_station.core.yandex_session import YandexSession
from .const import BASE_URL


_LOGGER = logging.getLogger(__name__)

API_BASE_URL = f"{BASE_URL}/api/v1"


class YandexLavka:
    session: YandexSession

    def __init__(self, session: YandexSession):
        self.session = session

    async def service_info(self, location: tuple[float | str, float | str]) -> dict:
        r = await self.session.get(f"{API_BASE_URL}/providers/v2/service-info", params={f"position[location][{ii}]": i for ii, i in enumerate(location)})

        return await r.json()

    async def tracked_orders(self) -> list[dict]:
        r = await self.session.get(f"{API_BASE_URL}/providers/orders/v1/tracked-orders")

        return await r.json()

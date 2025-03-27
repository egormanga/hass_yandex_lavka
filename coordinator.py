import datetime
import logging

import async_timeout
from homeassistant.core import HomeAssistant
#from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_NAME
from .yandex_lavka import YandexLavka


_LOGGER = logging.getLogger(__name__)


class YandexLavkaServiceInfoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, lavka: YandexLavka):
        super().__init__(
            hass,
            _LOGGER,
            name=DEFAULT_NAME,
            update_interval=datetime.timedelta(seconds=15),
            always_update=True,
        )
        self.lavka = lavka

    async def _async_update_data(self) -> dict:
        try:
            async with async_timeout.timeout(10):
                service_info = await self.lavka.service_info((self.hass.config.longitude, self.hass.config.latitude))
        #except ApiAuthError as err:
        #    # Raising ConfigEntryAuthFailed will cancel future updates
        #    # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #    raise ConfigEntryAuthFailed() from err
        except Exception as ex:
            raise UpdateFailed() from ex

        return service_info


class YandexLavkaOrdersCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, lavka: YandexLavka):
        super().__init__(
            hass,
            _LOGGER,
            name=DEFAULT_NAME,
            update_interval=datetime.timedelta(seconds=15),
            always_update=True,
        )
        self.lavka = lavka

    async def _async_update_data(self) -> dict:
        try:
            async with async_timeout.timeout(10):
                orders = await self.lavka.tracked_orders()
        #except ApiAuthError as err:
        #    # Raising ConfigEntryAuthFailed will cancel future updates
        #    # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #    raise ConfigEntryAuthFailed() from err
        except Exception as ex:
            raise UpdateFailed() from ex

        return {i['id']: i for i in orders}

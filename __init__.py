""" Yandex.Lavka integration. """

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client as ac,
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import voluptuous as vol

from ..yandex_station.core.const import DATA_CONFIG
from ..yandex_station.core.yandex_session import YandexSession
from .const import DOMAIN
from .coordinator import YandexLavkaOrdersCoordinator, YandexLavkaServiceInfoCoordinator
from .yandex_lavka import YandexLavka


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_DEBUG = "debug"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_TOKEN): cv.string,
        vol.Optional(CONF_DEBUG, default=False): cv.boolean,
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

type YandexLavkaConfigEntry = ConfigEntry[YandexLavkaCoordinator]


async def async_setup(hass: HomeAssistant, hass_config: dict):
    config: dict = (hass_config.get(DOMAIN) or {})
    hass.data[DOMAIN] = {DATA_CONFIG: config}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: YandexLavkaConfigEntry):
    async def update_cookie_and_token(**kwargs):
        hass.config_entries.async_update_entry(entry, data=kwargs)

    session = ac.async_create_clientsession(hass)
    yandex = YandexSession(session, **entry.data)
    yandex.add_update_listener(update_cookie_and_token)

    try:
        ok = await yandex.refresh_cookies()
    except Exception as e:
        raise ConfigEntryNotReady() from e

    if not ok:
        hass.components.persistent_notification.async_create(
            "Необходимо заново авторизоваться в Яндексе. Для этого [добавьте "
            "новую интеграцию](/config/integrations) с тем же логином.",
            title="Yandex.Lavka",
        )
        return False

    lavka = YandexLavka(yandex)

    if not entry.update_listeners:
        entry.add_update_listener(async_update_options)

    data = hass.data[DOMAIN][entry.unique_id] = {
        'service_info_coordinator': YandexLavkaServiceInfoCoordinator(hass, lavka),
        'orders_coordinator': YandexLavkaOrdersCoordinator(hass, lavka),
    }
    await asyncio.gather(*(i.async_config_entry_first_refresh() for i in data.values() if isinstance(i, DataUpdateCoordinator)))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_options(hass: HomeAssistant, config_entry: YandexLavkaConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: YandexLavkaConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

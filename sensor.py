import itertools

from homeassistant.const import MATCH_ALL, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import YandexLavkaConfigEntry
from .const import BASE_URL, DEFAULT_NAME, DOMAIN
from .coordinator import YandexLavkaOrdersCoordinator, YandexLavkaServiceInfoCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: YandexLavkaConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.unique_id]

    service_info_coordinator: YandexLavkaServiceInfoCoordinator = data['service_info_coordinator']
    orders_coordinator: YandexLavkaOrdersCoordinator = data['orders_coordinator']

    async_add_entities(itertools.chain(
        map(lambda x: x(service_info_coordinator), (DeliveryCostEntity, DeliveryTimeEntity, CashbackEntity)),
        map(lambda x: x(orders_coordinator), (OrdersEntity, ActiveOrdersEntity)),
        (OrderEntity(orders_coordinator, i) for i in orders_coordinator.data),
    ), update_before_add=True)


class YandexLavkaServiceInfoEntity(CoordinatorEntity[YandexLavkaServiceInfoCoordinator]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=f"{DEFAULT_NAME} {self.coordinator.config_entry.title}",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BASE_URL,
        )


class DeliveryCostEntity(YandexLavkaServiceInfoEntity):
    _attr_translation_key = 'delivery_cost'
    _attr_has_entity_name = True
    _unrecorded_attributes = {MATCH_ALL}

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{self.translation_key}"
        self._attr_unit_of_measurement = self._currency

    @callback
    def _handle_coordinator_update(self) -> None:
        pricing = self._pricing

        self._attr_state = pricing['deliveryCost']
        self._attr_extra_state_attributes = self.coordinator.data

        self.async_write_ha_state()

    @property
    def _currency(self) -> str:
        return self.coordinator.data['currencySign']

    @property
    def _pricing(self) -> dict:
        return self.coordinator.data['pricingConditions']


class DeliveryTimeEntity(YandexLavkaServiceInfoEntity):
    _attr_translation_key = 'delivery_time'
    _attr_has_entity_name = True
    _unrecorded_attributes = {MATCH_ALL}

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{self.translation_key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_state = self._text
        self._attr_extra_state_attributes = self.coordinator.data

        self.async_write_ha_state()

    @property
    def _text(self) -> str:
        return self.coordinator.data['deliveryTimeText']


class CashbackEntity(YandexLavkaServiceInfoEntity):
    _attr_translation_key = 'cashback'
    _attr_has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{self.translation_key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_state = self._cashbackAmount
        self._attr_extra_state_attributes = self._cashback

        self.async_write_ha_state()

    @property
    def _cashback(self) -> dict:
        return self.coordinator.data['cashback']

    @property
    def _cashbackAmount(self) -> int:
        return self.coordinator.data['cashbackAmount']


class YandexLavkaOrdersEntity(CoordinatorEntity[YandexLavkaOrdersCoordinator]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=f"{DEFAULT_NAME} {self.coordinator.config_entry.title}",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BASE_URL,
        )


class OrdersEntity(YandexLavkaOrdersEntity):
    _attr_translation_key = 'orders'
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{self.translation_key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        orders = self._orders

        self._attr_state = len(orders)
        self._attr_extra_state_attributes = {
            'orders': tuple(orders.keys()),
        }

        self.async_write_ha_state()

    @property
    def _orders(self) -> list[dict]:
        return self.coordinator.data


class ActiveOrdersEntity(OrdersEntity):
    _attr_translation_key = 'orders_active'

    @property
    def _orders(self) -> list[dict]:
        return {k: v for k, v in self.coordinator.data.items() if v.get('status') != 'closed'}


class OrderEntity(YandexLavkaOrdersEntity):
    _attr_translation_key = 'order'
    _attr_has_entity_name = True
    _unrecorded_attributes = {MATCH_ALL}

    def __init__(self, coordinator, order_id):
        super().__init__(coordinator)
        self._order_id = order_id
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{self.translation_key}_{slugify(order_id)}"
        self._attr_entity_registry_visible_default = (self._order.get('status') != 'closed')
        self._attr_translation_placeholders = {
            'order_no': order_id,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        order = self._order

        self._attr_state = order['status']
        self._attr_entity_picture = order['trackingInfo']['groceryImage']
        self._attr_translation_placeholders = {
            'order_no': order['shortOrderId'],
        }
        self._attr_extra_state_attributes = order

        self.async_write_ha_state()

    @property
    def _order(self) -> dict:
        return self.coordinator.data[self._order_id]

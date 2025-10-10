import logging
from dataclasses import dataclass

from tgtg_scanner.errors import TgtgAPIError
from tgtg_scanner.models.item import Item
from tgtg_scanner.models.dynamic_item import DynamicItem
from tgtg_scanner.tgtg import TgtgClient
from tgtg_scanner.models.alert_manager import AlertManager

log = logging.getLogger("tgtg")


@dataclass
class AddFavoriteRequest:
    item_id: str
    item_display_name: str
    proceed: bool


@dataclass
class RemoveFavoriteRequest:
    item_id: str
    item_display_name: str
    proceed: bool


class Favorites:
    def __init__(self, client: TgtgClient, alert_manager: AlertManager) -> None:
        self.client = client
        self.alert_manager = alert_manager

    def is_item_favorite(self, item_id: str) -> bool:
        """Returns true if the provided item ID is in the favorites.

        Args:
            item_id (str): Item ID
        Returns:
            bool: true, if the provided item ID is in the favorites

        """
        return any(item for item in self.client.get_favorites() if Item(item).item_id == item_id)

    def is_dynamic_favorite(self, item_id: str) -> bool:
        """Returns true if the provided item ID is a dynamic favorite.

        Args:
            item_id (str): Item ID
        Returns:
            bool: true, if the provided item ID is a dynamic favorite

        """
        log.debug("Checking if item %s is a dynamic favorite", item_id)
        dynamic_favorites = [Item(item) for item in self.client.get_favorites() if Item(item).price_type == "gradual_lower_price"]
        log.debug(f"dynamic favorites: {dynamic_favorites}")
        return any(item for item in dynamic_favorites if item.item_id == item_id)

    def get_item_by_id(self, item_id: str) -> Item:
        """Gets an item by the Item ID.

        Args:
            item_id (str): Item ID
        Returns:
            Item: the Item for the Item ID or an empty Item

        """
        try:
            return Item(self.client.get_item(item_id))
        except TgtgAPIError:
            return Item({})

    def get_favorites(self) -> list[Item]:
        """Get all favorite items.

        Return:
            List: List of favorite items

        """
        return [Item(item) for item in self.client.get_favorites()]

    def get_dynamic_favorites(self) -> list[Item]:
        """Get all favorite items

        Return:
            List: List of favorite items

        """
        dynamic_favorites = [DynamicItem(item) for item in self.client.get_favorites()
                             if Item(item).price_type == "gradual_lower_price"]

        # inject the alert_price
        for item in dynamic_favorites:
            price = self.alert_manager.get_price(item.item_id)
            if price is not None:
                item.alert_price = price
        return dynamic_favorites

    def add_favorites(self, item_ids: list[str]) -> None:
        """Adds all the provided item IDs to the favorites.

        Args:
            item_ids (str): Item ID list

        """
        for item_id in item_ids:
            self.client.set_favorite(item_id, True)

    def remove_favorite(self, item_ids: list[str]) -> None:
        """Removes all the provided item IDs from the favorites.

        Args:
            item_ids (str): Item ID list

        """
        for item_id in item_ids:
            self.client.set_favorite(item_id, False)

import json
import logging
import os
from typing import Optional

log = logging.getLogger("tgtg")

DATA_DIR = "/alertprice_data"
ALERT_PRICES_FILE = os.path.join(DATA_DIR, "alert_prices.json")

class AlertManager:
    """Manages loading, saving, and accessing alert prices."""
    def __init__(self):
        self.alert_prices: dict = self._load_prices()

    def _load_prices(self) -> dict:
        try:
            with open(ALERT_PRICES_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_prices(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ALERT_PRICES_FILE, "w") as f:
            json.dump(self.alert_prices, f, indent=4)

    def get_price(self, item_id: str) -> Optional[float]:
        """Gets the alert price for a specific item ID."""
        return self.alert_prices.get(item_id)

    def set_price(self, item_id: str, price: float) -> None:
        """Sets an alert price and saves it."""
        self.alert_prices[item_id] = price
        self._save_prices()

    def delete_price(self, item_id: str) -> None:
        """Deletes an alert price and saves it."""
        if item_id in self.alert_prices:
            del self.alert_prices[item_id]
            self._save_prices()
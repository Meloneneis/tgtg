from typing import Optional, Union

from tgtg_scanner.models.item import Item
from tgtg_scanner.models.location import Location

class DynamicItem(Item):
    def __init__(self, data: dict, location: Union[Location, None] = None, locale: str = "en_US"):
        super().__init__(data, location, locale)
        self.alert_price: Optional[float] = None
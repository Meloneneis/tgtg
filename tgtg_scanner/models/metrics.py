import logging
from datetime import datetime, timedelta, timezone

from prometheus_client import Counter, Gauge, start_http_server

from tgtg_scanner.models.item import Item
from tgtg_scanner.models.alert_manager import AlertManager

log = logging.getLogger("tgtg")


def _parse_iso_as_aware_utc(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    # Normalize to UTC
    return dt.astimezone(timezone.utc)

def format_interval_today_tomorrow(pickup_interval_start: str, pickup_interval_end: str) -> str:
    try:
        # Parse inputs as UTC-aware
        start_utc = _parse_iso_as_aware_utc(pickup_interval_start)
        end_utc = _parse_iso_as_aware_utc(pickup_interval_end)

        # Detect local timezone from the host and convert (handles DST automatically)
        local_tz = datetime.now().astimezone().tzinfo
        start_local = start_utc.astimezone(local_tz)
        end_local = end_utc.astimezone(local_tz)

        # Decide Today/Tomorrow relative to local calendar date
        today_local = datetime.now(local_tz).date()
        start_date = start_local.date()
        if start_date == today_local:
            label = "Today"
        elif start_date == today_local + timedelta(days=1):
            label = "Tomorrow"
        else:
            label = start_local.strftime("%d.%m.%Y")  # fallback date (German numeric)

        return f"{label} {start_local:%H:%M} - {end_local:%H:%M}"
    except Exception as exc:
        log.warning(
            "Error formatting interval %r – %r: %s",
            pickup_interval_start, pickup_interval_end, exc
        )
        return f"{pickup_interval_start} - {pickup_interval_end}"


class Metrics:
    """Provides a prometheus metrics client."""

    def __init__(self, port: int = 8000):
        self.port = port
        item_params = ["item_id", "display_name", "items_available", "pickup_interval", "item_price"]
        self.item_count = Gauge("tgtg_item_count", "Currently available Magic Bags", item_params)
        self.item_price = Gauge("tgtg_item_price", "Price for a Magic Bag", item_params)
        self.item_value = Gauge("tgtg_item_value", "Value for a Magic Bag", item_params)
        self.item_alert_difference = Gauge("tgtg_item_alert_difference", "Alert difference for a Magic Bag", item_params)
        self.get_favorites_errors = Counter(
            "tgtg_get_favorites_errors",
            "Count of request errors fetching tgtg favorites",
        )
        self.send_notifications = Counter(
            "tgtg_send_notifications",
            "Count of send notifications",
            item_params,
        )

    def enable_metrics(self) -> None:
        """Start the metrics http server."""
        start_http_server(self.port)
        log.info("Metrics server started on port %s", self.port)

    def update(self, item: Item) -> None:
        """Update the metrics."""
    def update(self, item: Item, alert_manager: AlertManager) -> None:
        """
        Update the metrics.
        """
        try:
            pickup_interval = format_interval_today_tomorrow(item.pickup_interval_start, item.pickup_interval_end)
            item_labels = [
                item.item_id,
                item.display_name,
                str(item.items_available),
                pickup_interval,
                str(item._price)
            ]

            self.item_count.labels(*item_labels).set(item.items_available)
            self.item_price.labels(*item_labels).set(item._price)
            self.item_value.labels(*item_labels).set(item._value)

            # Check if this item has an alert price configured
            alert_price = alert_manager.get_price(item.item_id)
            if alert_price is not None:
                self.item_alert_difference.labels(*item_labels).set(alert_price - item._price)
                log.info(f"Set alert price to {alert_price}")
        except ValueError as err:
            log.warning("Error updating metrics: %s", err)

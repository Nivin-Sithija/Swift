import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.core.config import get_settings

broker = RedisBroker(url=get_settings().redis_url)
dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=3)
def process_ticket(ticket_id: str) -> None:
    """Queue entry point; inline processing is the deterministic development default."""
    if not ticket_id:
        raise ValueError("ticket_id is required")

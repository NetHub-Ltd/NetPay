"""Redis helpers; Redis is auxiliary and never the durable payment store."""
from redis.asyncio import Redis
from app.core.config import Settings

def create_redis_client(settings: Settings) -> Redis:
    """Create a bounded asynchronous Redis client."""
    return Redis.from_url(settings.redis_url.get_secret_value(), decode_responses=True, socket_connect_timeout=2.0, socket_timeout=2.0, health_check_interval=30)

async def check_redis(client: Redis) -> None:
    """Raise when Redis health ping fails."""
    await client.ping()

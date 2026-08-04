from collections.abc import Callable

from fastapi import HTTPException, Request
from redis.exceptions import RedisError

from app.infrastructure.redis import redis_client


def rate_limit(scope: str, limit: int, window_seconds: int = 60) -> Callable:
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = f"stay-scale:rate:{scope}:{client}"
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, window_seconds)
        except RedisError:
            return
        if count > limit:
            raise HTTPException(status_code=429, detail="Too many requests; please try again later")

    return dependency

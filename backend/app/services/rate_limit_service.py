import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import redis
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitService:
    def __init__(self) -> None:
        self.redis_client = None
        self.fallback_store: Dict[str, List[datetime]] = {}

        try:
            redis_url = settings.REDIS_URL
            if not redis_url.startswith(("redis://", "rediss://")):
                redis_url = f"redis://{redis_url}"
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self.redis_client.ping()
            logger.info("Rate limit service initialized with Redis")
        except Exception as exc:
            logger.warning("Redis unavailable for rate limit, using local fallback: %s", exc)
            self.redis_client = None

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        if self.redis_client:
            self._check_redis(key, limit, window_seconds)
            return
        self._check_local(key, limit, window_seconds)

    def _check_redis(self, key: str, limit: int, window_seconds: int) -> None:
        redis_key = f"rate_limit:{key}"
        try:
            current = self.redis_client.incr(redis_key)
            if current == 1:
                self.redis_client.expire(redis_key, window_seconds)
            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Redis rate limit check failed, using local fallback: %s", exc)
            self._check_local(key, limit, window_seconds)

    def _check_local(self, key: str, limit: int, window_seconds: int) -> None:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        attempts = [item for item in self.fallback_store.get(key, []) if item >= window_start]
        if len(attempts) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
            )
        attempts.append(now)
        self.fallback_store[key] = attempts


rate_limit_service = RateLimitService()

import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching chatbot responses using Redis."""
    
    def __init__(self):
        try:
            # Parse Redis URL
            redis_url = settings.REDIS_URL
            if redis_url.startswith("redis://"):
                # Remove redis:// prefix and parse
                parts = redis_url.replace("redis://", "").split("/")
                host_port = parts[0].split(":")
                host = host_port[0] if len(host_port) > 0 else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(parts[1]) if len(parts) > 1 else 0
            else:
                host = "localhost"
                port = 6380
                db = 0
            
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Cache service initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, cache disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_cache_key(self, user_id: str, message: str, context_hash: Optional[str] = None) -> str:
        """Generate a cache key from user ID, message, and optional context."""
        # Normalize message (lowercase, strip whitespace)
        normalized_msg = message.lower().strip()
        
        # Create hash of message
        msg_hash = hashlib.md5(normalized_msg.encode()).hexdigest()[:8]
        
        # Include context hash if provided
        if context_hash:
            return f"chatbot:cache:{user_id}:{msg_hash}:{context_hash}"
        return f"chatbot:cache:{user_id}:{msg_hash}"
    
    def _is_simple_message(self, message: str) -> bool:
        """Check if message is a simple greeting or common question that can be cached longer."""
        simple_patterns = [
            "olá", "ola", "oi", "hey", "hi", "hello",
            "tchau", "até logo", "obrigado", "obrigada", "valeu",
            "ajuda", "help", "como funciona", "o que você faz",
            "bom dia", "boa tarde", "boa noite",
            "obrigado", "obrigada", "valeu", "thanks"
        ]
        normalized = message.lower().strip()
        return any(pattern in normalized for pattern in simple_patterns)
    
    def get_cached_response(self, user_id: str, message: str, context_hash: Optional[str] = None) -> Optional[str]:
        """Get cached response if available."""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key(user_id, message, context_hash)
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key[:50]}")
                return cached
            return None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    def set_cached_response(
        self, 
        user_id: str, 
        message: str, 
        response: str, 
        context_hash: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """Cache a response with appropriate TTL."""
        if not self.enabled:
            return
        
        try:
            cache_key = self._generate_cache_key(user_id, message, context_hash)
            
            # Determine TTL based on message type
            if ttl is None:
                if self._is_simple_message(message):
                    # Simple messages cached for 1 hour
                    ttl = 3600
                else:
                    # Contextual messages cached for 5 minutes
                    ttl = 300
            
            self.redis_client.setex(cache_key, ttl, response)
            logger.debug(f"Cached response for key: {cache_key[:50]} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache for a specific user."""
        if not self.enabled:
            return
        
        try:
            pattern = f"chatbot:cache:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def get_context_hash(self, context: Dict[str, Any]) -> str:
        """Generate a hash from context to use in cache key."""
        # Use only key metrics that affect response
        key_metrics = {
            "total_bills": context.get("total_bills", 0),
            "pending_bills": context.get("pending_bills", 0),
            "overdue_bills": context.get("overdue_bills", 0),
            "monthly_balance": round(context.get("monthly_balance", 0), 2),
            "current_month": context.get("current_month", "")
        }
        context_str = json.dumps(key_metrics, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]


# Global instance
cache_service = CacheService()


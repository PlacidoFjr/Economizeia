import hashlib
import json
import logging
import re
import unicodedata
from typing import Any, Dict, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-backed cache for chatbot responses.

    Cache keys are always isolated by user and schema version. Redis failures
    are swallowed so the chatbot flow never depends on cache availability.
    """

    MUTATING_PATTERNS = [
        "adicionar", "adiciona", "criar", "cria", "registrar", "registra",
        "lancar", "inserir", "paguei", "gastei", "recebi", "ganhei",
        "excluir", "apagar", "deletar", "cancelar", "editar", "alterar",
        "confirmar", "agendar", "marcar pago", "pago", "parcelado",
    ]
    SIMPLE_PATTERNS = [
        "ola", "oi", "hey", "hi", "hello", "bom dia", "boa tarde",
        "boa noite", "tchau", "ate logo", "obrigado", "obrigada",
        "valeu", "ajuda", "help", "como funciona", "o que voce faz",
        "o que vc faz", "como adicionar despesa", "como fazer upload",
        "como enviar boleto",
    ]

    def __init__(self):
        self.schema_version = settings.CHATBOT_CACHE_SCHEMA_VERSION
        self.enabled = bool(settings.CHATBOT_CACHE_ENABLED)
        self.redis_client = None

        if not self.enabled:
            logger.info("Chatbot cache disabled by configuration")
            return

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
            logger.info("Cache service initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, cache disabled: {e}")
            self.redis_client = None
            self.enabled = False

    def normalize_message(self, message: str) -> str:
        normalized = unicodedata.normalize("NFKD", message or "")
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _generate_cache_key(
        self,
        user_id: str,
        message: str,
        context_hash: Optional[str] = None,
        cache_type: str = "response",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        normalized_msg = self.normalize_message(message)
        message_hash = self._hash(normalized_msg)[:24]
        provider_part = self._hash(f"{provider or 'local'}:{model or 'rules'}")[:12]
        context_part = context_hash or "global"
        return (
            f"chatbot:{cache_type}:{self.schema_version}:"
            f"{user_id}:{provider_part}:{message_hash}:{context_part}"
        )

    def _is_simple_message(self, message: str) -> bool:
        normalized = self.normalize_message(message)
        return any(pattern in normalized for pattern in self.SIMPLE_PATTERNS)

    def is_cacheable_message(
        self,
        message: str,
        action: Optional[str] = None,
        has_pending_conversation: bool = False,
        requires_context: bool = False,
    ) -> bool:
        if action and action not in {"chat", "help", "financial_summary"}:
            return False
        if has_pending_conversation:
            return False
        if action == "financial_summary":
            return True

        normalized = self.normalize_message(message)
        if any(pattern in normalized for pattern in self.MUTATING_PATTERNS):
            return False
        return True

    def get_cached_response(
        self,
        user_id: str,
        message: str,
        context_hash: Optional[str] = None,
        cache_type: str = "response",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(
                user_id, message, context_hash, cache_type, provider, model
            )
            cached = self.redis_client.get(cache_key)
            logger.info("Chatbot cache %s", "hit" if cached else "miss")
            return cached
        except Exception as e:
            logger.error(f"Error getting chatbot cache: {e}")
            return None

    def set_cached_response(
        self,
        user_id: str,
        message: str,
        response: str,
        context_hash: Optional[str] = None,
        ttl: Optional[int] = None,
        cache_type: str = "response",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        if not self.enabled or not self.redis_client:
            return

        try:
            if ttl is None:
                ttl = (
                    settings.CHATBOT_CACHE_CONTEXTUAL_TTL
                    if context_hash
                    else settings.CHATBOT_CACHE_SIMPLE_TTL
                )

            cache_key = self._generate_cache_key(
                user_id, message, context_hash, cache_type, provider, model
            )
            self.redis_client.setex(cache_key, ttl, response)
            logger.info("Chatbot cache set ttl=%s contextual=%s", ttl, bool(context_hash))
        except Exception as e:
            logger.error(f"Error setting chatbot cache: {e}")

    def invalidate_user_cache(self, user_id: str):
        if not self.enabled or not self.redis_client:
            return

        try:
            pattern = f"chatbot:*:{self.schema_version}:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            logger.info("Invalidated chatbot cache entries for user_id=%s count=%s", user_id, len(keys))
        except Exception as e:
            logger.error(f"Error invalidating user chatbot cache: {e}")

    def invalidate_contextual_cache(self, user_id: str):
        self.invalidate_user_cache(user_id)

    def get_context_hash(self, context: Dict[str, Any]) -> str:
        key_metrics = {
            "total_bills": context.get("total_bills", 0),
            "pending_bills": context.get("pending_bills", 0),
            "confirmed_bills": context.get("confirmed_bills", 0),
            "scheduled_bills": context.get("scheduled_bills", 0),
            "paid_bills": context.get("paid_bills", 0),
            "overdue_bills": context.get("overdue_bills", 0),
            "total_pending": round(float(context.get("total_pending", 0) or 0), 2),
            "total_paid": round(float(context.get("total_paid", 0) or 0), 2),
            "monthly_income": round(float(context.get("monthly_income", 0) or 0), 2),
            "monthly_expenses": round(float(context.get("monthly_expenses", 0) or 0), 2),
            "monthly_balance": round(float(context.get("monthly_balance", 0) or 0), 2),
            "current_month": context.get("current_month", ""),
            "last_financial_update": context.get("last_financial_update"),
            "categories": self._compact_categories(context.get("categories", {})),
            "next_bills": self._compact_bills(context.get("next_bills", [])),
            "overdue_details": self._compact_bills(context.get("overdue_details", [])),
        }
        context_str = json.dumps(key_metrics, sort_keys=True, default=str)
        return self._hash(context_str)[:24]

    def _compact_categories(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        compact = {}
        for category, data in sorted(categories.items())[:10]:
            compact[category] = {
                "total": round(float(data.get("total", 0) or 0), 2),
                "count": int(data.get("count", 0) or 0),
            }
        return compact

    def _compact_bills(self, bills: Any) -> Any:
        compact = []
        for bill in list(bills or [])[:10]:
            compact.append({
                "issuer": bill.get("issuer"),
                "amount": round(float(bill.get("amount", 0) or 0), 2),
                "due_date": bill.get("due_date"),
                "status": bill.get("status"),
                "category": bill.get("category"),
            })
        return compact


cache_service = CacheService()

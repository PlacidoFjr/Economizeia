from fnmatch import fnmatch

from app.services.cache_service import CacheService


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.ttls = {}

    def ping(self):
        return True

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value
        self.ttls[key] = ttl

    def keys(self, pattern):
        return [key for key in self.data if fnmatch(key, pattern)]

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
            self.ttls.pop(key, None)


def make_cache():
    cache = CacheService.__new__(CacheService)
    cache.enabled = True
    cache.redis_client = FakeRedis()
    cache.schema_version = "test"
    return cache


def test_normalize_message_removes_accents_and_duplicate_spaces():
    cache = make_cache()

    assert cache.normalize_message("  Olá,   VOCÊ  ") == "ola, voce"


def test_cache_key_is_isolated_by_user():
    cache = make_cache()

    key_a = cache._generate_cache_key("user-a", "quanto tenho pendente?")
    key_b = cache._generate_cache_key("user-b", "quanto tenho pendente?")

    assert key_a != key_b
    assert ":user-a:" in key_a
    assert ":user-b:" in key_b


def test_cache_hit_for_simple_message():
    cache = make_cache()

    cache.set_cached_response("user-a", "oi", "Ola!")

    assert cache.get_cached_response("user-a", "OI") == "Ola!"


def test_cache_miss_when_context_changes():
    cache = make_cache()

    context_a = cache.get_context_hash({"pending_bills": 1, "total_pending": 10})
    context_b = cache.get_context_hash({"pending_bills": 2, "total_pending": 20})
    cache.set_cached_response("user-a", "quanto tenho pendente?", "R$ 10", context_hash=context_a)

    assert cache.get_cached_response("user-a", "quanto tenho pendente?", context_hash=context_a) == "R$ 10"
    assert cache.get_cached_response("user-a", "quanto tenho pendente?", context_hash=context_b) is None


def test_invalidate_user_cache_removes_only_user_entries():
    cache = make_cache()

    cache.set_cached_response("user-a", "oi", "A")
    cache.set_cached_response("user-b", "oi", "B")
    cache.invalidate_user_cache("user-a")

    assert cache.get_cached_response("user-a", "oi") is None
    assert cache.get_cached_response("user-b", "oi") == "B"


def test_redis_unavailable_does_not_break_flow():
    cache = make_cache()
    cache.enabled = False
    cache.redis_client = None

    assert cache.get_cached_response("user-a", "oi") is None
    cache.set_cached_response("user-a", "oi", "Ola")
    cache.invalidate_user_cache("user-a")


def test_mutating_messages_are_not_cacheable():
    cache = make_cache()

    assert not cache.is_cacheable_message("gastei R$ 35 no Uber")
    assert not cache.is_cacheable_message("adicionar receita de R$ 2500 salario")
    assert cache.is_cacheable_message("como funciona o upload?", action="chat")
    assert cache.is_cacheable_message("quanto gastei esse mes", action="financial_summary")


def test_contextual_cache_uses_contextual_ttl():
    cache = make_cache()
    context_hash = cache.get_context_hash({"pending_bills": 1, "total_pending": 10})

    cache.set_cached_response("user-a", "pendentes?", "R$ 10", context_hash=context_hash, ttl=123)
    key = next(iter(cache.redis_client.ttls))

    assert cache.redis_client.ttls[key] == 123

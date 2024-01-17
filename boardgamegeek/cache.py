import requests
import requests_cache

from .exceptions import BGGValueError


class CacheBackend:
    pass


class CacheBackendNone(CacheBackend):
    def __init__(self):
        self.cache = requests.Session()


class CacheBackendMemory(CacheBackend):
    """Cache HTTP requests in memory"""

    def __init__(self, ttl):
        try:
            int(ttl)
        except ValueError:
            raise BGGValueError
        self.cache = requests_cache.CachedSession(
            backend="memory", expire_after=ttl, allowable_codes=(200,)
        )


class CacheBackendSqlite(CacheBackend):
    """Cache HTTP requests in a SQLite database"""

    def __init__(self, path, ttl, fast_save=True):
        try:
            int(ttl)
        except ValueError:
            raise BGGValueError

        self.cache = requests_cache.CachedSession(
            cache_name=path,
            backend="sqlite",
            expire_after=ttl,
            extension="",
            fast_save=fast_save,
            allowable_codes=(200,),
        )

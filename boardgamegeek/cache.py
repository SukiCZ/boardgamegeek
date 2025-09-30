from pathlib import Path

import requests
import requests_cache

from .exceptions import BGGValueError

StrOrPath = str | Path


class CacheBackend:
    """Base class for cache backends"""

    cache: requests.Session


class CacheBackendNone(CacheBackend):
    """Do not cache HTTP requests"""

    def __init__(self) -> None:
        self.cache = requests.Session()


class CacheBackendMemory(CacheBackend):
    """Cache HTTP requests in memory"""

    def __init__(self, ttl: int):
        try:
            int(ttl)
        except ValueError as e:
            raise BGGValueError from e
        self.cache = requests_cache.CachedSession(
            backend="memory",
            expire_after=ttl,
            allowable_codes=(200,),
        )


class CacheBackendSqlite(CacheBackend):
    """Cache HTTP requests in a SQLite database"""

    def __init__(self, path: StrOrPath, ttl: int, fast_save: bool = True):
        try:
            int(ttl)
        except ValueError as e:
            raise BGGValueError from e

        self.cache = requests_cache.CachedSession(
            cache_name=path,
            backend="sqlite",
            expire_after=ttl,
            extension="",
            fast_save=fast_save,
            allowable_codes=(200,),
        )

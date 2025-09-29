from __future__ import annotations

import logging
import warnings

from .api import BGGCommon
from .cache import CacheBackendMemory, CacheBackend
from .exceptions import BGGValueError
from .loaders import create_geeklist_from_xml, add_geeklist_items_from_xml
from .objects.geeklist import GeekList
from .utils import DEFAULT_REQUESTS_PER_MINUTE
from .utils import request_and_parse_xml

log = logging.getLogger("boardgamegeek.legacy_api")

API_ENDPOINT = "https://www.boardgamegeek.com/xmlapi"


class BGGClientLegacy(BGGCommon):
    def __init__(
        self,
        cache: CacheBackend = CacheBackendMemory(ttl=3600),
        timeout: float = 15,
        retries: int = 3,
        retry_delay: float = 5,
        disable_ssl: bool = False,  # deprecated, will be removed in future versions
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        access_token: str | None = None,
    ):
        if disable_ssl:
            warnings.warn("'disable_ssl' is deprecated, will be removed", DeprecationWarning, stacklevel=2)

        super().__init__(
            api_endpoint=API_ENDPOINT,
            cache=cache,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
            requests_per_minute=requests_per_minute,
            access_token=access_token,
        )
        self._geeklist_api_url = API_ENDPOINT + "/geeklist"

    def geeklist(self, listid: int, comments: bool = False) -> GeekList:
        # Parameter validation
        if not listid:
            raise BGGValueError("List Id must be specified")
        log.debug(f"retrieving list {listid}")

        params = {}
        if comments:
            params["comments"] = 1
        url = f"{self._geeklist_api_url}/{listid}"
        xml_root = request_and_parse_xml(
            self.requests_session,
            url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
            headers=self._get_auth_headers(),
        )

        lst = create_geeklist_from_xml(xml_root, listid)
        add_geeklist_items_from_xml(lst, xml_root)

        return lst

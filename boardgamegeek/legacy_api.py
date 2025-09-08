import logging

from .api import BGGCommon
from .api import CacheBackendMemory
from .api import DEFAULT_REQUESTS_PER_MINUTE
from .api import BGGValueError
from .api import request_and_parse_xml
from .loaders import create_geeklist_from_xml, add_geeklist_items_from_xml

log = logging.getLogger("boardgamegeek.legacy_api")

API_ENDPOINT = "https://www.boardgamegeek.com/xmlapi"


class BGGClientLegacy(BGGCommon):
    def __init__(
        self,
        cache=CacheBackendMemory(ttl=3600),
        timeout=15,
        retries=3,
        retry_delay=5,
        disable_ssl=False,
        requests_per_minute=DEFAULT_REQUESTS_PER_MINUTE,
        access_token=None,
    ):
        super().__init__(
            api_endpoint=API_ENDPOINT,
            cache=cache,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
            requests_per_minute=requests_per_minute,
            access_token=access_token,
        )
        self._search_api_url = None
        self._thing_api_url = None
        self._guild_api_url = None
        self._user_api_url = None
        self._plays_api_url = None
        self._hot_api_url = None
        self._collection_api_url = None
        self._geeklist_api_url = API_ENDPOINT + "/geeklist"

    def geeklist(self, listid, comments=False):
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

"""
:mod:`boardgamegeek.utils` - Generic helper functions
=====================================================

.. module:: boardgamegeek.utils
   :platform: Unix, Windows
   :synopsis: generic helper functions

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""
import datetime
import html
import logging
import threading
import time
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError as ETParseError

import requests
from requests.adapters import HTTPAdapter

from .exceptions import BGGApiError, BGGApiRetryError, BGGApiTimeoutError

html_unescape = html.unescape


log = logging.getLogger("boardgamegeek.utils")

DEFAULT_REQUESTS_PER_MINUTE = 30


class RateLimitingAdapter(HTTPAdapter):
    """
    Adapter for the Requests library which makes sure there's a delay between consecutive requests to the BGG site
    so that we don't get throttled
    """

    __last_request_timestamp = None  # time when the last request was made
    __time_between_requests = (
        0  # interval to wait between requests in order to match the expected number of
    )
    # requests per second

    __rate_limit_lock = threading.Lock()

    def __init__(self, rpm=DEFAULT_REQUESTS_PER_MINUTE, **kw):
        """

        :param rpm: how many requests per minute to allow
        :param kw:
        :return:
        """
        if rpm <= 0:
            log.warning(
                f"invalid requests per minute value ({rpm}), falling back to default"
            )
            rpm = DEFAULT_REQUESTS_PER_MINUTE

        RateLimitingAdapter.__time_between_requests = 60.0 / float(rpm)

        super().__init__(**kw)

    def send(self, request, **kw):
        log.debug("acquiring rate limiting lock")
        with RateLimitingAdapter.__rate_limit_lock:
            log.debug(
                "time between requests:{}, last request timestamp: {}".format(
                    RateLimitingAdapter.__time_between_requests,
                    RateLimitingAdapter.__last_request_timestamp,
                )
            )

            # determine if we need to sleep in order to enforce the maximum requested amount of requests per minute
            if RateLimitingAdapter.__last_request_timestamp is not None:
                time_delta = time.time() - RateLimitingAdapter.__last_request_timestamp
                need_to_wait = RateLimitingAdapter.__time_between_requests - time_delta

                log.debug(
                    f"time since last request: {time_delta}, need to wait: {need_to_wait}"
                )

                if need_to_wait > 0:
                    time.sleep(need_to_wait)

            RateLimitingAdapter.__last_request_timestamp = time.time()
            log.debug("releasing rate limiting lock")

        log.debug(f"sending request: {request}")
        return super().send(request, **kw)


class DictObject:
    """
    Just a fancy wrapper over a dictionary
    """

    def __init__(self, data):
        self._data = data

    def __getattr__(self, item):
        # allow accessing user's variables using .attribute
        try:
            return self._data[item]
        except Exception:
            # TODO Too broad?
            raise AttributeError

    # TODO: remove this ? Turn to property ?
    def data(self):
        """
        Access to the internal data dictionary, for easy dumping
        :return: the internal data dictionary
        """
        return self._data


def xml_subelement_attr_by_attr(
    xml_elem,
    subelement,
    filter_attr,
    filter_value,
    convert=None,
    attribute="value",
    default=None,
    quiet=False,
):
    """
    Search for a sub-element having an attribute ``filter_attr`` set to ``filter_value``

    For the following XML document:

    .. code-block:: xml

        <xml_elem>
            <subelement filter="this" value="THIS" />
        </xml_elem>

    a call to ``xml_subelement_attr(xml_elem, "subelement", "filter", "this")`` would return ``"THIS"``


    :param xml_elem: search the children nodes of this element
    :param subelement: Name of the sub-element to search for
    :param filter_attr: Name of the attribute the sub-element must contain
    :param filter_value: Value of the attribute
    :param convert: if not None, a callable to perform the conversion of this attribute to a certain object type
    :param attribute: name of the attribute to get
    :param default: default value if the subelement or attribute is not found
    :param quiet: if True, don't raise exception from conversions, return default instead
    :return: value of the attribute or ``None`` in error cases

    """
    if xml_elem is None or not subelement:
        return None

    for subel in xml_elem.findall(f'.//{subelement}[@{filter_attr}="{filter_value}"]'):
        value = subel.attrib.get(attribute)
        if value is None:
            value = default
        elif convert:
            try:
                value = convert(value)
            except Exception as e:
                if quiet:
                    value = default
                else:
                    raise e
        return value
    return default


def xml_subelement_attr(
    xml_elem, subelement, convert=None, attribute="value", default=None, quiet=False
):
    """
    Search for a sub-element and return the value of its attribute.

    For the following XML document:

    .. code-block:: xml

        <xml_elem>
            <subelement value="THIS" />
        </xml_elem>

    a call to ``xml_subelement_attr(xml_elem, "subelement")`` would return ``"THIS"``


    :param xml_elem: search the children nodes of this element
    :param subelement: Name of the sub-element to search for
    :param convert: if not None, a callable to perform the conversion of this attribute to a certain object type
    :param attribute: name of the attribute to get
    :param default: default value if the subelement or attribute is not found
    :param quiet: if True, don't raise exception from conversions, return default instead
    :return: value of the attribute or ``None`` in error cases

    """
    if xml_elem is None or not subelement:
        return None

    subel = xml_elem.find(subelement)
    if subel is None:
        value = default
    else:
        value = subel.attrib.get(attribute)
        if value is None:
            value = default
        elif convert:
            try:
                value = convert(value)
            except Exception as e:
                if quiet:
                    value = default
                else:
                    raise e
    return value


def xml_subelement_attr_list(
    xml_elem, subelement, convert=None, attribute="value", default=None, quiet=False
):
    """
    Search for sub-elements and return a list of the specified attribute.

    .. code-block:: xml

        <xml_elem>
            <subelement value="THIS" />
            <subelement value="THIS2" />
            ...
        </xml_elem>

    For the above document, ["THIS", "THIS2"] will be returned

    :param xml_elem: search the children nodes of this element
    :param subelement: name of the sub-element to search for
    :param convert: if not None, a callable used to perform the conversion of this attribute to a certain object type
    :param attribute: name of the attribute to get
    :param default: default value to use if an attribute is missing
    :param quiet: if True, don't raise exceptions from conversions, instead use the default value
    :return: list containing the values of the attributes or ``None`` in error cases
    """
    if xml_elem is None or not subelement:
        return None

    subel = xml_elem.findall(subelement)
    res = []
    for e in subel:
        value = e.attrib.get(attribute)
        if value is None:
            value = default
        elif convert:
            try:
                value = convert(value)
            except Exception as e:
                if quiet:
                    value = default
                else:
                    raise e
        res.append(value)

    return res


def xml_subelement_text(xml_elem, subelement, convert=None, default=None, quiet=False):
    """
    Return the text of the specified subelement

    For the document below:

    .. code-block:: xml

        <xml_elem>
            <subelement>text</subelement>
        </xml_elem>

    ``"text"`` will be returned

    :param xml_elem: search the children nodes of this element
    :param subelement: name of the subelement whose text will be retrieved
    :param convert: if not None, a callable used to perform the conversion of the text to a certain object type
    :param default: default value if subelement is not found
    :param quiet: if True, don't raise exceptions from conversions, instead use the default value
    :return: The text associated with the sub-element or ``None`` in case of error
    """
    if xml_elem is None or not subelement:
        return None

    subel = xml_elem.find(subelement)
    if subel is None:
        text = default
    else:
        text = subel.text
        if text is None:
            text = default
        elif convert:
            try:
                text = convert(text)
            except Exception as e:
                if quiet:
                    text = default
                else:
                    raise e
    return text


def request_and_parse_xml(
    requests_session, url, params=None, timeout=15, retries=3, retry_delay=5
):
    """
    Downloads an XML from the specified url, parses it and returns the xml ElementTree.

    :param requests_session: A Session of the ``requests`` library, used to fetch the url
    :param url: the address where to get the XML from
    :param params: dictionary containing the parameters which should be sent with the request
    :param timeout: number of seconds after which the request times out
    :param retries: number of retries to perform in case of timeout
    :param retry_delay: the amount of seconds to sleep when retrying an API call that returned 202
    :return: :py:func:`xml.etree.ElementTree` corresponding to the XML
    :raises: :py:class:`BGGApiRetryError` if this request should be retried after a short delay
    :raises: :py:class:`BGGApiError` if the response was invalid or couldn't be parsed
    :raises: :py:class:`BGGApiTimeoutError` if there was a timeout
    """

    retr = retries

    # retry loop
    while retr >= 0:
        retr -= 1
        try:
            r = requests_session.get(url, params=params, timeout=timeout)

            if r.status_code == 202:
                if retries == 0:
                    # no retries have been requested, therefore raise exception to signal the application that it
                    # needs to retry
                    # (BoardGameGeek API says that on status code 202 the call should be retried after a delay)
                    raise BGGApiRetryError
                elif retr == 0:
                    # retries were requested, but we reached 0. Signal the application that it needs to retry itself.
                    raise BGGApiRetryError(
                        f"failed to retrieve data after {retries} retries"
                    )
                else:
                    # sleep for the specified delay and retry
                    log.debug(
                        f"API call will be retried in {retry_delay} seconds ({retr} more retries)"
                    )
                    if retr >= 0:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                    continue
            elif r.status_code == 503:
                # it seems they added some sort of protection which triggers when too many requests are made, in which
                # case we get back a 503. Try to delay and retry
                log.warning("API returned 503, retrying")
                if retr >= 0:
                    time.sleep(retry_delay)
                    retry_delay *= 3
                continue

            if not r.headers.get("content-type").lower().startswith("text/xml"):
                raise BGGApiError("non-XML reply")

            xml = r.text

            root_elem = ET.fromstring(xml)

            return root_elem

        except requests.exceptions.Timeout:
            if retries == 0:
                raise BGGApiTimeoutError
            elif retr == 0:
                # ... reached 0 retries
                raise BGGApiTimeoutError(
                    f"failed to retrieve data after {retries} retries"
                )
            else:
                log.debug(
                    f"API request timeout, retrying {retr} more times w/timeout {timeout}"
                )
                timeout *= 2.5
                continue

        except ETParseError as e:
            raise BGGApiError(f"error decoding BGG API response: {e}")

        except (BGGApiRetryError, BGGApiTimeoutError):
            raise

        except Exception as e:
            raise BGGApiError(f"error fetching BGG API response: {e}")

    raise BGGApiError("couldn't fetch data within the configured number of retries")


def fix_url(url):
    """
    The BGG API started returning URLs like //cf.geekdo-images.com/images/pic55406.jpg for thumbnails and images.
    This function fixes them.

    :param url: the url to fix
    :return: the fixed url
    """
    if url and url.startswith("//"):
        url = f"http:{url}"
    return url


def fix_unsigned_negative(value):
    # the BGG api seems to return negative years cast to unsigned ints (32 bit) in search results. This function
    # fixes the values so that they're negative again.
    if value > 0x7FFFFFFF:
        value -= 0x100000000
    return value


def get_board_game_version_from_element(xml_elem):
    data = {
        "id": int(xml_elem.attrib["id"]),
        "yearpublished": fix_unsigned_negative(
            xml_subelement_attr(
                xml_elem, "yearpublished", convert=int, default=0, quiet=True
            )
        ),
        "language": xml_subelement_attr_by_attr(xml_elem, "link", "type", "language"),
        "publisher": xml_subelement_attr_by_attr(
            xml_elem, "link", "type", "boardgamepublisher"
        ),
        "artist": xml_subelement_attr_by_attr(
            xml_elem, "link", "type", "boardgameartist"
        ),
        "thumbnail": xml_subelement_text(xml_elem, "thumbnail"),
        "image": xml_subelement_text(xml_elem, "image"),
        "name": xml_subelement_attr(xml_elem, "name"),
        "product_code": xml_subelement_attr(xml_elem, "productcode"),
    }

    for item in ["width", "length", "depth", "weight"]:
        data[item] = xml_subelement_attr(
            xml_elem, item, convert=float, quiet=True, default=0.0
        )

    return data


def get_marketplace_listing_from_element(xml_elem):
    try:
        list_date_string = xml_subelement_attr(xml_elem, "listdate")
        list_date = datetime.datetime.strptime(
            list_date_string, "%a, %d %b %Y %H:%M:%S %z"
        )
    except ValueError:
        list_date = None

    data = {
        "list_date": list_date,
        "price": xml_subelement_attr(xml_elem, "price", convert=float, default=0.0),
        "currency": xml_subelement_attr(xml_elem, "price", attribute="currency"),
        "condition": xml_subelement_attr(xml_elem, "condition"),
        "notes": xml_subelement_attr(xml_elem, "notes"),
        "link": xml_subelement_attr(xml_elem, "link", attribute="href"),
    }

    return data

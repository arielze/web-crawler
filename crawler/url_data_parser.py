from typing import Set
from html.parser import HTMLParser
from urllib.parse import urljoin
from crawler.common import filter_protocols


class URLDataParser(HTMLParser):
    """Simple and minimalistic anchor links extractor."""

    def __init__(self, url: str):
        self.base_url = url
        self.links: Set[dict] = set()
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, link_url in attrs:
                if attr == "href":
                    if filter_protocols(link_url, True):
                        link_url = urljoin(self.base_url, link_url)
                        self.links.add(link_url)

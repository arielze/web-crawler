from urllib.parse import urlparse


class CrawlerError(Exception):
    pass


def filter_protocols(url: str, allow_no_protocol: bool) -> bool:
    url_parts = urlparse(url)
    if url_parts.scheme:
        return url_parts.scheme in ["http", "https"]
    else:
        return allow_no_protocol

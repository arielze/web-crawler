from typing import Any
from queue import Queue, Empty
from urllib.parse import urlparse
from threading import Lock
from crawler.common import CrawlerError, filter_protocols


EmptyQueue = Empty


def url_key(url: str) -> str:
    """Generates key for the ignoring URL fragments and scheme"""
    url_parts = urlparse(url)
    path = url_parts.path[:-1] if url_parts.path.endswith('/') else url_parts.path
    return f"{url_parts.netloc}/{path}/{url_parts.query}"


lock = Lock()


class URLsManager:
    """Class for managing all persistent data, and crawling tasks distribution.

        in a distributed solution the class functionality should be backed-up by a real queue server and a database.
        good alternatives can be:
        - queue: RabbitMQ
        - database: I was thinking of Redis which support atomic actions that can help managing duplicate runs of same
          URL, any other key/value might be a good choice although, we should take in account solving duplicate run of
          URLs.
    """
    def __init__(self):
        self.urls = {}
        self.queue: Queue = Queue()

    def save_url(self, url: str, status: int, score: float, depth: int, message: str = ''):
        if not filter_protocols(url, False):
            raise CrawlerError(f"Un supported protocol for url {url}")

        ukey = url_key(url)
        self.urls[ukey] = {
            'url': url,
            'status': status,
            'score': score,
            'depth': depth,
            'message': message
        }

    def enqueue_url(self, url: str, depth: int) -> bool:
        if not filter_protocols(url, False):
            raise CrawlerError(f"Un supported protocol for url {url}")

        ukey = url_key(url)
        with lock:
            if ukey not in self.urls:
                self.urls[ukey] = None
                self.queue.put({'url': url, 'depth': depth})
                return True
        return False

    def get_next_url(self, timeout: int = 10) -> Any:
        return self.queue.get(timeout=timeout)

    def print_urls(self):
        print("URL\tdepth\tscore")
        count_good_urls = 0
        for url, urls_data in self.urls.items():
            if urls_data['status'] < 400:
                count_good_urls += 1
                print(f"{urls_data['url']}\t{urls_data['depth']}\t{urls_data['score']}")
        print(f"Total links crawled: {count_good_urls}")

    def print_errors(self):
        errors = [
            urls_data for url, urls_data in self.urls.items()
            if urls_data['status'] >= 400
        ]
        count_urls = len(errors)

        if count_urls > 0:
            print("\n\nErrors report")
            print("URL\tstatus code\terror message")
            for urls_data in errors:
                print(f"{urls_data['url']}\t{urls_data['status']}\t{urls_data['message']}")
            print(f"Total errors crawled: {count_urls} of {len(self.urls)} links")
            print("* error code 1000 are connection errors")
            print("* error code 2000 are crawler errors")
            print("* error code 3000 are general errors")
        else:
            print("No errors found")

    def queue_empty(self):
        return self.queue.empty()

import sys
import requests
from requests.exceptions import RequestException, HTTPError
from typing import List, Any, Tuple, Set
from queue import Queue
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class URLsManager:
    '''Class for managin al persistant data, and crawling tasks distribution

        in a distributed solution the class functionality should be backed-up by a real queue server and a database.
        good alternatives can be:
        - queue: RabbitMQ
        - database: I was thinking of Redis which support atomic cations that can help managing duplicate runs of same
          URL, any other key/value might be a good choice although, we should take in account solving duplicate run of
          URLs.
    '''
    def __init__(self):
        self.urls = {}
        self.queue: Queue = Queue()

    def save_url(self, url: str, status: int, score: float, depth: int, message: str = ''):
        url_key = self.url_key(url)
        self.urls[url_key] = {
            'url': url,
            'status': status,
            'score': score,
            'depth': depth,
            'message': message
        }

    def url_key(self, url: str) -> str:
        '''Generates key for the ignoring URL fragments and scheme'''
        url_parts = urlparse(url)
        return f"{url_parts.hostname}/{url_parts.path}/{url_parts.query}"

    def enqueue_url(self, url: str, depth: int):
        url_key = self.url_key(url)
        if url_key not in self.urls:
            self.urls[url_key] = None
            self.queue.put({'url': url, 'depth': depth})

    def get_next_url(self) -> Any:
        return self.queue.get()

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
        else:
            print("No errors founs")

    def queue_empty(self):
        return self.queue.empty()


class URLDataParser(HTMLParser):
    '''Simple and minimalistic anchor links extractor'''

    def __init__(self, url: str):
        self.base_url = url
        self.links: Set[dict] = set()
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, link_url in attrs:
                if attr == "href":
                    # this does not handle cases where the href point to an email, phone number,
                    # script or any non url target
                    link_url = urljoin(self.base_url, link_url)

                    if urlparse(link_url).scheme in ["http", "https"]:
                        self.links.add(link_url)


class Crawler:
    '''Main crawler class, instantiate in a stateless object that execute the crawling.'''

    def __init__(self, urls_manager: URLsManager, base_url: str, max_depth: int):
        url_parts = urlparse(base_url)
        if not url_parts.scheme:
            base_url = u"http://{base_url}".format(base_url=base_url)
        self.urls_manager = urls_manager
        self.base_url = base_url
        self.max_depth = max_depth

    def get_links(self, url: str, data: str) -> List:
        parser = URLDataParser(url)
        parser.feed(data)
        return list(parser.links)

    def calculate_score(self, urls: List) -> float:
        # if no links in page score is 0
        if not urls:
            return 0
        base_host = urlparse(self.base_url).hostname
        inner_urls = [url for url in urls if urlparse(url).hostname == base_host]
        return len(inner_urls) / len(urls)

    def crawl(self, url: str, current_depth: int = 0):
        current_depth += 1
        if current_depth > self.max_depth:
            return
        try:
            res = requests.get(url)
            res.raise_for_status()
            urls = self.get_links(url, res.text)
            score = self.calculate_score(urls)

            # don't need to enqueue next level links if they'll reach max_depth
            if current_depth + 1 <= self.max_depth:
                for link_url in urls:
                    self.urls_manager.enqueue_url(link_url, current_depth)

            self.urls_manager.save_url(url, res.status_code, score, current_depth)
        except HTTPError:
            self.urls_manager.save_url(url, res.status_code, 0, current_depth)
        except RequestException as e:
            self.urls_manager.save_url(url, 1000, 0, current_depth, str(e))
        except Exception as e:
            self.urls_manager.save_url(url, 2000, 0, current_depth, str(e))

    def do_crawl(self, print_errors: bool = False):
        self.urls_manager.enqueue_url(self.base_url, 0)
        while not self.urls_manager.queue_empty():
            task = self.urls_manager.get_next_url()
            self.crawl(task['url'], task['depth'])

        self.urls_manager.print_urls()
        if print_errors:
            self.urls_manager.print_errors()


usage = """
Running site crawler:
python web_crawler.py site_url max_depth [options]

arguments:
    site_url - root URL as strting point of the crawler, must be a valid URL
    max_depth - integer larger than 0

opthins:
    --report-errors - reports erroneuse links

example: python web_crawler.py https://www.example.com/ 2
"""


def parse_args() -> Tuple:

    try:
        if len(sys.argv) < 3 or len(sys.argv) > 5:
            print(usage)
        base_url = sys.argv[1]
        max_depth = max(int(sys.argv[2]), 1)
        print_errors = len(sys.argv) == 4 and sys.argv[3] == '--report-errors'
        return base_url, max_depth, print_errors
    except Exception as e:
        print("Error:", str(e))
        print(usage)
        exit(1)


if __name__ == "__main__":

    base_url, max_depth, print_errors = parse_args()
    urls_manager = URLsManager()
    crawler = Crawler(urls_manager, base_url, max_depth)
    crawler.do_crawl(print_errors)

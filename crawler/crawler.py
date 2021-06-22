import requests
from requests.exceptions import RequestException, HTTPError
from typing import List
from urllib.parse import urlparse
from crawler.url_data_parser import URLDataParser
from crawler.urls_manager import URLsManager, EmptyQueue
from crawler.common import CrawlerError


class Crawler:
    """Crawler worker class.

    Stateless object that reads crawling tasks from queue and execute them,
    should be easily adopt to run in a distributed manner.
    """

    def __init__(self, urls_manager: URLsManager, base_url: str, max_depth: int):
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
        base_host = urlparse(self.base_url).netloc
        inner_urls = [url for url in urls if urlparse(url).netloc == base_host]
        return len(inner_urls) / len(urls)

    def enqueue_urls(self, urls: List[str], current_depth: int):
        # don't need to enqueue next level links if they'll reach max_depth
        if current_depth + 1 <= self.max_depth:
            for link_url in urls:
                self.urls_manager.enqueue_url(link_url, current_depth)

    def crawl(self, url: str, current_depth: int = 0):
        current_depth += 1
        if current_depth > self.max_depth:
            return
        try:
            res = requests.get(url)
            res.raise_for_status()
            urls = self.get_links(url, res.text)
            score = self.calculate_score(urls)
            self.enqueue_urls(urls, current_depth)
            self.urls_manager.save_url(url, res.status_code, score, current_depth)
        except HTTPError:
            self.urls_manager.save_url(url, res.status_code, 0, current_depth)
        except RequestException as e:
            self.urls_manager.save_url(url, 1000, 0, current_depth, str(e))
        except CrawlerError as e:
            self.urls_manager.save_url(url, 2000, 0, current_depth, str(e))
        except Exception as e:
            self.urls_manager.save_url(url, 3000, 0, current_depth, str(e))
        print('+', end='')

    def do_crawl(self):
        while True:
            try:
                task = self.urls_manager.get_next_url(timeout=1)
            except EmptyQueue:
                break
            self.crawl(task['url'], task['depth'])


def run_crawler(urls_manager: URLsManager, base_url: str, max_depth: int):
    crawler = Crawler(urls_manager, base_url, max_depth)
    crawler.do_crawl()

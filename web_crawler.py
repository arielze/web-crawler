import sys
import time
from threading import Thread
from typing import Tuple, List
from urllib.parse import urlparse
from crawler.crawler import run_crawler
from crawler.urls_manager import URLsManager


usage = """
Running site crawler:
python web_crawler.py site_url max_depth [options]

arguments:
    site_url - root URL as strting point of the crawler, must be a valid URL
    max_depth - integer larger than 0

opthins:
    --report-errors - reports erroneuse links
    --threaded - for running in multithreaded (10 threads)

example: python web_crawler.py https://www.example.com/ 2
"""


def parse_args(argv) -> Tuple:

    try:
        if len(argv) < 3 or len(argv) > 5:
            print(usage)
        base_url = argv[1]
        max_depth = max(int(argv[2]), 1)
        report_errors = '--report-errors' in argv
        threaded = '--threaded' in argv
        return base_url, max_depth, report_errors, threaded
    except Exception as e:
        print("Error:", str(e))
        print(usage)
        exit(1)


def prepare_base_url(base_url: str) -> str:

    url_parts = urlparse(base_url)
    if not url_parts.scheme:
        base_url = u"http://{base_url}".format(base_url=base_url)
    return base_url


def main(argv: List):
    base_url, max_depth, print_errors, threaded = parse_args(argv)
    base_url = prepare_base_url(base_url)
    urls_manager = URLsManager()
    urls_manager.enqueue_url(base_url, 0)
    if threaded:
        num_threads = 10
        print("Running in multithreaded")

        threads = [
            Thread(
                target=run_crawler,
                args=(urls_manager, base_url, max_depth)
            ) for _ in range(num_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
    else:
        print("Running in single thread")
        run_crawler(urls_manager, base_url, max_depth)

    urls_manager.print_urls()
    if print_errors:
        urls_manager.print_errors()


if __name__ == "__main__":
    st = time.time()
    main(sys.argv)
    print("execution time:", time.time() - st)

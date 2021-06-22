import pytest
from typing import List
from crawler.crawler import Crawler
from crawler.common import CrawlerError
from web_crawler import parse_args, prepare_base_url
from crawler.url_data_parser import URLDataParser
from crawler.urls_manager import URLsManager, url_key


# parse args
def test_parse_args():
    res = parse_args(["web_crauler.py", "blabla.com", 9])
    assert res == ("blabla.com", 9, False, False)


def test_parse_args_with_errors_report():
    res = parse_args(["web_crauler.py", "blabla.com", 9, "--report-errors", "--threaded"])
    assert res == ("blabla.com", 9, True, True)


def test_parse_args_with_zero_depth():
    res = parse_args(["web_crauler.py", "blabla.com", 0, "--report-errors"])
    assert res == ("blabla.com", 1, True, False)


def test_parse_args_with_negative_depth():
    res = parse_args(["web_crauler.py", "blabla.com", -2, "--report-errors", "--threaded"])
    assert res == ("blabla.com", 1, True, True)


# URLDataParser
def test_single_link():
    data = '<a href="http://www.google.com">google</a>'
    url = "https://www.google.com"
    parser = URLDataParser(url)
    parser.feed(data)
    assert parser.links == {"http://www.google.com"}


def test_multi_link():
    data = """<a href="http://www.google.com">google</a>
    <a href="http://www.firefox.com">firefox</a>
    <a href="http://www.yahoo.com">yahoo</a>
    <a href="/mylink">my inner link</a>
    <a href="his-link">his inner link</a>
    <a href="#anchor">an anchor</a>
    """
    url = "https://www.stam.com/page1"
    parser = URLDataParser(url)
    parser.feed(data)
    expected_links = [
        "http://www.firefox.com",
        "http://www.google.com",
        "http://www.yahoo.com",
        "https://www.stam.com/page1#anchor",
        "https://www.stam.com/page1/his-link ",
        "https://www.stam.com/page1/mylink",
    ].sort()
    assert list(parser.links).sort() == expected_links


def test_un_supported_protocols_link():
    data = """<a href="http://www.google.com">google</a>
    <a href="mailto:ariel@me.com">email</a>
    <a href="tel:+97299999999">phone</a>
    <a href="file://some_file.txt">fille</a>
    <a href="ftp://www.google.com">ftp</a>
    <a href="#anchor">an anchor</a>
    """
    url = "https://www.stam.com/page1"
    parser = URLDataParser(url)
    parser.feed(data)
    expected_links = [
        "http://www.google.com",
        "https://www.stam.com/page1#anchor",
    ].sort()
    assert list(parser.links).sort() == expected_links


def test_broken_document():
    data = """<html><body> <a href="http://www.google.com>google
    """
    url = "https://www.stam.com/page1"
    parser = URLDataParser(url)
    parser.feed(data)
    assert list(parser.links).sort() is None


def test_for_non_html_document():
    data = """Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium
    doloremque laudantium, totam rem aperiam eaque ipsa, quae ab illo inventore veritatis
    et quasi architecto beatae vitae dicta sunt, explicabo. Nemo enim ipsam voluptatem,
    quia voluptas sit, aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos,
    qui ratione voluptatem sequi nesciunt, neque porro quisquam est, qui dolorem ipsum,
    quia dolor sit, amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt,
    ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam,
    quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?
    Quis autem vel eum iure reprehenderit, qui in ea voluptate velit esse, quam nihil molestiae consequatur,
    vel illum, qui dolorem eum fugiat, quo voluptas nulla pariatur?
    """
    url = "https://www.stam.com/page1"
    parser = URLDataParser(url)
    parser.feed(data)
    assert list(parser.links).sort() is None


# URLsManager
def test_save_url():
    urls_manager = URLsManager()
    url = 'http://stam.com'
    urls_manager.save_url(url, 200, 0.23, 1, 'message a')
    expected_links = {
        'stam.com//': {'url': url, 'status': 200, 'score': 0.23, 'depth': 1, 'message': 'message a'}
    }
    assert urls_manager.urls == expected_links


def test_un_supported_protocol_save_url():
    urls_manager = URLsManager()
    url = 'ftp://stam.com'
    with pytest.raises(CrawlerError) as error:
        urls_manager.save_url(url, 200, 0.23, 1, 'message a')
    expected_message = f"Un supported protocol for url {url}"
    assert str(error.value) == expected_message


def test_enqueue_url():
    urls_manager = URLsManager()
    url = 'http://stam.com'
    urls_manager.enqueue_url(url, 1)
    expected = {'url': url, 'depth': 1}
    assert urls_manager.get_next_url() == expected
    expected_links = {
        'stam.com//': None
    }
    assert urls_manager.urls == expected_links


def test_un_supported_protocol_enqueue_url():
    urls_manager = URLsManager()
    url = 'ftp://stam.com'
    with pytest.raises(CrawlerError) as error:
        urls_manager.enqueue_url(url, 1)
    expected_message = f"Un supported protocol for url {url}"
    assert str(error.value) == expected_message


def test_cannot_enqueue_twice_same_url():
    urls_manager = URLsManager()
    url = 'http://stam.com'
    firs = urls_manager.enqueue_url(url, 1)
    second = urls_manager.enqueue_url(url, 1)
    assert firs
    assert second is False
    expected = {'url': url, 'depth': 1}
    assert urls_manager.get_next_url() == expected
    assert urls_manager.queue_empty()
    expected_links = {
        'stam.com//': None
    }
    assert urls_manager.urls == expected_links


urls_keys_test: List[tuple] = [
    ('http://stam.com/', 'stam.com//'),
    ('http://stam.com', 'stam.com//'),
    ('https://stam.com/', 'stam.com//'),
    ('http://www.stam.com', 'www.stam.com//'),
    ('http://www.stam.com/page1/page2', 'www.stam.com//page1/page2/'),
    ('http://www.stam.com/page1/page2/', 'www.stam.com//page1/page2/'),
    ('http://www.stam.com/page1/page2#anc', 'www.stam.com//page1/page2/'),
    ('http://www.stam.com/page1/page2/#anc', 'www.stam.com//page1/page2/'),
    ('http://www.stam.com/page1/page2?a=1&b=2', 'www.stam.com//page1/page2/a=1&b=2'),
    ('http://www.stam.com/page1/page2/?a=1&b=2', 'www.stam.com//page1/page2/a=1&b=2'),
    ('http://www.stam.com/page1/page2?a=1&b=2#anc', 'www.stam.com//page1/page2/a=1&b=2'),
]


@pytest.mark.parametrize("url,key", urls_keys_test)
def test_url_key(url, key):
    assert url_key(url) == key


urls_in_test: List[tuple] = [
    ('http://stam.com/', 'http://stam.com/'),
    ('http://stam.com', 'http://stam.com'),
    ('https://stam.com/', 'https://stam.com/'),
    ('http://www.stam.com', 'http://www.stam.com'),
    ('www.stam.com', 'http://www.stam.com'),
    ('www.stam.com/', 'http://www.stam.com/'),
    ('stam.com', 'http://stam.com'),
]


@pytest.mark.parametrize("url_in,url_out", urls_in_test)
def test_prepare_base_url(url_in, url_out):
    assert prepare_base_url(url_in) == url_out


# Crawler
def test_dont_scan_if_max_depth_reached(mocker):
    m_request = mocker.patch('requests.get')
    crawler = Crawler(URLsManager(), 'http://base_url.com', 3)
    crawler.crawl('http://base_url.com/page1', 4)
    m_request.assert_not_called()


scores_test: List[tuple] = [
    ('https://www.stam.com/', 0.5),
    ('http://www.stam.com/', 0.5),
    ('https://www.stam.com', 0.5),
    ('http://www.stam.com', 0.5),
    ('https://www.yahoo.com/', 1 / 6),
    ('https://www.other.com/', 0),
]


@pytest.mark.parametrize("base_url,score", scores_test)
def test_page_score(base_url, score):
    urls: List[str] = [
        "http://www.firefox.com",
        "http://www.google.com",
        "http://www.yahoo.com",
        "https://www.stam.com/page1#anchor",
        "https://www.stam.com/page1/his-link ",
        "https://www.stam.com/page1/mylink",
    ]

    crawler = Crawler(URLsManager(), base_url, 3)
    assert crawler.calculate_score(urls) == score


def test_no_urls_score_0():
    urls: List[str] = []
    base_url = 'http://stam.com'
    crawler = Crawler(URLsManager(), base_url, 3)
    assert crawler.calculate_score(urls) == 0


def test_urls_not_enqueued_when_next_depth_reach_max_depth(mocker):
    m_enqueue = mocker.patch.object(URLsManager, "enqueue_url")
    urls: List[str] = [
        "http://www.firefox.com",
        "http://www.google.com",
        "http://www.yahoo.com",
        "https://www.stam.com/page1#anchor",
        "https://www.stam.com/page1/his-link ",
        "https://www.stam.com/page1/mylink",
    ]
    base_url = 'http://stam.com'
    crawler = Crawler(URLsManager(), base_url, 3)
    crawler.enqueue_urls(urls, 3)
    m_enqueue.assert_not_called()


def test_crawler_urls_enqueue(mocker):
    m_enqueue = mocker.patch.object(URLsManager, "enqueue_url")
    urls: List[str] = [
        "http://www.firefox.com",
        "http://www.google.com",
        "http://www.yahoo.com",
        "https://www.stam.com/page1#anchor",
        "https://www.stam.com/page1/his-link ",
        "https://www.stam.com/page1/mylink",
    ]
    calls = [mocker.call(url, 2) for url in urls]
    base_url = 'http://stam.com'
    crawler = Crawler(URLsManager(), base_url, 3)
    crawler.enqueue_urls(urls, 2)
    m_enqueue.assert_has_calls(calls)


def test_crawl(mocker):
    m_enqueue = mocker.patch.object(URLsManager, "enqueue_url")
    m_save = mocker.patch.object(URLsManager, "save_url")
    data = """<a href="http://www.google.com">google</a>
    <a href="http://www.firefox.com">firefox</a>
    <a href="http://www.yahoo.com">yahoo</a>
    <a href="/mylink">my inner link</a>
    <a href="his-link">his inner link</a>
    <a href="#anchor">an anchor</a>
    """
    respons = mocker.Mock(text=data, status_code=200, raise_for_status=lambda: True)
    mocker.patch("requests.get", return_value=respons)

    base_url = "https://www.stam.com"
    url = "https://www.stam.com/page1"
    crawler = Crawler(URLsManager(), base_url, 3)
    crawler.crawl(url, 1)
    m_enqueue.assert_called()
    m_save.assert_called_once_with(url, 200, 0.5, 2)

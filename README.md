# Sample Web Crawler
Web crawler, for traversing web page links till reaching a maximum depth. Each page is registered with it score of links refering to the start domain.

author:  Ariel Zerahia
arielzarahia@gmail.com

## Basic (naive) implementation
Approaching the problem with synchroneuse solution, running on a single process, single thread, all information of clawled URLs is saved on memory and does not take care of managing a secure access to common resources (not thread safe).

But still it is build to be easily converted into a distributed implementation. This can be achieved by replacing the `URLsManager` class implementation with:
1. database for storing the URL's information
1. queue for managing the crawling tasks
1. some locking mechanism

### Software components
#### URLsManager
Class for managing all persistent data, and crawling tasks distribution

In a distributed solution the class functionality should be backed-up by a real queue server and a database.
good alternatives can be:
- queue: RabbitMQ
- database: I was thinking of Redis which support atomic actions that can help preventing duplicate runs of same URL, any other key/value might be a good choice although, we should take in account solving duplicate run requirement.
#### Crawler
Crawler worker class.

Stateless object that reads crawling tasks from queue and execute them, should be easily adopt to run in a distributed manner.
#### URLDataParser
Simple and minimalistic anchor links extractor, event based for not consumming to much memory.
An alternative for parsing and quering the entire document could be using BeautifulSoup.

### Install
Inside a virtual env running on python 3.8 (tested only on 3.8might run on other versions), run"
`pip install .`

### Excecution
```python web_crawler.py base_url  max_depth```
#### Execution including errors report
```python web_crawler.py base_url  max_depth --report-errors```

#### For running tests and code quality check:
`pip install .[test]` (ob zsh `pip install .\[test\]`)

##### Running tests:
`pytest tests/test.py`

##### Running flake8 (code quality):
`flake8 --max-line-length=120 --exclude=.env .` (`.env` should be replaced with the virtual env folder name)

##### Running mypy (types hints check):
` mypy --ignore-missing-imports --check-untyped-defs . `

### Testing the code
For testing the code I recommend running running it among other sites, on this two URL thar mimicates Error responces:
- http://httpstat.us/
- https://the-internet.herokuapp.com/status_codes


## Multithreaded implementation
Simple multithreaded implementation based on the basic implementation, performed by running 10 workers on saparated threads in a non-blocking I/O.

### Excecution
```python web_crawler.py base_url  max_depth --threaded```
#### Execution including errors report
```python web_crawler.py base_url  max_depth --threaded --report-errors```

## Possible Improvments
1. running in parallel in a distributed system


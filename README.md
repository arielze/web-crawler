# Lightricks Web Crawler
Web crawler for gathering links of a page till reaching a maximum depth. Each page is registered with it score of links refering  to the strt domain.

author:  Ariel Zerahia
email: arielzarahia@gmail.com

## Naive implementation
Basic implementation, all run on a single process, it saves al the information of the clawled URLs in memory and does not take care of managing a secure access to common resources.

But still it is build to be easily converted into a distributed implementation. This can be achieved by replacing the `URLsManager` class implementation with:
1. database for storing the URL's information
1. queue for managing the crawling tasks
1. some locking mechanism

### Install
Inside a virtual env running on python 3.8 (tested only on 3.8might run on other versions), run"
`pip install .`

#### For running tests and code quality check:
`pip install .[test]` (ob zsh `pip install .\[test\]`)

##### Running tests:
`pytest tests`

##### Running flake8 (code quality):
`flake8 --max-line-length=120 --exclude=.env .` (`.env` should be replaced with the virtual env folder name)

##### Running mypy (types hints check):
` mypy --ignore-missing-imports --check-untyped-defs . `

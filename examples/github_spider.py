"""Simple example using pycrawl to crawl GitHub.
"""

from pycrawl.spiders.route import RouteSpider


spider = RouteSpider(
    concurrency=5,
    urls=['https://github.com'],
    domains=['github.com', 'www.github.com'],
    max_depth=3,
)


@spider.route('github.com/\w+/?$')
def parse_user(spider, response):
    print('user', response.request.url)


@spider.route('github.com/\w+/\w+?$')
def parse_repo(spider, response):
    print('repo', response.request.url)


if __name__ == '__main__':
    spider.run()

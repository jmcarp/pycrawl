"""Simple example using pycrawl to crawl GitHub.
"""

from pycrawl.spiders.route import RouteSpider


spider = RouteSpider(__name__)
spider.config.update({
    'URLS': ['https://github.com'],
    'DOMAINS': ['github.com', 'www.github.com'],
})


@spider.route('github.com/\w+/?$')
def parse_user(spider, response):
    print('user', response.request.url)


@spider.route('github.com/\w+/\w+?$')
def parse_repo(spider, response):
    print('repo', response.request.url)


if __name__ == '__main__':
    spider.run()

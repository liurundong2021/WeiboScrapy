import logging
import os
from typing import Any
from datetime import datetime
from scrapy.http import Response
from scrapy import Spider
from scrapy import logformatter


# >>> Scrapy Static Settings >>>
BOT_NAME = "WeiboScrapy"
SPIDER_MODULES = ["WeiboScrapy.spiders"]
NEWSPIDER_MODULE = "WeiboScrapy.spiders"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
MEDIA_ALLOW_REDIRECTS = True
DOWNLOAD_WARNSIZE = 134217728 # 128 MB
DOWNLOAD_MAXSIZE = 0
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
# <<< Scrapy Static Settings <<<

# >>> Project Static Settings >>>
DOWNLOADER_MIDDLEWARES = {
    'WeiboScrapy.middlewares.CookiePoolMiddleware': 100,
    'WeiboScrapy.middlewares.ArticleMiddleware': 200,
    'WeiboScrapy.middlewares.ImageMiddleware': 201,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400
}
ITEM_PIPELINES = {
    'WeiboScrapy.pipelines.WeiboMediaPipeline': 1,
    'WeiboScrapy.pipelines.ArticleJsonPipeline': 400
}
DROPPEDMSG = "Dropped: %(exception)s" + os.linesep + "%(item)s"
class WeiboLogFormatter(logformatter.LogFormatter):
    def dropped(
        self, item: Any, exception: BaseException, response: Response, spider: Spider
    ) -> dict:
        """Logs a message when an item is dropped while it is passing through the item pipeline."""
        return {
            "level": logging.DEBUG,
            "msg": DROPPEDMSG,
            "args": {
                "exception": exception,
                "item": item,
            },
        }
LOG_FORMATTER = 'WeiboScrapy.settings.WeiboLogFormatter'
# DUPEFILTER_DEBUG = True
# <<< Project Static Settings <<<

# JOBDIR = './crawls/search'
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.2
LOG_LEVEL = 'INFO'
LOG_FILE = f'./log/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'

img = True
video = True
article = True
FILES_STORE = './output/media/'        # Directory to save media

long_text = True
retweet = True

search = {
    'keyword': '淄博',
    'time': {
        'from': '2023-04-10-00',
        'to': '2023-04-10-01'
    },
    'content': {
        'type': 'all',
        'include': 'all'
    }
}
history = {
    'user_file': 'output/users_1684738442.jsonl',
    'time': {
        'from': '2023-02-01',
        'to': '2023-04-01'
    },
    'output_dir': './output/history/'
}
blog_file = './output/淄博_test_719.jsonl' # For these spider: user, comment, repost

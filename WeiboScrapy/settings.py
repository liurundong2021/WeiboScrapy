from datetime import datetime

BOT_NAME = "WeiboScrapy"
SPIDER_MODULES = ["WeiboScrapy.spiders"]
NEWSPIDER_MODULE = "WeiboScrapy.spiders"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
MEDIA_ALLOW_REDIRECTS = True
DOWNLOAD_WARNSIZE = 134217728 # 128 MB
DOWNLOAD_MAXSIZE = 0

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 0.3

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "WeiboScrapy.middlewares.WeiboscrapySpiderMiddleware": 543,
#}

# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'WeiboScrapy.middlewares.CookiePoolMiddleware': 100
}

# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'WeiboScrapy.pipelines.WeiboMediaPipeline': 1,
   'WeiboScrapy.pipelines.ArticleJsonPipeline': 400
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

FILES_STORE = './test/media/'        # Directory to save media

img = True
video = True
article = True

LOG_LEVEL = 'INFO'
LOG_FILE = f'./log/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'

long_text = True
retweet = False   # Crawl retweet blog need to be complete, there is still many bugs, do not crawl retweet blog now.

search = {
    'keyword': '淄博',
    'time': {
        'from': '2023-04-10-00',
        'to': '2023-04-11-00'
    },
    'content': {
        'type': 'all',
        'include': 'all'
    }
}

history = {
    'user_file': 'data/淄博_04-01-00_04-17-00/user_split_200/9.jsonl',
    'time': {
        'from': '2022-04-01',
        'to': '2023-04-01'
    },
    'output_dir': './data/淄博_04-01-00_04-17-00/history/'
}

user = {
    'blog_file': './test/0.jsonl'
}

comment = {
    'blog_file': './data/blog.jsonl'
}

repost = {
    'blog_file': './data/blog.jsonl'
}

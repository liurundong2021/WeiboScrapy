import re
import json
import time
import scrapy
from tqdm import tqdm
from WeiboScrapy import config
from scrapy.http import Request
from WeiboScrapy.util import get_blog_item


class HistorySpider(scrapy.Spider):
    '''Hisotry Spider

    Crawl user hisotry blog.

    For efficiency, this spider don't crawl long-text blog content, must run long-text spider after.

    Attributes:
        user_file: A jsonl file write user info by line.
        time_from_dt: Date from.
        time_to_dt: Date to.
    '''

    name = "history"
    allowed_domains = ["weibo.com"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'WeiboScrapy.pipelines.HistoryPipeline': 300
        }
    }

    def __init__(self):
        self.user_file = config.history['user_file']
        self.ts_from = int(time.mktime(time.strptime(config.history['time']['from'], '%Y-%m-%d')))
        self.ts_to = int(time.mktime(time.strptime(config.history['time']['to'], '%Y-%m-%d')))

    def start_requests(self):
        uids = []
        with open(self.user_file) as f:
            while 1:
                line = f.readline()
                if not line:
                    break

                rc = json.loads(line)
                uid = rc['uid']
                uids.append(uid)

        for uid in tqdm(uids):
            step = 1000000
            url = f'https://weibo.com/ajax/statuses/searchProfile?uid={uid}&page=1&feature=4'
            if self.ts_to - self.ts_from <= step:
                search_url = url + f'&starttime={self.ts_from}&endtime={self.ts_to}'
                yield Request(search_url)
            else:
                for ts in range(self.ts_from, self.ts_to, step):
                    search_url = url + f'&starttime={ts}&endtime={ts + step}'
                    yield Request(search_url)
                search_url = url + f'&starttime={ts}&endtime={self.ts_to}'
                yield Request(search_url)

    def parse(self, response):
        ret = json.loads(response.text)
        data = ret.get('data', {})
        if not data:
            req = response.request
            req.dont_filter = True
            yield req
        elif data['list']:
            blogs = data['list']

            self.logger.debug(f'{response.url = }, mblogid list = {[blog["mblogid"] for blog in blogs]}')
            for blog in blogs:
                item = get_blog_item(blog)

                # 过滤转发的内容，选择原创微博
                uid = re.search('uid=(\d*)', response.url).group(1)
                if blog.get('retweeted_status', None) or item['uid'] != uid:
                    self.logger.debug(f'Not self blog - url = https://weibo.com/{item["uid"]}/{item["mblogid"]}')
                    continue

                yield item

            if len(blogs) == 20:
                url = re.sub('page=(\d*)', lambda matchobj: 'page=' + str(int(matchobj.group(1)) + 1), response.url)
                yield Request(url, priority=1)
        elif re.search('page=(\d*)', response.url).group(1) == '51':
            self.logger.warning(f'Page = 51 - {response.url = }')

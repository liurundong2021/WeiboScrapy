import re
import json
import time
import scrapy
from tqdm import tqdm
from scrapy.http import Request
from WeiboScrapy import settings
from WeiboScrapy.util import get_blog_item


class HistorySpider(scrapy.Spider):
    '''Hisotry Spider

    Crawl user hisotry blog.

    Attributes:
        user_file: A jsonl file write user info by line.
        ts_from: Timestamp from.
        ts_to: Timestamp to.
    '''

    name = "history"
    allowed_domains = ["weibo.com"]

    custom_settings = {
        'ITEM_PIPELINES': settings.ITEM_PIPELINES | {
            'WeiboScrapy.pipelines.HistoryPipeline': 300
        }
    }

    users = []

    def __init__(self):
        self.user_file = settings.history['user_file']
        self.ts_from = int(time.mktime(time.strptime(settings.history['time']['from'], '%Y-%m-%d')))
        self.ts_to = int(time.mktime(time.strptime(settings.history['time']['to'], '%Y-%m-%d')))
        if self.ts_from > self.ts_to:
            exit('Time from > time to, set again.')

        with open(self.user_file) as f:
            while 1:
                line = f.readline()
                if not line:
                    break

                item = json.loads(line)
                total = item['total']
                history = item['history']
                if not total:           # No history blogs.
                    continue
                avg_blogs, ts_start = self.avg_blogs_ts_start(history, total)
                if not ts_start:
                    continue
                if avg_blogs < 1000:
                    step = 864000       # 10 days.
                elif avg_blogs < 5000:
                    step = 432000       # 5 days.
                else:
                    step = 86400        # 1 day.
                user = {
                    'uid': item['uid'],
                    'step': step,
                    'ts_start': ts_start,
                    'history': history
                }
                self.users.append(user)

    def start_requests(self):
        for user in tqdm(self.users):
            step = user['step']
            ts_start = user['ts_start']
            url = f'https://weibo.com/ajax/statuses/searchProfile?uid={user["uid"]}&page=1&feature=4'
            for ts in range(ts_start, self.ts_to, step):
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
            for blog in blogs:
                for i in get_blog_item(blog):
                    yield i
            if len(blogs) == 20:
                url = re.sub('page=(\d*)', lambda matchobj: 'page=' + str(int(matchobj.group(1)) + 1), response.url)
                yield Request(url)
        elif re.search('page=(\d*)', response.url).group(1) == '51':
            self.logger.warning(f'Page = 51 - {response.url = }')

    def avg_blogs_ts_start(self, history: dict, total: int) -> tuple[int, int]:
        '''Coumpute to get search history time step, and get timestamp start.
        '''

        count = 0
        ts_start = 0
        for y in history:
            for m in history[y]:
                ts = time.mktime(time.strptime(f'{y}-{m}', '%Y-%m'))
                if ts < self.ts_to and ts > self.ts_from:
                    if count == 0:
                        ts_start = int(ts)
                    count += 1
        if not ts_start:        # If no blogs in time interval.
            return 0, 0
        else:
            avg_blogs = int(total / count)
            return avg_blogs, ts_start

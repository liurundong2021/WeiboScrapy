import re
import json
import scrapy
from time import time
from tqdm import tqdm
from scrapy.http import Request
from WeiboScrapy import settings

# TODO: need complete.
# 1. merge retweet item to blog item, add a flag to distinguish them. See get_blog_item in util.py
class RepostSpider(scrapy.Spider):
    name = "repost"

    custom_settings = {
        'ITEM_PIPELINES': settings.ITEM_PIPELINES | {
            'WeiboScrapy.pipelines.CommentRepostPipeline': 300
        }
    }

    mids = set()

    def __init__(self):
        with open(settings.blog_file) as f:
            while 1:
                line = f.readline()
                if not line:
                    break

                item = json.loads(line)
                mid = item['mid']
                self.mids.add(mid)

    def start_requests(self):
        for mid in tqdm(self.mids):
            url = f'https://weibo.com/ajax/statuses/repostTimeline?id={mid}&page=1'
            yield Request(url)

    def parse(self, response):
        ret = json.loads(response.text)
        max_page = ret['max_page']
        reposts = ret['data']

        for repost in reposts:
            item = {
                'origin_mid': repost['retweeted_status']['mid'],
                'uid': repost['user']['idstr'],
                'created_at': repost['created_at'],
                'text': repost['text_raw'],
                'location': repost.get('region_name', '').replace('发布于 ', ''),
                'mblogid': repost['mblogid'],
                'mid': repost['mid'],
                'source': repost['source'],
                'attitudes_count': repost['attitudes_count'],
                'comments_count': repost['comments_count'],
                'reposts_count': repost['reposts_count'],
                'ts': int(time())
            }
            yield item

        page = int(re.search('page=(\d+)', response.url).group(1))
        if page < max_page:
            url = re.sub('page=(\d+)', f'page={page+1}', response.url)
            yield Request(url)

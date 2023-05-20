import re
import json
import scrapy
from time import time
from tqdm import tqdm
from WeiboScrapy import settings
from scrapy.http import Request


class CommentSpider(scrapy.Spider):
    name = "comment"
    allowed_domains = ["weibo.com"]

    custom_settings = {
        'ITEM_PIPELINES': {
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
            url = f'https://weibo.com/ajax/statuses/buildComments?is_show_bulletin=0&id={mid}'
            yield Request(url)

    def parse(self, response):
        # TODO - When there is picture in comment.
        ret = json.loads(response.text)
        max_id = ret.get('max_id')
        comments = ret['data']
        mid = re.search(r'id=(\d+)', response.url).group(1)

        for comment in comments:
            item = {
                'origin_mid': mid,
                'uid': comment['user']['idstr'],
                'created_at': comment['created_at'],
                'like_counts': comment['like_counts'],
                'floor_number': comment['floor_number'],
                'source': comment.get('source', '').replace('来自', ''),
                'text': comment['text_raw'],
                'rootid': comment['rootidstr'],
                'readtimetype': comment['readtimetype'],
                'reply_id': comment.get('reply_comment', {}).get('idstr', ''),
                'ts': int(time())
            }
            yield item

        if max_id:
            url = response.url
            if 'max_id' in url:
                url = re.sub(r'max_id=\d+', f'max_id={max_id}', url)
            else:
                url += f'&max_id={max_id}'
            yield Request(url)

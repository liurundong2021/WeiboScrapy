import re
import json
import scrapy
from time import time
from tqdm import tqdm
from scrapy.http import Request
from WeiboScrapy import settings


class UserSpider(scrapy.Spider):
    name = "user"
    allowed_domains = ["weibo.com"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'WeiboScrapy.pipelines.UserPipeline': 300
        }
    }

    uids = set()

    def __init__(self):
        with open(settings.blog_file) as f:
            while 1:
                line = f.readline()
                if not line:
                    break

                item = json.loads(line)
                uid = item['uid']
                self.uids.add(uid)

    def start_requests(self):
        for uid in tqdm(self.uids):
            url = f'https://weibo.com/ajax/profile/info?uid={uid}'
            yield Request(url, cb_kwargs={'uid': uid})

    def parse(self, response, uid):
        if "usernotexists" in response.url:
            self.logger.info(f"User do not exist! - {uid = }")
        else:
            data = json.loads(response.text)
            user_data:dict = data['data']['user']
            item = {
                "uid": user_data['idstr'],
                "screen_name": user_data['screen_name'],
                'gender': user_data.get('gender', ''),
                'location': '',
                'created_at': '',
                'credit_level': '',
                'education': '',
                'description': user_data.get('description'),
                'total': 0,
                "verified": user_data['verified'],
                'verified_type': user_data['verified_type'],
                'verified_reason': user_data.get('verified_reason', ''),
                'verified_type_ext': user_data.get('verified_type_ext', ''),
                'v_plus': user_data.get('v_plus'),
                'followers_count': user_data.get('followers_count'),
                'follow_count': user_data.get('friends_count'),
                'statuses_count': user_data.get('statuses_count'),
                'svip': user_data.get('svip'),
                'top_user': user_data.get('top_user'),
                'user_type': user_data.get('user_type'),
                'is_star': user_data.get('is_star'),
                'history': '',
                'avatar_hd': user_data['avatar_hd'],
                'mbrank': user_data.get('mbrank'),
                'mbtype': user_data.get('mbtype'),
                'planet_video': user_data.get('planet_video'),
                'pc_new': user_data.get('pc_new'),
                'profile_url': 'https://weibo.com' + user_data.get('profile_url'),
                'ts': int(time())
            }
            url = f"https://weibo.com/ajax/profile/detail?uid={item['uid']}"
            yield Request(url, self.parse_detail, cb_kwargs={'item': item})

    def parse_detail(self, response, item:dict):
        data: dict = json.loads(response.text)['data']

        item['location'] = data.get('ip_location', '').replace('IP属地：', '')
        if not item['location']:
            item['location'] = data.get('location', '')
        item['location'] = re.sub(r'\s.*', '', item['location'])
        item['created_at'] = data.get('created_at')
        item['credit_level'] = data.get('sunshine_credit', {}).get('level', '')
        item['education'] = data.get('education', {}).get('school', '')

        url = f'https://weibo.com/ajax/profile/mbloghistory?uid={item["uid"]}'
        yield Request(url, self.parse_mbloghistory, cb_kwargs={'item': item})

    def parse_mbloghistory(self, response, item:dict):
        history = json.loads(response.text).get('data', {})
        if not history:
            req = response.request
            req.dont_filter = True
            yield req

        item['history'] = history
        uid = item['uid']
        url = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0'
        yield Request(url, self.parse_mblogcount, cb_kwargs={'item': item})

    def parse_mblogcount(self, response, item:dict):
        total = json.loads(response.text)['data']['total']
        item['total'] = total
        yield item

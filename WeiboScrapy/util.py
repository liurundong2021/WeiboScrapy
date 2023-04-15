import re
import json
from time import time
from scrapy.http import Request
from scrapy.http import Response


def get_blog_item(data):
    '''Get blog item by Weibo response JSON data.
    '''

    item = {
        'mblogid': data['mblogid'],
        'mid': data['mid'],
        'uid': data['user']['idstr'],
        'created_at': data['created_at'],
        'region_name': data.get('region_name', '').replace('发布于 ', ''),
        'source': re.sub('<.*?>', '', data['source']),
        'edit_count': data.get('edit_count', 0),
        'mblogtype': data['mblogtype'],
        'mlevel': data['mlevel'],
        'isLongText': 1 if 'continue_tag' in data and data['isLongText'] else 0,

        'content': data['text_raw'].replace('\u200b', ''),
        'pic_num': data['pic_num'],
        'pic_ids': data['pic_ids'],

        'reposts_count': data['reposts_count'],
        'comments_count': data['comments_count'],
        'comment_selected': data['comment_manage_info']['approval_comment_type'],
        'attitudes_count': data['attitudes_count'],

        'ts': int(time()),
    }
    # TODO - object: video, article...
    # video url
    # if 'page_info' in data and data['page_info'].get('object_type', '') == 'video':
    #     if 'cards' in data['page_info']:
    #         item['video'] = data['page_info']['cards'][0]['media_info']['stream_url']
    #     else:
    #         item['video'] = data['page_info']['media_info']['mp4_720p_mp4']

    return item

def parse_long_text(res: Response):
    '''Parse entire text content for long blog.
    '''

    data: dict = json.loads(res.text)['data']

    if data['ok']:
        item = res.meta['item']
        item['content'] = data['longTextContent'].replace('\u200b', '')
        yield item
    else:
        yield Request(res.url, parse_long_text, dont_filter=True, meta={'item': res.meta['item']})

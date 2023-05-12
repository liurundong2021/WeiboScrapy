import re
import json
from time import time
import logging


logger = logging.getLogger(__name__)

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
        # TODO - pic in text extract fail.
        'pic_ids': [pic['pic_id'] for pic in data.get('pic_focus_point', {})],

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

def parse_long_text(response, item):
    '''Parse entire text content for long blog.
    '''

    res = json.loads(response.text)
    ok = res['ok']
    longTextContent = res.get('data', {}).get('longTextContent', '')
    if not ok:
        logger.info(f'Long-text content request failed - {res["ok"] = } {res.get("message", "") = }')
    else:
        if longTextContent:
            item['content'] = longTextContent
            yield item
        else:
            req = response.request
            req.dont_filter = True
            yield req

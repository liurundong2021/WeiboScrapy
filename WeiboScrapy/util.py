import re
import json
from time import time
import logging


logger = logging.getLogger(__name__)

def get_blog_item(data: dict):
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
        'pic_ids': data.get('pic_ids', []),
        'video_url': '',
        'article_id': '',

        'reposts_count': data['reposts_count'],
        'comments_count': data['comments_count'],
        'comment_selected': data['comment_manage_info']['approval_comment_type'],
        'attitudes_count': data['attitudes_count'],

        'ts': int(time()),
    }

    # Get other type pic.
    if item['pic_num'] != len(item['pic_ids']):
        if item['pic_num'] == len(item['pic_ids']) + 1:
            pic_re = re.search('mapi/(.*)\s?', data['text_raw'])
            if pic_re:
                item['pic_ids'].append(pic_re.group(1))
            else:
                logger.warning(f'Can not get pic url in text - {item["mblogid"] = }, {item["uid"] = }')
        else:
            logger.warning(f'pic_nums and len(pic_ids) not pare - {item["mblogid"] = }, {item["uid"] = }, {item["pic_num"] = }, {len(item["pic_ids"]) = }')

    text = json.dumps(data, ensure_ascii=False)
    # If has video, get video url.
    video_re = re.search(r'"(http://f.video.weibocdn.com/.*?)"', text)
    if video_re:
        item['video_url'] = video_re.group(1)
    # If has article, get article id.
    article_re = re.search(r'https://weibo.com/ttarticle/p/show\?id=(\d*)', text)
    if article_re:
        item['article_id'] = article_re.group(1)

    return item

def parse_long_text(response, item):
    '''Parse entire text content for long blog.
    '''

    res = json.loads(response.text)
    ok = res['ok']
    longTextContent = res.get('data', {}).get('longTextContent', '')
    if not ok:
        logger.info(f'Long-text content request failed - {item["mblogid"] = }, {item["uid"] = }, {res.get("message", "") = }')
    else:
        if longTextContent:
            item['content'] = longTextContent
            yield item
        else:
            req = response.request
            req.dont_filter = True
            yield req

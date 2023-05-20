import re
import json
from time import time
import logging
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

# TODO: merge retweet.
def get_blog_item(ret: dict):
    '''Get blog item by Weibo response JSON data.
    '''

    item = {
        'mblogid': ret['mblogid'],
        'mid': ret['mid'],
        'uid': ret['user']['idstr'],
        'created_at': ret['created_at'],
        'region_name': ret.get('region_name', '').replace('发布于 ', ''),
        'source': re.sub('<.*?>', '', ret['source']),
        'edit_count': ret.get('edit_count', 0),
        'mblogtype': ret['mblogtype'],
        'mlevel': ret['mlevel'],
        'isLongText': 1 if 'continue_tag' in ret and ret['isLongText'] else 0,

        'content': ret['text_raw'].replace('\u200b', ''),
        'img_count': 0,
        'video_count': 0,
        'article_count': 0,
        # 'pic_num': ret['pic_num'],
        # 'pic_ids': [],
        # 'video_url': '',
        # 'article_id': '',

        'reposts_count': ret['reposts_count'],
        'comments_count': ret['comments_count'],
        'comment_selected': ret['comment_manage_info']['approval_comment_type'],
        'attitudes_count': ret['attitudes_count'],

        'file_urls': [],
        'files': [],
        'medias': {},

        'ts': int(time()),
    }

    if 'mix_media_info' in ret:
        for media_item in ret['mix_media_info']['items']:
            if media_item['type'] == 'pic':
                item['img_count'] += 1
                item['medias'][media_item['data']['largest']['url']] = 'img'
            elif media_item['type'] == 'video':
                item['video_count'] += 1
                item['medias'][media_item['data']['media_info']['mp4_720p_mp4']] = 'video'
            else:
                logger.warning(f'mix_media_info item, not pic and video - {item["mblogid"] = }, {item["uid"] = }, {media_item.get("id", "") = }')

    if 'pic_infos' in ret:
        for pic in ret['pic_infos']:
            item['img_count'] += 1
            item['medias'][ret['pic_infos'][pic]['original']['url']] = 'img'

    if '查看图片' in ret['text'].split('//<')[0]:
        soup = BeautifulSoup(ret['text'], 'html.parser')
        links = soup.find_all('a')
        for link in links:
            if link.text == '查看图片':
                item['img_count'] += 1
                item['medias'][link['href']] = 'img'

    if 'page_info' in ret:
        object_type = ret['page_info'].get('object_type', '')
        if object_type == 'video':
            item['video_count'] += 1
            if 'cards' in ret['page_info']:
                item['medias'][ret['page_info']['cards'][0]['media_info']['stream_url']] = 'video'
            else:
                url = ret['page_info']['media_info']['mp4_720p_mp4']
                if not url:
                    url = ret['page_info']['media_info']['mp4_hd_url']
                if not url:
                    url = ret['page_info']['media_info']['stream_url']
                item['medias'][url] = 'video'

        elif object_type == 'article':
            item['article_count'] += 1
            item['medias']['https://weibo.com/ttarticle/p/show?id=' + ret['page_info']['page_id']] = 'article'

    if ret['pic_num'] != item['img_count']:
        logger.warning(f'pic_nums and img_count not pare - {item["mblogid"] = }, {item["uid"] = }, {ret["pic_num"] = }, {item["img_count"] = }, {item["medias"]}\n' +
                       f'{ret["text"] = }')


    if '微博视频' in ret['text'] and not item['video_count']:
        logger.warning(f'text has "微博视频" but video_count = 0 - {item["mblogid"] = }, {item["uid"] = }')

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

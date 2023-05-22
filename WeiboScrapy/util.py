import re
import json
import logging
from time import time
from bs4 import BeautifulSoup
from WeiboScrapy import settings
from scrapy.http import Request


logger = logging.getLogger(__name__)

def parse_blog(response):
    ret = json.loads(response.text)
    if not ret.get('ok', 1):
        logger.info(f'Request blog failed - {response.url}, {ret.get("message", "") = }')
    else:
        return get_blog_item(ret)

def get_blog_item(ret: dict, type: str = 'origin'):
    # Basic parse item.
    item = {
        'mblogid': ret['mblogid'],
        'mid': ret['mid'],
        'uid': ret['user']['idstr'],
        'complaint': ret.get('complaint', {}).get('showcontent', ''),
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
        'type': type,
        'retweet_mblogid': '',

        'reposts_count': ret['reposts_count'],
        'comments_count': ret['comments_count'],
        'comment_manage_info': ret['comment_manage_info'],
        'attitudes_count': ret['attitudes_count'],

        'file_urls': [],
        'files': [],
        'medias': {},

        'ts': int(time()),
    }
    if 'retweeted_status' in ret:
        item['retweet_mblogid'] = ret['retweeted_status']['mblogid']
        item['type'] = 'retweet'

    # TODO: Put it after parse long-text.
    # If image or video url is in long-text but not short content, this won't get url in the tail of long-text.
    # Get image and video
    if '查看图片' in ret['text'].split('//<')[0]:
        soup = BeautifulSoup(ret['text'].split('//<')[0], 'html.parser')
        links = soup.find_all('a')
        for link in links:
            if link.text == '查看图片':
                item['img_count'] += 1
                item['medias'][link['href']] = 'img'
    if 'pic_infos' in ret:
        for pic in ret['pic_infos']:
            item['img_count'] += 1
            item['medias'][ret['pic_infos'][pic]['original']['url']] = 'img'
    if 'mix_media_info' in ret:
        for media_item in ret['mix_media_info']['items']:
            if media_item['type'] == 'pic':
                item['img_count'] += 1
                item['medias'][media_item['data']['largest']['url']] = 'img'
            elif media_item['type'] == 'video':
                item['video_count'] += 1
                url = media_item['data']['media_info']['mp4_720p_mp4']
                if not url:
                    url = media_item['data']['media_info']['stream_url']
                item['medias'][url] = 'video'
            else:
                logger.warning(f'mix_media_info item, not pic and video - {item["mblogid"] = }, {item["uid"] = }, {media_item.get("id", "") = }')
    if 'retweeted_status' not in ret and 'page_info' in ret:
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

    # Validate if image and video crawl right.
    if ret['pic_num'] != item['img_count']:
        logger.warning(f'pic_nums and img_count not pare - {item["mblogid"] = }, {item["uid"] = }, {ret["pic_num"] = }, {item["img_count"] = }, {item["medias"]}')
    if '微博视频' in ret['text'].split('//<')[0] and not item['video_count']:
        logger.warning(f'text has "微博视频" but video_count = 0 - {item["mblogid"] = }, {item["uid"] = }')

    # Parse retweet blog.
    if item['retweet_mblogid'] and settings.retweet:
        retweet_blog = ret['retweeted_status']
        if not retweet_blog['user']:
            item['retweet_mblogid'] = retweet_blog['text_raw'].replace('\u200b', '')
        else:
            if 'page_info' in ret:
                retweet_blog['page_info'] = ret['page_info']
            for i in get_blog_item(ret['retweeted_status'], 'retweet_origin'):
                yield i

    # Advance parse item: long-text and retweet.
    if item['isLongText'] and settings.long_text:
        mbid = item['mblogid']
        url = f'https://weibo.com/ajax/statuses/longtext?id={mbid}'
        yield Request(url, parse_long_text, cb_kwargs={'item': item})
    else:
        yield item

def parse_long_text(response, item):
    res = json.loads(response.text)
    longTextContent = res.get('data', {}).get('longTextContent', '')
    if not res['ok']:
        logger.info(f'Long-text content request failed - {item["mblogid"] = }, {item["uid"] = }, {res.get("message", "") = }')
    elif longTextContent:
        item['content'] = longTextContent
        yield item
    else:
        req = response.request
        req.dont_filter = True
        yield req

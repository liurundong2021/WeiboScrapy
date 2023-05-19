import re
import os
import json
import hashlib
import mimetypes
import logging
from time import time
from hashlib import md5
from bs4 import BeautifulSoup
from datetime import datetime
from WeiboScrapy import settings
from pathlib import Path
from scrapy.http import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.python import to_bytes


logger = logging.getLogger(__name__)

class SearchPipeline:
    count = 0

    def open_spider(self, spider):
        ts = int(time())
        kw = settings.search['keyword']
        tf = settings.search['time']['from']
        tt = settings.search['time']['to']
        ct = settings.search['content']['type']
        ci = settings.search['content']['include']
        self.file_name = f'{ts}_{kw}_{tf}_{tt}_{ct}_{ci}.jsonl'
        self.file = open(f'./output/{self.file_name}', 'w')

    def process_item(self, item, spider):
        self.count += 1
        line = json.dumps(item, ensure_ascii=False) + '\n'
        self.file.write(line)
        self.file.flush()
        return item

    def close_spider(self, spider):
        self.file.close()
        new_file_name = re.sub('\.jsonl', f'_{self.count}.jsonl', self.file_name)
        os.rename(f'./output/{self.file_name}', f'./output/{new_file_name}')

class HistoryPipeline:
    def open_spider(self, spider):
        name = re.search(r".*/(.*)\.jsonl", settings.history["user_file"]).group(1)
        self.output_path = settings.history['output_dir'] + name
        os.makedirs(self.output_path)

    def process_item(self, item, spider):
        uid = item['uid']
        with open(f'{self.output_path}/{uid}.jsonl', 'a') as f:
            line = json.dumps(item, ensure_ascii=False) + '\n'
            f.write(line)

        return item

class UserPipeline:
    def open_spider(self, spider):
        ts = int(time())
        output_path = f'./output/users_{ts}.jsonl'
        self.file = open(output_path, 'w')

    def process_item(self, item, spider):
        self.file.write(json.dumps(item, ensure_ascii=False) + '\n')
        self.file.flush()
        return item

    def close_spider(self, spider):
        self.file.close()

class CommentRepostPipeline:
    def open_spider(self, spider):
        ts = int(time())
        self.output_path = f'./output/{spider.name}_{ts}/'
        os.mkdir(self.output_path)

    def process_item(self, item, spider):
        file = self.output_path + item['origin_mid'] + '.jsonl'
        with open(file, 'a') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return item

class WeiboMediaPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        if 'f.video.weibocdn.com' in request.url:
            # video from weibo.
            url_no_param = request.url.split('?')[0].split('/')[-1]
            media_guid = hashlib.sha1(to_bytes(url_no_param)).hexdigest()
            media_ext = Path(url_no_param).suffix
        else:
            # video from other platform. find has kuaishou video in test.
            # TODO: video from kuaishou is redirect url, wheather to get origin url, then can get file name.
            media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
            media_ext = Path(request.url).suffix

        if media_ext not in mimetypes.types_map:
            media_ext = ""

            media_type = mimetypes.guess_type(request.url)[0]
            if media_type:
                media_ext = mimetypes.guess_extension(media_type)
            else:
                if item['medias'][request.url] == 'video':
                    media_ext = '.mp4'
                elif item['medias'][request.url] == 'img':
                    media_ext = '.jpg'
                elif item['medias'][request.url] == 'article':
                    media_ext = '.html'

        return f"{media_guid}{media_ext}"

    def get_media_requests(self, item, info):
        for url in item['medias']:
            if ((settings.img and item['medias'][url] == 'img')
                or (settings.video and item['medias'][url] == 'video')
                or (settings.article and item['medias'][url] == 'article')):
                yield Request(url)

class ArticleJsonPipeline:
    def process_item(self, item, spider):
        if not settings.article:
            return item

        for file in item['files']:
            if 'ttarticle' in file['url'] and 'html' in file['path']:
                atc_html = open(settings.FILES_STORE + file['path']).read()
                logger.debug('load file path: ' + settings.FILES_STORE + file['path'])
                # os.remove(FILES_STORE + file['path'])
                soup = BeautifulSoup(atc_html, 'html.parser')
                atc_json = {
                    'title': soup.find('title').text,
                    'author': soup.find('em', 'W_autocut').text,
                    'pub_time': datetime.fromtimestamp(int(soup.find('span', 'time')['bjtimestamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'read_count': soup.find('span', 'num').text.split('：')[1],
                    'ts': int(time()),
                    'content': ''
                }
                if soup.find('div', 'WB_editor_iframe_word'):
                    atc_json['content'] = soup.find('div', 'WB_editor_iframe_word')
                elif soup.find('div', 'WB_editor_iframe_new'):
                    atc_json['content'] = soup.find('div', 'WB_editor_iframe_new')
                else:
                    logger.error(f'Parse {file["path"]} error.')
                atc_json['content'] = atc_json['content'].text.replace('\u200b', '').strip()
                file_name = file['path'].split('.')[0] + '.json'
                with open(settings.FILES_STORE + file_name, 'w') as f:
                    f.write(json.dumps(atc_json, ensure_ascii=False))
                file['path'] = file_name
                file['checksum'] = md5(str(atc_json).encode('utf-8')).hexdigest()
        return item

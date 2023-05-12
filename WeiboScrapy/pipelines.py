import re
import os
import json
from time import time
from WeiboScrapy import config


class SearchPipeline:
    count = 0

    def open_spider(self, spider):
        ts = int(time())
        kw = config.search['keyword']
        tf = config.search['time']['from']
        tt = config.search['time']['to']
        ct = config.search['content']['type']
        ci = config.search['content']['include']
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
        self.output_path = './output/hisotry/' + re.search('.*/(.*)\.jsonl', spider.user_file).group(1)
        os.makedirs(self.output_path, exist_ok=True)

    def process_item(self, item, spider):
        uid = item['uid']
        with open(f'{self.output_path}/{uid}.jsonl', 'a') as f:
            line = json.dumps(item, ensure_ascii=False) + '\n'
            f.write(line)

        return item

import re
import json
from WeiboScrapy import config
from datetime import datetime
from datetime import timedelta
from WeiboScrapy.util import get_blog_item
from WeiboScrapy.util import parse_long_text
from scrapy import Spider
from scrapy.http import Request


class SearchSpider(Spider):
    '''Search spider.

    Crawl search result by advance search on Weibo.

    Attributes:
        name: Spider name.
        kw: Search keyword
        tf: time from
        tt: time to
        ct: content type
        ci: content include
        ctd: content type dict
        cid: content include dict
        dt_parse_format: search url timescope format
    '''

    name = 'search'
    allowed_domains = ['weibo.com']

    custom_settings = {
        'ITEM_PIPELINES': {
            'WeiboScrapy.pipelines.SearchPipeline': 300
        }
    }

    dt_parse_format = '%Y-%m-%d-%H'
    ctd = {
        'default': '',
        'hot': '&xsort=hot',
        'ori': '&scope=ori',
        'verify': '&vip=1',
        'media': '&category=4'
    }
    cid = {
        'default': '',
        'pic': '&haspic=1',
        'video': '&hasvideo=1',
        'link': '&haslink=1'
    }

    def __init__(self):
        self.kw = config.search['keyword']
        self.tf = config.search['time']['from']
        self.tt = config.search['time']['to']
        self.ct = config.search['content']['type']
        self.ci = config.search['content']['include']

        self.logger.info(
            'Search spider start...\n' +
            f'--- keyword: {self.kw}\n' +
            f'--- time from: {self.tf}\n' +
            f'--- time to: {self.tt}\n' +
            f'--- content type: {self.ct}\n' +
            f'--- content include: {self.ci}'
        )

    def start_requests(self):
        # format datetime
        dt_from = datetime.strptime(self.tf, self.dt_parse_format)
        dt_to = datetime.strptime(self.tt, self.dt_parse_format)
        dt = dt_from

        # traverse timescope
        while(dt < dt_to):
            # traverse search content type and content include
            # scrapy会自动过滤重复web请求，最终爬取到的数据不会冗余
            dt_str_from = dt.strftime(self.dt_parse_format)
            dt_str_to = (dt + timedelta(hours=1)).strftime(self.dt_parse_format)
            self.logger.info(f'Crawling: keyword = {self.kw} timescope = :{dt_str_from}:{dt_str_to}')
            if self.ct == 'all' and self.ci == 'all':
                for ct in self.ctd.values():
                    for ci in self.cid.values():
                        url = self.get_search_url(dt, ct, ci)
                        yield Request(url)
            elif self.ci == 'all':
                for ci in self.cid.values():
                    url = self.get_search_url(dt, self.ctd[self.ct], ci)
                    yield Request(url)
            elif self.ct == 'all':
                for ct in self.ctd.values():
                    url = self.get_search_url(dt, ct, self.cid[self.ci])
                    yield Request(url)
            else:
                url = self.get_search_url(dt, self.ctd[self.ct], self.cid[self.ci])
                yield Request(url)
            dt += timedelta(hours=1)

    def parse(self, respons):
        '''Parse search result page.

        Send Weibo request, get response and extract mbid. Then send blog info Request, parse blog content.
        '''
        html = respons.text

        if 'card-no-result' in html:
            pass
        else:
            mbids = re.findall(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', html)
            for mbid in mbids:
                url = f'https://weibo.com/ajax/statuses/show?id={mbid}'
                yield Request(url, self.parse_blog, priority=2)
            next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
            if next_page:
                url = 'https://s.weibo.com' + next_page.group(1)
                yield Request(url, priority=1)

    def get_search_url(self, dt: datetime, ct='', ci=''):
        '''Generate search URL.
        '''

        dt_str_from = dt.strftime(self.dt_parse_format)
        dt_str_to = (dt + timedelta(hours=1)).strftime(self.dt_parse_format)

        url = (
            f'https://s.weibo.com/weibo?q={self.kw}' +
            f'&timescope=custom%:{dt_str_from}:{dt_str_to}' +
            f'{ct}' +
            f'{ci}'
        )

        return url

    def parse_blog(self, respons):
        '''Parse blog info.
        '''

        data = json.loads(respons.text)
        item = get_blog_item(data)

        if item['isLongText']:
            mbid = item['mblogid']
            url = f'https://weibo.com/ajax/statuses/longtext?id={mbid}'
            yield Request(url, parse_long_text, meta={'item': item}, priority=3)
        else:
            yield item

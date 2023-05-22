import re
from datetime import datetime
from datetime import datetime
from datetime import timedelta
from WeiboScrapy import settings
from WeiboScrapy.util import parse_blog
from scrapy import Spider
from scrapy.http import Request
from bs4 import BeautifulSoup


class SearchSpider(Spider):
    '''Search Spider.

    Crawl search result by advance search on Weibo.

    Attributes:
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

    custom_settings = {
        'ITEM_PIPELINES': settings.ITEM_PIPELINES | {
            'WeiboScrapy.pipelines.RetweetFilterPipeline': 200,
            'WeiboScrapy.pipelines.SearchPipeline': 300,
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
        self.kw = settings.search['keyword']
        self.tf = settings.search['time']['from']
        self.tt = settings.search['time']['to']
        self.ct = settings.search['content']['type']
        self.ci = settings.search['content']['include']
        self.long_text = settings.long_text

        self.logger.info(
            'Search spider start...\n' +
            f'--- keyword: {self.kw}\n' +
            f'--- time from: {self.tf}\n' +
            f'--- time to: {self.tt}\n' +
            f'--- content type: {self.ct}\n' +
            f'--- content include: {self.ci}'
        )

    def start_requests(self):
        dt_from = datetime.strptime(self.tf, self.dt_parse_format)
        dt_to = datetime.strptime(self.tt, self.dt_parse_format)
        dt = dt_from

        while(dt < dt_to):
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

    def parse(self, response):
        html = response.text

        if 'card-no-result' in html:
            pass
        else:
            soup = BeautifulSoup(html, 'html.parser')
            div_froms = soup.find_all('div', 'from')
            for div_from in div_froms:
                mbid = re.search(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', str(div_from)).group(1)
                url = f'https://weibo.com/ajax/statuses/show?id={mbid}'
                yield Request(url, parse_blog)
            next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
            if next_page:
                url = 'https://s.weibo.com' + next_page.group(1)
                yield Request(url)

    def get_search_url(self, dt: datetime, ct='', ci=''):
        dt_str_from = dt.strftime(self.dt_parse_format)
        dt_str_to = (dt + timedelta(hours=1)).strftime(self.dt_parse_format)

        url = (
            f'https://s.weibo.com/weibo?q={self.kw}' +
            f'&timescope=custom%:{dt_str_from}:{dt_str_to}' +
            f'{ct}' +
            f'{ci}'
        )

        return url

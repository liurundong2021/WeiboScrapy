# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import re
import json
import logging
from WeiboScrapy.settings import DEFAULT_REQUEST_HEADERS
from requests import get
from scrapy.exceptions import CloseSpider
from scrapy.exceptions import StopDownload


logger = logging.getLogger(__name__)

# class WeiboscrapySpiderMiddleware:
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the spider middleware does not modify the
#     # passed objects.

#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_spider_input(self, response, spider):
#         # Called for each response that goes through the spider
#         # middleware and into the spider.

#         # Should return None or raise an exception.
#         return None

#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.

#         # Must return an iterable of Request, or item objects.
#         for i in result:
#             yield i

#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.

#         # Should return either None or an iterable of Request or item objects.
#         pass

#     def process_start_requests(self, start_requests, spider):
#         # Called with the start requests of the spider, and works
#         # similarly to the process_spider_output() method, except
#         # that it doesn’t have a response associated.

#         # Must return only requests (not items).
#         for r in start_requests:
#             yield r

#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)


# # class WeiboscrapyDownloaderMiddleware:
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the downloader middleware does not modify the
#     # passed objects.

#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_request(self, request, spider):
#         # Called for each request that goes through the downloader
#         # middleware.

#         # Must either:
#         # - return None: continue processing this request
#         # - or return a Response object
#         # - or return a Request object
#         # - or raise IgnoreRequest: process_exception() methods of
#         #   installed downloader middleware will be called
#         return None

#     def process_response(self, request, response, spider):
#         # Called with the response returned from the downloader.

#         # Must either;
#         # - return a Response object
#         # - return a Request object
#         # - or raise IgnoreRequest
#         return response

#     def process_exception(self, request, exception, spider):
#         # Called when a download handler or a process_request()
#         # (from other downloader middleware) raises an exception.

#         # Must either:
#         # - return None: continue processing this exception
#         # - return a Response object: stops process_exception() chain
#         # - return a Request object: stops process_exception() chain
#         pass

#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)

class CookiePoolMiddleware():
    """Cookie pool middleware
    """

    ##### pool structure #####
    # pool = {
    #    "cookie name": {                       cookie name in cookies.json
    #        "cookie": "<cookie example>",      cookie value in cookies.json
    #        "status": 0                        for record failed times
    #    }
    # }
    ##########################
    pool = {}
    ck_names = []           # Cookie names.
    i = 0                   # Cookie index, for rotate cookie names.

    def __init__(self):
        headers = DEFAULT_REQUEST_HEADERS
        with open('WeiboScrapy/cookies.json') as f:
            cookies = json.load(f)

        logger.info("Testing cookie...")
        for ck_name in cookies.keys():
            cookie = cookies[ck_name].strip()
            headers["Cookie"] = cookie
            r = get("https://s.weibo.com/weibo?q=123", headers=headers, allow_redirects=False)

            if r.status_code == 200:
                self.pool[ck_name] = {"cookie": cookie, "status": 0}
                self.ck_names.append(ck_name)
            else:
                logger.warning(f"Cookie not available! - {ck_name = }, {r.status_code = }")

        logger.info(f"Available cookie count: {len(self.pool)}")

        if len(self.pool) == 0:
            raise CloseSpider("No cookie available, modify your 'cookies.json'.")


    def process_request(self, request, spider):
        """
        Set cookie for request.
        """

        ck_name = self.get_ck_name()
        request.headers["cookie"] = bytes(self.pool[ck_name]["cookie"], "utf-8")
        request.meta["ck_name"] = ck_name

    def process_response(self, request, response, spider):
        """
        Varify cookie usable, and handle outdated cookie.
        """

        ck_name = request.meta['ck_name']

        # TODO - Spider middleware.
        # When crawl user, maybe user is not exist.
        if "usernotexists" in response.text:
            uid = re.search("uid=(\d*)", response.url).group(1)
            logger.info(f"User do not exist! - {uid = }")
            raise StopDownload(fail=False)
        elif response.status in [302, 400]:
            self.pool[ck_name]['status'] += 1
            new_ck_name = self.get_ck_name()
            request.headers['cookie'] = bytes(self.pool[new_ck_name]['cookie'], 'utf-8')
            request.dont_filter = True
            request.meta['ck_name'] = new_ck_name
            return request
        elif response.status == 414:
            spider.crawler.engine.close_spider(self, reason='Frequently request has been detect, spider closed. Please increase DOWNLOAD_DELAY.')
        else:
            # Signal to tell cookie is alive.
            self.pool[ck_name]['status'] = 0
            if ck_name not in self.ck_names:
                self.ck_names.append(ck_name)
            return response

    def get_ck_name(self):
        """
        Cookie pool api

        If cookie failed consecutive for 5 times, regard as expired, remove from pool.
        Cookie success for once cookie failure will be reset.
        """

        while self.ck_names:
            self.i = (self.i + 1) % len(self.ck_names)
            ck_name = self.ck_names[self.i]
            if self.pool[ck_name]["status"] < 5:
                return ck_name
            self.ck_names.remove(ck_name)
            logger.warning(f"Cookie removed(expired)! - name: {ck_name}")
            logger.info(f"Available cookie count: {len(self.ck_names)}")
        raise CloseSpider('No cookie available! - get_ck_name')

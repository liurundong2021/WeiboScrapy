import json
import logging
from requests import get


logger = logging.getLogger(__name__)

class CookiePoolMiddleware():
    pool = []
    i = 0                   # Cookie index, for rotate cookie names.
    fail_count = {}

    def __init__(self):
        headers = { 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36' }

        cookies_str = open('WeiboScrapy/cookies.json').read()
        cookies = json.loads(cookies_str)

        logger.info("Testing cookie...")
        for cookie in cookies:
            logger.debug(f'Testing {cookie["key"]}...')
            headers["Cookie"] = cookie["value"]
            r = get("https://weibo.com/", headers=headers, allow_redirects=False)

            if r.status_code == 200:
                self.pool.append(cookie)
                self.fail_count[cookie['key']] = 0
            else:
                logger.info(f"{cookie['key']} not available.")

        if len(self.pool) == 0:
            exit("No cookie available, modify your 'cookies.json'.")
        else:
            logger.info(f"{len(self.pool)} cookies available.")

    def process_request(self, request, spider):
        cookie = self.get_cookie()
        request.headers["cookie"] = bytes(cookie["value"], "utf-8")
        request.meta["cookie"] = cookie

    def process_response(self, request, response, spider):
        cookie = request.meta['cookie']
        logger.debug(f'Response info - {response.url = }, {response.status = }')

        # Temporary failure, request again.
        if 'login' in response.url or 'passport' in response.url or response.status == 400:
            new_cookie = self.get_cookie(cookie)
            request.headers['cookie'] = bytes(new_cookie['value'], 'utf-8')
            request.dont_filter = True
            request.meta['cookie'] = new_cookie
            return request
        # Request frequently.
        elif response.status == 414:
            logger.warning('Request frequently, decrease DOWNLOAD_DELAY or stop for a while.')
            spider.crawler.engine.close_spider(spider, reason='Frequently request has been detect, spider closed. Please increase DOWNLOAD_DELAY.')
            return request
        else:
            self.fail_count[cookie['key']] = 0
            if cookie not in self.pool:
                self.pool.append(cookie)
            return response

    def get_cookie(self, old_cookie=None):
        if old_cookie:
            self.fail_count[old_cookie['key']] += 1
            if self.fail_count[old_cookie['key']] > 10:
                self.pool.remove(old_cookie)
                logger.info(f'Remove cookie - {old_cookie["key"]}')
        self.i = (self.i + 1) % len(self.pool)
        return self.pool[self.i]

class ArticleMiddleware:
    '''For verify wheather article request is correct.
    '''

    def process_response(self, request, response, spider):
        if 'ttarticle' in request.url and '抱歉，出错啦' in response.text:
            request.dont_filter = True
            return request
        else:
            return response

class ImageMiddleware:
    '''Request weibo image need this referer value in headers.
    '''

    def process_request(self, request, spider):
        if 'sinaimg' in request.url:
            request.headers['Referer'] = bytes('https://weibo.com/', 'utf-8')

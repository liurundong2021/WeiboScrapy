import json
import logging
from requests import get
from scrapy.exceptions import CloseSpider


logger = logging.getLogger(__name__)

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
        headers = { 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36' }

        cookie_file = open('WeiboScrapy/cookies.json').read()
        cookies = json.loads(cookie_file)

        logger.info("Testing cookie...")
        for ck_name in cookies:
            logger.debug(f'Testing {ck_name = }...')
            cookie = cookies[ck_name].strip()
            headers["Cookie"] = cookie
            r = get("https://weibo.com/", headers=headers, allow_redirects=False)

            if r.status_code == 200:
                self.pool[ck_name] = {"cookie": cookie, "status": 0}
                self.ck_names.append(ck_name)
            else:
                logger.info(f"{ck_name = } not available.")

        if len(self.pool) == 0:
            raise CloseSpider("No cookie available, modify your 'cookies.json'.")
        else:
            logger.info(f"{len(self.pool)} cookies available.")

    def process_request(self, request, spider):
        """
        Set cookie for request.
        """

        ck_name = self.get_ck_name()
        request.headers["cookie"] = bytes(self.pool[ck_name]["cookie"], "utf-8")
        request.meta["ck_name"] = ck_name
        if 'sinaimg' in request.url:
            # Success request weibo image need this referer value.
            request.headers['Referer'] = bytes('https://weibo.com/', 'utf-8')

    def process_response(self, request, response, spider):
        """
        Varify cookie usable, and handle outdated cookie.
        """

        ck_name = request.meta['ck_name']

        # Cookie outdate.
        if 'login' in response.url or 'passport' in response.url:
            logger.debug(f'{ck_name = } outdate.')
            if ck_name in self.ck_names:
                self.ck_names.remove(ck_name)
            # Request again.
            new_ck_name = self.get_ck_name()
            request.headers['cookie'] = bytes(self.pool[new_ck_name]['cookie'], 'utf-8')
            request.dont_filter = True
            request.meta['ck_name'] = new_ck_name
            return request
        # Request frequently.
        elif response.status == 414:
            # TODO: do not close spider when frequently, rotate cookie pool or wait for some time.
            # self.pool[ck_name]['status'] += 1
            spider.crawler.engine.close_spider(self, reason='Frequently request has been detect, spider closed. Please increase DOWNLOAD_DELAY.')
            return request
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
            logger.info(f"{ck_name = } expired.")
            logger.info(f"{len(self.ck_names)} cookies available.")
        # TODO: spider do not close.
        raise CloseSpider('No cookie available!')

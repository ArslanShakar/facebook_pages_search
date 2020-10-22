# -*- coding: utf-8 -*-

import csv
import json
import random
import time
from datetime import datetime
from urllib.parse import quote

from scrapy import Spider, Request, Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


def get_search_terms_from_file():
    with open('../input/search terms.csv', mode='r', encoding='utf-8') as csv_file:
        return [x.get('search keyword') for x in csv.DictReader(csv_file)
                if x.get('search keyword', '').strip()]


class FacebookPublicGroupsSpider(Spider):
    name = 'facebook_public_groups'
    allowed_domains = ['www.facebook.com']
    base_url = 'https://www.facebook.com/'

    search_keywords = get_search_terms_from_file()
    pages_search_url_t = 'https://web.facebook.com/public?query={q}&type=pages'
    # "https://web.facebook.com/pages/category/dentist/"

    # options = webdriver.ChromeOptions()
    options = webdriver.FirefoxOptions()
    options.add_argument('--disable-gpu')

    # driver = Chrome(ChromeDriverManager().install(), options=options)
    driver = Firefox(executable_path="../geckodriver")

    today_date = datetime.today().strftime('%d%b%y')

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': f'../output/facebook_pages_{today_date}.csv',
        'FEED_EXPORT_FIELDS': ['page_name', 'page_link', 'search_keyword', 'phone', 'email',
                               'street_address', 'city', 'state', 'postal_code', 'country']
    }

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.parse, meta={'handle_httpstatus_all': True})

    def parse(self, response):
        # seen_pages = []
        # for r in csv.DictReader(open("../output/facebook pages.csv")):
        #     r = dict(r)
        #     if r['page_name'] == 'page_name' or r['page_link'] in seen_pages:
        #         continue
        #     seen_pages.append(r['page_link'])
        #     r['country'] = r["city"].split(',')[-1].strip()
        #     yield r
        #
        # return

        for keyword in self.search_keywords[:]:
            url = self.pages_search_url_t.format(q=quote(keyword))
            response = self.get_response_from_web_driver(url)
            time.sleep(30)

            for page in response.css('._3u1'):
                page_url = page.css('a._32mo::attr(href)').get('')
                item = dict()
                item['page_link'] = page_url
                item['search_keyword'] = keyword

                yield self.parse_details(
                    self.get_response_from_web_driver(page_url.rstrip('/') + '/about', scroll=False), item)

        # for e in csv.DictReader(open("../output/facebook pages.csv")):
        #     item = dict()
        #     item['page_link'] = e['page_link']
        #     item['search_keyword'] = e['search_keyword']
        #
        #     yield self.parse_details(
        #         self.get_response_from_web_driver(e['page_link'].rstrip('/') + '/about', scroll=False), item)

    def parse_details(self, response, item):
        item['page_name'] = response.css('#u_0_0 span a ::text').get('').strip()
        item['phone'] = response.css('._50f4:contains(Call)::text').get('').lstrip('Call ')
        email = ''.join([a for a in response.css('a::attr(href)').getall() if 'mailto' in a])
        item['email'] = email.replace('mailto:', '')
        # item['phone'] = response.css('._4-u3:contains(About) + div ::text').get()
        raw = json.loads(response.css('[type="application/ld+json"]::text').get('{}'))
        address = raw.get('address', {})
        if address:
            item["street_address"] = address['streetAddress']
            item["city"] = address['addressLocality'] or ''
            item["state"] = address['addressRegion']
            item["postal_code"] = address['postalCode']
            item['country'] = item["city"].split(',')[-1].strip()
            return item

    def get_response_from_web_driver(self, url, scroll=True):
        self.driver.get(url)

        if not scroll:
            self.is_exists(css_selector='#u_0_0 span a', timeout=4)
            return Selector(text=self.driver.page_source)

        time.sleep(random.choice([1, 1.5, 2, 2.5]))
        start_point = 0
        end_point = 8000

        if not self.is_exists(css_selector='._3u1', timeout=2):
            return Selector(text=self.driver.page_source)

        while True:
            if self.is_exists(css_selector='#browse_end_of_results_footer', timeout=0.5):
                break

            self.driver.execute_script(f"window.scrollTo({start_point}, {end_point});")

            time.sleep(0.2)

            start_point, end_point = end_point, end_point + 8000

        return Selector(text=self.driver.page_source)

    def is_exists(self, css_selector, timeout=4.0):
        try:
            WebDriverWait(self.driver, timeout=timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

            return True  # success

        except TimeoutException:
            return False  # fail

    def close(spider, reason):
        try:
            spider.driver.close()
        except:
            pass

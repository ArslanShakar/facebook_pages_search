# -*- coding: utf-8 -*-
import csv
import time
from datetime import datetime
from urllib.parse import quote
import random

from scrapy import Spider, Request, Selector, signals
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from ..items import FacebookSearchItem


def get_search_terms_from_file():
    with open('../search terms.csv', mode='r', encoding='utf-8') as csv_file:
        return [x.get('search keyword') for x in csv.DictReader(csv_file)]


class FacebookSpider(Spider):
    name = 'facebook'
    allowed_domains = ['www.facebook.com']
    base_url = 'https://www.facebook.com/'

    search_keywords = get_search_terms_from_file()
    pages_search_url_t = 'https://web.facebook.com/public?query={q}&type=pages'

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    driver = Chrome(ChromeDriverManager().install(), options=options)

    todays_date = datetime.today().strftime('%d%m%Y')

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': f'../output/facebook search results_{todays_date}.csv',
        'FEED_EXPORT_FIELDS': ['page_name', 'page_link', 'search_keyword', 'phone', 'email']
    }

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.parse, meta={'handle_httpstatus_all': True})

    def parse(self, response):
        for keyword in self.search_keywords:
            url = self.pages_search_url_t.format(q=quote(keyword))
            response = self.get_response_from_web_driver(url)

            for page in response.css('._3u1'):
                page_url = page.css('a._32mo::attr(href)').get('')
                item = FacebookSearchItem()
                item['page_link'] = page_url
                item['search_keyword'] = keyword

                yield self.parse_details(
                    self.get_response_from_web_driver(page_url.rstrip('/') + '/about', scroll=False), item)

    def parse_details(self, response, item):
        item['page_name'] = response.css('#u_0_0 span a ::text').get()
        item['phone'] = response.css('._50f4:contains(Call)::text').get('').lstrip('Call ')
        item['email'] = ''.join([a for a in response.css('a::attr(href)').getall() if 'mailto' in a]).lstrip('mailto:')
        # item['phone'] = response.css('._4-u3:contains(About) + div ::text').get()

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

# -*- coding: utf-8 -*-
import csv
import time
from urllib.parse import quote

from scrapy import Spider, Selector, Request


def get_search_terms_from_file():
    with open('../search terms.csv', mode='r', encoding='utf-8') as csv_file:
        return [x.get('search_term') for x in csv.DictReader(csv_file)]


class FacebookSpider(Spider):
    name = 'test'
    allowed_domains = ['www.facebook.com']
    start_urls = ['https://www.facebook.com/']

    search_terms = get_search_terms_from_file()
    pages_search_url_t = 'https://web.facebook.com/public?query={q}&type=pages'

    def start_requests(self):
        for term in self.search_terms:
            url = self.pages_search_url_t.format(q=quote(term))
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        a=0

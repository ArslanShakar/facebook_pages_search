# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class FacebookSearchItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    page_link = Field()
    search_keyword = Field()
    page_name = Field()
    phone = Field()
    email = Field()

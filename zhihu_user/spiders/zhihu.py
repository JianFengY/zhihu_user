# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider, Request
import json

from zhihu_user.items import UserItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_user = 'excited-vczh'

    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
    # 粉丝
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    # 关注
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        """spider中初始的request是通过调用start_requests()来获取的"""
        # 获取用户信息
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        # 获取粉丝列表
        yield Request(self.followers_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20),
                      callback=self.parse_followers)
        # 获取关注列表
        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20),
                      callback=self.parse_follows)

    def parse_user(self, response):
        """获取用户信息，并分别调用方法获取他们的关注与粉丝"""
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        # 对获取到的用户，再获取他们的粉丝列表
        yield Request(
            self.followers_url.format(user=result.get('url_token'), include=self.followers_query, offset=0, limit=20),
            self.parse_followers)
        # 获取他们的关注列表
        yield Request(
            self.follows_url.format(user=result.get('url_token'), include=self.follows_query, offset=0, limit=20),
            self.parse_follows)

    def parse_followers(self, response):
        """获取某个用户所有粉丝列表"""
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)  # 调用parse_user()爬取某个粉丝的信息
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_followers)  # 爬取下一页粉丝列表

    def parse_follows(self, response):
        """获取某个用户所有关注列表"""
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)  # 调用parse_user()爬取某个关注者的信息
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_follows)  # 爬取下一页关注列表

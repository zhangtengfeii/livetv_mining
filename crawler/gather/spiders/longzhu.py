# -*- coding: utf-8 -*-
from scrapy import Spider, Request

from ..items import ChannelItem, RoomItem

import json


class LongZhuSpider(Spider):
    name = 'longzhu'
    allowed_domains = ['longzhu.com', 'plu.cn']
    start_urls = [
        'http://www.longzhu.com/channels'
    ]
    custom_settings = {
        'SITE': {
            'code': 'longzhu',
            'name': '龙珠',
            'description': '龙珠直播-游戏直播平台',
            'url': 'http://www.longzhu.com',
            'image': 'http://r.plures.net/plu/images/small-longzhu-logo.png',
            'show_seq': 4
        }
    }

    def parse(self, response):
        channel_list = []
        for div_element in response.xpath('//div[@class="list-item-thumb"]'):
            a_element = div_element.xpath('a')[0]
            url = a_element.xpath('@href').extract_first()
            short = url[url.rfind('/') + 1:]
            name = a_element.xpath('@title').extract_first()
            image = a_element.xpath('img/@src').extract_first()
            channel_list.append({
                'short': short,
                'name': name,
                'image': image,
                'url': response.urljoin(url)
            })
        room_query = {
            'url': 'http://api.plu.cn/tga/streams?max-results=50&sort-by=top',
            'offset': 0, 'channels': channel_list
        }
        yield Request('{}&start-index=0'.format(room_query['url']), callback=self.parse_room_list, meta=room_query)

    def parse_room_list(self, response):
        channel_list = response.meta['channels']
        room_list = json.loads(response.text)['data']['items']
        if isinstance(room_list, list):
            for mixjson in room_list:
                cjson = mixjson['game'][0]
                if len(channel_list) > 0:
                    filter_channel = [channel for channel in channel_list if channel['short'] == cjson['tag']]
                    if len(filter_channel) > 0:
                        yield ChannelItem({
                            'office_id': str(cjson['id']),
                            'short': filter_channel[0]['short'],
                            'name': filter_channel[0]['name'],
                            'image': filter_channel[0]['image'],
                            'url': filter_channel[0]['url']
                        })
                        channel_list.remove(filter_channel[0])

                rjson = mixjson['channel']
                yield RoomItem({
                    'office_id': str(rjson['id']),
                    'name': rjson['status'],
                    'image': mixjson['preview'],
                    'url': rjson['url'],
                    'online': int(mixjson['viewers']) if mixjson['viewers'].isdigit() else 0,
                    'host': rjson['name'],
                    'channel': cjson['tag']
                })
            if len(room_list) > 0:
                next_meta = response.meta
                next_meta['offset'] += 50
                yield Request('{}&start-index={}'.format(next_meta['url'], str(next_meta['offset'])),
                              callback=self.parse_room_list, meta=next_meta)

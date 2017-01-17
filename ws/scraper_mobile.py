#!/usr/bin/env python3

# This scraper uses m.weibo.cn as data source. This source doesn't
# require cookies, the transfer size is usually only ~10% of that of
# weibo.com (a HUGE advantage), and we can extract data like status
# texts much more easily with this structured data source; but for what
# we do, there is also one drawback: the granularity of status creation
# time is capped at one minute.

import json
import re
import time

import arrow
import requests

import ws.conf
import ws.utils
from ws.logger import logger

TZ = 'Asia/Shanghai'

SESSION = requests.Session()
SESSION.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
}

MWEIBOCN_STATUS_LINK = re.compile(r'^http://m\.weibo\.cn/status/(?P<basename>\w+)\?.*')

def fetch(uid):
    try:
        resp = SESSION.get(
            f'http://m.weibo.cn/container/getIndex?type=uid&value={uid}&containerid=107603{uid}',
            headers={'Referer': f'http://m.weibo.com/u/{uid}'},
        )
    except Exception:
        logger.warning('connection failed, retrying in 5...')
        time.sleep(5)
        return None
    if resp.status_code != 200:
        dumppath = ws.utils.dump(resp.text)
        logger.warning(f'got HTTP {resp.status_code}; response dumped into {dumppath}')
        return None
    try:
        return resp.json()
    except json.JSONDecodeError:
        logger.warning('response cannot be decoded as JSON')
        return None

def parse_datetime(d):
    year, month, day, *_ = arrow.now().to(TZ).timetuple()
    if d.endswith('分钟前'):
        minutes = int(d[:-3])
        t =  arrow.now().replace(minutes=-minutes)
    elif d.endswith('小时前'):
        hours = int(d[:-3])
        t = arrow.now().replace(hours=-hours)
    elif d.startswith('今天'):
        t = arrow.get(d, 'hh:mm', tzinfo=TZ).replace(year=year, month=month, day=day)
    elif d[2] == '-':  # not starting with a four digit year
        t = arrow.get(d, 'MM-DD hh:mm', tzinfo=TZ).replace(year=year)
    else:
        t = arrow.get(d, 'YYYY-MM-DD hh:mm', tzinfo=TZ)
    return t.to(TZ).timestamp

# Returns a list of quadruplets of three ints and a str:
#   (ouid, status_id, status_timestamp, url)
def parse(response):
    statuses = []
    try:
        for card in response['cards']:
            status_link = card['scheme']
            status = card['mblog']
            # Skip pinned status
            if 'isTop' in status and status['isTop'] == 1:
                continue

            ouid = int(status['user']['id'])
            sid = int(status['id'])

            timestamp = parse_datetime(status['created_at'])

            url_basename = MWEIBOCN_STATUS_LINK.match(status_link).group('basename')
            url = f'http://weibo.com/{ouid}/{url_basename}'

            statuses.append((ouid, sid, timestamp, url))
    except Exception:
        dumppath = ws.utils.dumpjson(response)
        logger.warning(f'invalid response; response object dumped into {dumppath}')
        raise
        return []

    return statuses

# Returns a triplet of two ints and a str:
#   (status_id, status_timestamp, url)
# or None if no original status is found.
def latest_status(uid):
    uid = int(uid)
    response = fetch(uid)
    if response is None:
        return None
    statuses = parse(response)
    try:
        return next(filter(lambda s: s[0] == uid, statuses))[1:]
    except StopIteration:
        dumppath = ws.utils.dumpjson(response)
        logger.warning(f'no original status found; response object dumped into {dumppath}')
        return None

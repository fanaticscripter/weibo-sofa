#!/usr/bin/env python3

import http.cookies
import re
import time

import arrow
import requests

import ws.conf
from ws.logger import logger

# 1st group: original user id pattern
# 2nd group: content between ouid and mid, might contain
#            r'feedtype=\"top\"', the signature of a pinned status
# 3rd group: status id pattern
# 4th group: last path segment of the status URL (which should look like
#            http://weibo.com/<status_id>/<hash>
# 5th group: timestamp pattern (Javascript millisecond timstamp, 13
#            digits till year 2286)
EXTRACTOR = re.compile(r'ouid=(\d+)(.*?)mid=\\"(\d+)\\".*?href=\\"\\/\1\\/(\w+)\?.*?date=\\"(\d{13})\\"')

SESSION = requests.Session()
SESSION.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
}

def load_cookie(s):
    cookie = http.cookies.SimpleCookie()
    cookie.load(s)
    for key, morsel in cookie.items():
        SESSION.cookies.set(key, morsel.value, domain='weibo.com')
    load_cookie.has_been_run = True

load_cookie.has_been_run = False

def fetch(uid):
    if not load_cookie.has_been_run:
        raise RuntimeError('Haven\'t provided weibo.com cookie with load_cookie')
    try:
        resp = SESSION.get(f'http://weibo.com/u/{uid}?is_all=1')
    except Exception:
        logger.warning('Connection failed, retrying in 5...')
        time.sleep(5)
        return None
    if resp.status_code != 200:
        logger.warning(f'Got HTTP {resp.status_code}')
        return None
    return resp.text

# Returns a list of quadruplets of three ints and a str:
#   (ouid, status_id, status_timestamp, url)
def parse(html):
    statuses = []
    for ouid, filler, sid, basename, timestamp_ms in EXTRACTOR.findall(html):
        # Skip pinned status
        if r'feedtype=\"top\"' not in filler:
            ouid = int(ouid)
            sid = int(sid)
            timestamp = int(timestamp_ms) // 1000
            url = f'http://weibo.com/{ouid}/{basename}'
            statuses.append((ouid, sid, timestamp, url))
    return statuses

# Returns a triplet of two ints and a str:
#   (status_id, status_timestamp, url)
# or None if no original status is found.
def latest_status(uid):
    uid = int(uid)
    html = fetch(uid)
    if html is None:
        return None
    statuses = parse(html)
    try:
        return next(filter(lambda s: s[0] == uid, statuses))[1:]
    except StopIteration:
        logger.warning('No original status found')
        return None

load_cookie(ws.conf.cookies)

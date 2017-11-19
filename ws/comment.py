#!/usr/bin/env python3

import time

import requests

import ws.conf
from ws.logger import logger

DEFAULT_COMMENT = ws.conf.comment_text
DEFAULT_REPLY = ws.conf.reply_text
ACCESS_TOKEN = ws.conf.access_token

SESSION = requests.session()
SESSION.headers = {
    # This doesn't appear to be documented anywhere, but without setting
    # the content type to application/x-www-form-urlencoded, I get error
    # code 10016 ("miss required parameter (comment), see doc for more
    # info.") all the time. Finally found out from a blog post
    # http://jianfeihit.iteye.com/blog/1821712.
    #
    # application/x-www-form-urlencoded for *a JSON request without even
    # a body*? You kidding me? What a garbage API.
    'Content-Type': 'application/x-www-form-urlencoded',
}

# sid is the status id; text is the content of the comment, defaulting
# to comment.text in conf.ini.
def post_comment(sid, text=DEFAULT_COMMENT):
    if not text:
        logger.warning('comment should not be empty')
        return False
    url = 'https://api.weibo.com/2/comments/create.json'
    payload = {
        'access_token': ACCESS_TOKEN,
        'comment': text,
        'id': sid,
    }
    try:
        resp = SESSION.post(url, params=payload)
    except Exception:
        logger.warning('connection failed')
        return False
    if resp.status_code != 200:
        logger.warning(f'got HTTP {resp.status_code}: {resp.text}')
        return False
    else:
        return True

# sid is the status id, cid is the comment id, text is the content of
# the reply, default to comment.reply_text in conf.ini.
def reply_to_comment(sid, cid, text=DEFAULT_REPLY):
    if not text:
        logger.warning('reply to comment should not be empty')
        return False
    url = 'https://api.weibo.com/2/comments/reply.json'
    payload = {
        'access_token': ACCESS_TOKEN,
        'cid': cid,
        'id': sid,
        'comment': text,
        'without_mention': 1,
    }
    try:
        resp = SESSION.post(url, params=payload)
    except Exception:
        logger.warning('connection failed')
        return False
    if resp.status_code != 200:
        logger.warning(f'got HTTP {resp.status_code}: {resp.text}')
        return False
    else:
        return True

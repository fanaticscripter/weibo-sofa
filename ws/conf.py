#!/usr/bin/env python3

import configparser
import os
import re
import sys

from ws.logger import logger

# Root of the repo
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

CONFPATH = os.path.join(root, 'conf.ini')
if not os.path.isfile(CONFPATH):
    logger.error(f'conf.ini not found in {root}')
    sys.exit(1)
config = configparser.ConfigParser()
try:
    config.read(CONFPATH)
except configparser.ParsingError:
    logger.error('conf.ini corrupted')
    sys.exit(1)

# spec is of the form section.key
SPEC = re.compile('^(?P<section>.*)\.(?P<key>.*)$')
def getkey(spec, type=None, required=True, default=None):
    m = SPEC.match(spec)
    section = m.group('section')
    key = m.group('key')
    try:
        value = config[section][key]
    except KeyError:
        if required and default is None:
            logger.error(f'{spec} required but not found in conf.ini')
            sys.exit(1)
        else:
            value = default
    if type is not None:
        value = type(value)
    return value

access_token = getkey('app.access_token')
max_delay = getkey('comment.max_delay', type=float, default=60)
op_comment_max_delay = getkey('comment.op_comment_max_delay', type=float, default=300)
comment_text = getkey('comment.text')
reply_text = getkey('comment.reply_text', default=comment_text)
cookies = getkey('scraper.cookies', required=False)
polling_interval = getkey('scraper.polling_interval', type=float, default=1)

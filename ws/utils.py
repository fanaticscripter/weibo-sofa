#!/usr/bin/env python3

import json
import os
import tempfile

# Shorten text to no longer than count characters, ending in ... if
# necessary.
def shorten(text, count):
    if len(text) <= count:
        return text
    else:
        return text[:count-3] + '...'

# Dump text into a tempfile, and returns the path.
def dump(text):
    fd, path = tempfile.mkstemp
    os.write(fd, text)
    os.close(fd)
    return path

def dumpjson(obj):
    dump(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))

#!/usr/bin/env python3

import os

from peewee import *

import ws.conf

DBPATH = os.path.join(ws.conf.root, 'statuses.db')
db = SqliteDatabase(DBPATH)

class Status(Model):
    uid = IntegerField()
    sid = IntegerField(unique=True)
    timestamp = IntegerField()
    url = TextField(unique=True)

    class Meta:
        database = db

# Returns True if inserted; False if already exists
def insert_status(uid, sid, timestamp, url):
    # We don't require timestamps to match, because different data
    # sources can have different granularity in timestamps.
    _, created = Status.get_or_create(uid=uid, sid=sid, url=url, defaults={'timestamp': timestamp})
    return created

db.create_tables([Status], safe=True)

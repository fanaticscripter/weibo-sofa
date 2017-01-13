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
    url = TextField()

    class Meta:
        database = db

# Returns True if inserted; False if already exists
def insert_status(uid, sid, timestamp, url):
    _, created = Status.get_or_create(uid=uid, sid=sid, timestamp=timestamp, url=url)
    return created

db.create_table(Status, safe=True)

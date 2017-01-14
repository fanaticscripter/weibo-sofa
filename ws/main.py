#!/usr/bin/env python3

import argparse
import signal
import sys
import time

import arrow

TZ = 'Asia/Shanghai'

def sigint_handler(signal, frame):
    print('Interrupted.', file=sys.stderr)
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def timestamp2print(timestamp, timefmt=None):
    if timefmt is None:
        timefmt = '%Y-%m-%dT%H:%M:%S%z'
    return arrow.get(timestamp).to(TZ).strftime(timefmt)

def main():
    parser = argparse.ArgumentParser(description='Grab target user\'s Weibo sofas.')
    parser.add_argument('uid', type=int, help='user id of the target user')
    args = parser.parse_args()
    uid = args.uid

    # Import local modules after parsing arguments so as to not fail
    # with missing conf when user is simply trying to read the help
    # text.
    import ws.comment
    import ws.conf
    import ws.db
    import ws.scraper

    polling_interval = ws.conf.polling_interval
    max_delay = ws.conf.max_delay

    starting_time = 0
    while True:
        # Sleep until polling_interval seconds after the starting time
        # of the last request.
        sleep_length = (starting_time + polling_interval) - time.time()
        if sleep_length > 0:
            time.sleep(sleep_length)

        starting_time = time.time()
        try:
            sid, timestamp, url = ws.scraper.latest_status(uid)
        except TypeError:
            # Got None
            continue

        new = ws.db.insert_status(uid, sid, timestamp, url)
        if new:
            now = timestamp2print(time.time())
            posting_time = timestamp2print(timestamp)
            print(f'{now}: {uid} {sid} {posting_time} {url}')

            # Do not post the comment if we're already too late to the
            # party
            if time.time() - timestamp > max_delay:
                continue
            successful = ws.comment.post_comment(sid)
            if successful:
                now = timestamp2print(time.time())
                print(f'{now}: posted comment to {url}')

if __name__ == '__main__':
    main()

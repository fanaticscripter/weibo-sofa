#!/usr/bin/env python3

import argparse
import logging
import signal
import sys
import time

import arrow

from ws.logger import logger

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
    parser.add_argument('-m', '--mobile', action='store_true',
                        help='''scrape mobile site m.weibo.cn instead of
                        weibo.com (does not require cookies, provides huge
                        transfer size savings, but you might be blocked after a
                        while, and status posting time granularity is limited
                        to one minute)''')
    parser.add_argument('-n', '--no-salt-to-injury', action='store_true',
                        help='''do not add salt to injury by replying to
                        target user's first comment''')
    parser.add_argument('--skip-repost', action='store_true',
                        help='do not grab the sofa if the status is a repost')
    parser.add_argument('--mercy', action='store_true', help='leave sofa to the target user')
    parser.add_argument('-d', '--debug', action='store_true', help='print debugging info')
    parser.add_argument('uid', type=int, help='user id of the target user')
    args = parser.parse_args()
    uid = args.uid
    mobile = args.mobile
    mercy = args.mercy

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Import local modules after parsing arguments so as to not fail
    # with missing conf when user is simply trying to read the help
    # text.
    import ws.comment
    import ws.conf
    import ws.db

    if mobile:
        import ws.scraper_mobile as scraper
    else:
        import ws.scraper as scraper

    polling_interval = ws.conf.polling_interval
    max_delay = ws.conf.max_delay
    op_comment_max_delay = ws.conf.op_comment_max_delay
    # There's an uncertainty of 60 seconds in posting time obtained from
    # the mobile site data source; we have to add this to the max delay.
    if mobile:
        max_delay += 60
        op_comment_max_delay += 60

    posting_time_fmt = '%Y-%m-%dT%H:%M%z' if mobile else None

    starting_time = 0
    new_status_timestamp = 0  # Used when waiting for OP to post a comment
    while True:
        # Sleep until polling_interval seconds after the starting time
        # of the last request.
        sleep_length = (starting_time + polling_interval) - time.time()
        if sleep_length > 0:
            time.sleep(sleep_length)

        logger.debug('polling')
        starting_time = time.time()
        latest = scraper.latest_status(uid)
        try:
            sid, timestamp, url, repost = latest
        except TypeError:
            # Got None
            continue

        new = ws.db.insert_status(uid, sid, timestamp, url)
        if new:
            new_status_timestamp = timestamp
            now = timestamp2print(time.time())
            posting_time = timestamp2print(timestamp, timefmt=posting_time_fmt)
            print(f'{now}: {uid} {sid} {posting_time} {url}')

            # Do not post the comment if we're already too late to the
            # party
            if time.time() - timestamp <= max_delay:
                if repost and args.skip_repost:
                    print(f'{now}: did not comment on this repost due to --skip-repost')
                elif mercy:
                    print(f'{now}: withheld comment due to --mercy')
                else:
                    successful = ws.comment.post_comment(sid)
                    if successful:
                        now = timestamp2print(time.time())
                        print(f'{now}: posted comment to {url}')
        else:
            logger.debug(f'seen: {sid}')

        # Try to reply to OP's first comment
        # The mobile scraper doesn't support this feature
        if ((not args.no_salt_to_injury and not mobile and
             time.time() <= new_status_timestamp + op_comment_max_delay)):
            comments = scraper.status_comments(sid)
            if comments is None:  # Failed to extract comments
                continue
            # The returned comments are in reverse chronological order
            # Find the earliest one posted by the OP and reply to it
            for _, cid, comment_uid in reversed(comments):
                if comment_uid == uid:
                    break
            else:
                # OP hasn't commented yet (or comments pour in too fast
                # and OP's comment already fell out of the first page)
                continue

            successful = ws.comment.reply_to_comment(sid, cid)
            if successful:
                now = timestamp2print(time.time())
                print(f'{now}: posted reply to comment {cid} in {url}')
                # Reset new status timestamp to stop checking
                new_status_timestamp = 0

if __name__ == '__main__':
    main()

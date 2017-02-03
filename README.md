<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# weibo-sofa

![Supported Python Versions](https://img.shields.io/badge/python-3.6-blue.svg?maxAge=2592000)
![License](https://img.shields.io/badge/license-WTFPL-blue.svg?maxAge=2592000)

A simple and harmless tool to troll your Weibo followee, especially if they're into grabbing their own "sofa". 😉 Always be the first to respond! (Well, not guaranteed, but we try our best.)

# Table of contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Roadmap](#roadmap)
- [Notes](#notes)
- [License](#license)

## Installation

Python 3.6 or later is required due to usage of [f-strings](https://docs.python.org/3.6/whatsnew/3.6.html#whatsnew36-pep498). With a suitable Python installed:

```
git clone https://github.com/fanaticscripter/weibo-sofa.git
cd weibo-sofa
pip install -r requirements.txt
./sofa --help
```

Installation within a venv is highly recommended.

## Configuration

Copy `conf.ini.template` to `conf.ini`, then fill out the values. You will need

- weibo.com cookies in order to download pages (grab them from browser after signing in) — only required if you use the primary weibo.com data source, and can be omitted if you use the mobile m.weibo.cn data source (`-m, --mobile`);
- A Weibo API access token in order to post comments (register an app at [open.weibo.com/development](http://open.weibo.com/development) then generate a token in Weibo's [API explorer](http://open.weibo.com/tools/apitest.php)).

## Usage

`sofa` expects a Weibo user id, e.g., `5230466807`. Run

```
./sofa <uid>
```

and `sofa` will start doing its thing (blocking). Due to its blocking and long-running nature, it's best practice to run `sofa` within a terminal multiplexer, e.g. GNU Screen or tmux. It is possible to run multiple `sofa` sessions with different uids, but weibo.com might decide you're abusive and temporarily stop serving you pages.

More info in

```
./sofa --help
```

Sample session:

```
./sofa 5230466807
2017-01-13T06:31:31+08:00 5230466807 4062857111079909 2017-01-11T22:14:42+08:00 http://weibo.com/5230466807/Eqncr4wVT
2017-01-13T16:49:22+08:00 5230466807 4063500009818236 2017-01-13T16:49:21+08:00 http://weibo.com/5230466807/EqDVmFcaE
2017-01-13T16:49:23+08:00 posted comment to http://weibo.com/5230466807/EqDVmFcaE
...
```

## How it works

Weibo's API does not allow access to user timeline and statuses unless the target user has authorized your app. This is annoying but understandable: data is what they sell, so they don't give it up for free. Being understandable doesn't help with problem solving though, and there's really nothing immoral about automating access to a tiny, tiny slice of proprietary yet public (or at least visible to you) data for lolz, so we just scrape weibo.com's web pages to get the job done.

Yet web scraping code is inherently brittle, especially for pages as bad as weibo.com's — at the moment they frigging serve raw HTML content in escaped Javascript strings (!!!) on their desktop site, and user pages on their mobile site m.weibo.cn are nothing more than a dummy container plus generic JS code (I probably should look into their AJAX calls). (**Update**: I have added an alternative scraper utilizing m.weibo.cn's structured data source — available under the `-m, --mobile` option — which doesn't require cookies, provides huge transfer size savings, and is hopefully more resilient to random changes by Sina's shitty programmers. There's one fatal issue though: running at a one second interval, I always get blocked after a few hours — the private API starts returning 403 for every single request; then it takes quite a while for the block to time out. Another minor issue is that the posting time granularity there is limited to one minute.) Therefore, don't be surprised if my regex-based scraper breaks at any moment. Rest assured that when it breaks it will be very noisy about it.

So, we talked about scraping weibo.com for data. We do it very often, every 1 second by default (configurable), if your connection to weibo.com can keep up with it — requests are serialized. The rest is obvious: if we detect a new status, we immediately post the pre-configured comment to it. Note that we don't post a comment if the status has been out for a while already, because it would be a shame if you claim to be the sofa occupier when you actually aren't; the default tolerable delay is 1 minute (again configurable).

I'd recommend running `sofa` on a server or desktop (anything constantly on and connected, really) located in Mainland China (or anywhere where the connection to weibo.com is fast and reliable, which can't be said for my current U.S. residence), or results may be disappointing.

**Update (Feb 3, 2017).** I have now added the ability to also reply to OP's first comment to her own status. Check out `comment.reply_text` and `comment.op_comment_max_delay` in `conf.ini.template` for details. This feature isn't supported by the mobile scraper, since that one is in a state of abandonment.

## Roadmap

- Add optional OAuth flow to generate token from appid and secret.

## Notes

- Including emojis is simple. Weibo automatically converts textual representations of emojis — that is, emoji names wrapped in square brackets — into emojis. For instance, comment text "沙发[二哈]" would become "沙发![[二哈]](https://img.t.sinajs.cn/t4/appstyle/expression/ext/normal/74/moren_hashiqi_org.png)". Find out the names of emojis by inserting them with Weibo's status composer.

- Including images is hard. There's no support in the API. If you manage to get ahold of a link like <http://photo.weibo.com/h5/comment/compic_id/1022:230597fc542ee08ed312f4de2d1ed5d541b430>, you could shorten it with `t.cn` (in this case, into <http://t.cn/RtCfXI1>), and include the short link in the comment text, which would be converted into an attached image automatically. An example would be "嘟嘟http://t.cn/RtCfXI1", which would be converted into "嘟嘟" with [this image](http://ww3.sinaimg.cn/bmiddle/005Hl0D7gw1f6mqksxcggj30k00k0abe.jpg) attached.

  However, as far as I can tell, the only way to get ahold of a link like that is to post a comment with the desired image in the first place... And I couldn't even do that with the web interface. When I tried (on Jan 27, 2017), there was a photo button alongside the emoji button in the comment composer, but unlike the emoji button, it was grayed out. Not sure if it was a VIP-only feature or what. I did know I could accomplish that in the iOS client, but based on the shitty track records of Chinese Internet companies, I did not trust the app enough to grant it access to my photos.

  That's all I can say about commenting with images. Basically, if you're dedicated enough, just post the image in a comment beforehand, grab the photo.weibo.com link, shorten it and include the URL in your comment text.

  Lesson from this episode: shitty API sucks. Hardly a surprise.

## License

Copyright (c) 2017 Z. Wang <fanaticscripter@gmail.com>

This work is free. You can redistribute it and/or modify it under the terms of the Do What The Fuck You Want To Public License, Version 2, as published by Sam Hocevar.

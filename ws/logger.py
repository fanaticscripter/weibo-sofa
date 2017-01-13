#!/usr/bin/env python3

import logging

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)

logger = logging.getLogger()

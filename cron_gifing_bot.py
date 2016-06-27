#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time

from keys import GIF_DIR

ONE_WEEK = 60 * 60 * 24 * 7


for f in os.listdir(GIF_DIR):
    if os.path.isfile(f) and time.time() - os.path.getctime(f) > ONE_WEEK:
        os.remove(f)

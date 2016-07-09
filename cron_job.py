#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time

from keys import GIF_DIR

ONE_WEEK = 60 * 60 * 24 * 7

os.chdir(GIF_DIR)

print("There are currently {} GIFs on the system".format(str(len(files))))
[os.remove(f) for f in os.listdir(GIF_DIR) if time.time() - os.path.getctime(f) > ONE_WEEK and os.path.isfile(f)]
print("After cleaning there are {} GIFs on the system".format(str(len(os.listdir(GIF_DIR)))))

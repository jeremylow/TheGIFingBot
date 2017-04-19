#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jeremy Low
# License: MIT
from __future__ import print_function

import json
import logging
import logging.config

import os
from os import getpid, remove
from os.path import abspath, basename, dirname, splitext, join, realpath

import re
import shutil
import subprocess

import requests
import twitter

from gifing_bot import keys
from gifing_bot.utils import random_string


with open('bot_supervisord.pid', 'w+') as pidfile:
    pidfile.write(str(getpid()))

BASE_DIR = dirname(abspath(__file__))
logger = logging.getLogger(__name__)


def setup_logging(default_path='conf/logging_config.json',
                  default_level=logging.INFO,
                  env_key='LOG_CFG'):
    """Setup logging configuration."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def save_video(video_url):
    """Saves a video file to the file system.

    Args:
        video_url (str): URL of the MP4 to save to the file system.
    Returns:
        Filename (not path) of saved video as a string.
    """

    logger.debug("Saving video", )
    req = requests.get(video_url, stream=True)
    video_name = "{0}.mp4".format(random_string())
    with open(video_name, 'wb') as video_file:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)
                video_file.flush()
    return video_name


def frames_to_gif(mp4):
    """Convert video to GIF.

    Args:
        folder_name (str): Name of the folder containing all the frames
        extracted from the original video.
    Returns:
        Full path of the newly-created GIF on the file system.
    """

    gif = splitext(basename(mp4))[0] + '.gif'

    cmd = "{0}/mp4_to_gif.sh {1} {2}".format(BASE_DIR, mp4, gif)
    subprocess.call(cmd, shell=True)

    gif_path = realpath(gif)
    remove(mp4)
    return gif_path


def upload_gif(gif):
    """Move GIF over to hosting site path.

    Args:
        gif (str): path to the GIF file.
    Returns:
        URL of GIF.
    """

    moved_gif = shutil.move(gif, keys.GIF_DIR)
    gif_name, _ = splitext(basename(moved_gif))
    return "https://iseverythingstilltheworst.com/gifs/{0}".format(gif_name)


def send_dm(api, sender_id=None, msg=None):
    """Sends a message to the user.

    Args:
        sender_id (int): Twitter ID of the sender of the Direct
            Message (i.e., the person that requested the GIF be made).
        msg (str): Direct Message to send back to the user.
    Returns:
        True
    """
    api.send_direct_message(user_id=sender_id, text=msg)
    return True


def on_event(api, event):
    """ Auto follow back """

    # Exclude events that originate with us.
    if event.source['id'] in [4012966701, 3206731269]:
        return True

    try:
        if event.event == 'follow':
            follower = event.source['id']
            api.CreateFriendship(user_id=follower)
            logger.info("Followed {0}".format(follower))
        else:
            return True
    except:
        return True

def parse_sender(tweet):
    """Get sender id or None if not found."""
    logger.debug(tweet)
    try:
        sender_id = tweet.sender.id
        logging.info("Sender: {0}".format(sender_id))
    except Exception as e:
        logger.critical(e)
        return None

    # Check to see if TheGIFingBot is the sender.
    # If so, pass & don't do anything.
    if sender_id in [4012966701, 3206731269]:
        return None

    return sender_id


def get_shared_tweet(tweet):
    """Get status_id of tweet in DM.

    Check to make sure there's an attached tweet. The regex
    looks for text along the lines of status/12437385203,
    which should be the linked tweet.
    """
    logger.debug(tweet._json)
    shared_tweet = tweet._json['entities']['urls'][0]['expanded_url']
    match = re.search('status\/(\d+)', shared_tweet)
    if match:
        shared_id = match.groups()[0]
    return int(shared_id)


def on_direct_message(api, tweet):
    dm = twitter.models.DirectMessage.NewFromJsonDict(tweet)
    sender = parse_sender(dm)

    if not sender:
        return

    shared_id = get_shared_tweet(tweet)

    if shared_id:
        original_tweet = api.GetStatus(shared_id)
    else:
        send_dm(sender_id=sender, msg=keys.MGS['need_shared'])
        return

    # Next check to make sure that the original tweet had a GIF in it.
    # At the moment, it seems you can only attach one GIF. This *should*
    # take care of the possibility that you can attach more later.
    gifs = [m for m in original_tweet.media if m.type == 'animated_gif']

    if not gifs:
        send_dm(sender_id=sender, msg=keys.MGS['no_gif'])
        return

    # Yay, we're actually doing this!
    for gif in gifs:
        try:
            video = save_video(gif)
            converted_gif = frames_to_gif(video)
            url = upload_gif(converted_gif)
            msg = "I am good bot!! I made you a GIF: {}".format(url)
            send_dm(api=api, sender_id=sender, msg=msg)
        except Exception as e:
            logger.error(e)
    return


def main():
    gb_keys = keys.KEYS['prod_keys']

    api = twitter.Api(gb_keys['CONSUMER_KEY'],
                      gb_keys['CONSUMER_SECRET'],
                      gb_keys['ACCESS_KEY'],
                      gb_keys['ACCESS_SECRET'],
                      tweet_mode='extended')

    for line in api.GetUserStream():
        if 'event' in line.keys():
            on_event(api, line)
        elif 'sender_id' in line.keys():
            on_direct_message(api, line)


if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger()
    logger.info("Initialized GifingBot")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLater, alligator\n\n")

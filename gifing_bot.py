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
import tweepy

import keys

from utils import (
    post_slack,
    random_string)

with open('bot_supervisord.pid', 'w+') as pidfile:
    pidfile.write(str(getpid()))


BASE_DIR = dirname(abspath(__file__))


def setup_logging(default_path='conf/logging_config.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration

    """
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


class DMListener(tweepy.StreamListener):

    @staticmethod
    def _get_api():
        """Get an Tweepy API instance

        Args:
            none
        Returns:
            tweepy.api instance.
        """
        gb_keys = keys.KEYS[os.getenv('GBKEYS')]
        # logger.debug("Getting api with keys {0}".format(", ".join([gb_keys.CONSUMER_KEY,gb_keys.CONSUMER_SECRET,gb_keys.ACCESS_KEY,gb_keys.ACCESS_SECRET])))
        auth = tweepy.OAuthHandler(
            gb_keys['CONSUMER_KEY'],
            gb_keys['CONSUMER_SECRET'])
        auth.set_access_token(gb_keys['ACCESS_KEY'], gb_keys['ACCESS_SECRET'])
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def parse_entities(extended_entities):
        logger.debug("Parsing extended entities")
        logger.debug(extended_entities)

        gifs = []

        if not extended_entities:
            logger.info("Couldn't find extended entities:\n\n{}".format(original_tweet))

        else:
            for media in extended_entities['media']:
                if media.get('type') == 'animated_gif':
                    gifs.append(media['video_info']['variants'][0]['url'])
                elif media.get('type') == 'video':
                    variants = media['video_info']['variants']
                    videos = []
                    for variant in variants:
                        if variant['content_type'] == 'video/mp4':
                            videos.append(variant)
                    video = sorted(videos, key=lambda video: videos[0]['bitrate'])[-1]
                    gifs.append(video['url'])
        return gifs

    def send_dm(self, sender_id=None, msg=None):
        """Sends a message to the user.

        Args:
            sender_id (int): Twitter ID of the sender of the Direct Message (i.e.,
                the person that requested the GIF be made).
            msg (str): Direct Message to send back to the user.
        Returns:
            True
        """
        self.api.send_direct_message(user_id=sender_id, text=msg)

        return True

    def on_connect(self):
        self.api = self._get_api()
        logger.debug(self.api)
        logger.info('Connected to Twitter. YAY!')

    def on_event(self, event):
        """ Auto follow back """

        # Exclude events that originate with us.
        if event.source['id_str'] == str(4012966701) or event.source['id_str'] == str(3206731269):
            return True

        try:
            if event.event == 'follow':
                follower = event.source['id_str']
                self.api.create_friendship(user_id=follower)
                logger.info("Followed {0}".format(follower))
            else:
                return True
        except:
            return True

    def on_direct_message(self, status):
        try:
            sender = status.direct_message['sender']['id']
        except Exception as e:
            logger.critical(e)
            return True

        logging.info("Sender: {0}".format(sender))
        # Check to see if TheGIFingBot is the sender. If so, pass & don't do
        # anything.
        if sender == 4012966701 or sender == 3206731269:
            return True
        dm = status._json
        logging.debug(dm)

        # Check to make sure there's an attached tweet. The regex looks for text along
        # the lines of status/12437385203, which should be the linked tweet.
        try:
            shared_tweet = dm['direct_message']['entities']['urls'][0]['expanded_url']
            match = re.search('status\/(\d+)', shared_tweet)
            if match:
                shared_id = match.groups()[0]
        except Exception as e:
            logger.warning(e)
            self.send_dm(sender_id=sender, msg=keys.MGS['need_shared'])
            return True

        if shared_id:
            original_tweet = self.api.get_status(shared_id)._json
        else:
            return True

        # Next check to make sure that the original tweet had a GIF in it.
        # At the moment, it seems you can only attach one GIF. This *should*
        # take care of the possibility that you can attach more later.
        extended_entities = original_tweet.get('extended_entities', None)
        gifs = self.parse_entities(extended_entities)

        if not gifs:
            self.send_dm(sender_id=sender, msg=keys.MGS['no_gif'])
            return True

        # Yay, we're actually doing this!
        for gif in gifs:
            try:
                video = self.save_video(gif)
                converted_gif = self.frames_to_gif(video)
                url = self.upload_gif(converted_gif)
                msg = "I am good bot!! I made you a GIF: {}".format(url)
                self.send_dm(sender_id=sender, msg=msg)
            except Exception as e:
                logger.error(e)
                post_slack(msg=e)
        return True


def main():
    logger.debug("Running main() using {0}".format(os.getenv('GBKEYS')))
    gb_keys = keys.KEYS[os.getenv('GBKEYS')]

    auth = tweepy.OAuthHandler(
        gb_keys['CONSUMER_KEY'],
        gb_keys['CONSUMER_SECRET'])
    auth.set_access_token(gb_keys['ACCESS_KEY'], gb_keys['ACCESS_SECRET'])

    stream = tweepy.Stream(auth, DMListener())
    stream.userstream()


if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger()
    logger.info("Initialized GifingBot")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLater, alligator\n\n")

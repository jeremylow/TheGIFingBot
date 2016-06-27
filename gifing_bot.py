from __future__ import print_function

import logging
import logging.handlers
from os import getpid, remove
from os.path import abspath, basename, dirname, splitext, join, realpath
import re
import shutil
import subprocess

import requests
import tweepy
from pyshk.api import Api

import keys

from utils import (
    now,
    post_slack,
    random_string)

with open('bot_supervisord.pid', 'w') as pidfile:
    pidfile.write(str(getpid()))


BASE_DIR = dirname(abspath(__file__))
LOGFILE = join(BASE_DIR, 'GifingBot.log')

logger = logging.getLogger('GifingBot')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOGFILE,
                                               maxBytes=1048576,
                                               backupCount=5)
logger.addHandler(handler)
logger.debug("{0}: Initialized Gifing Bot".format(now()))


class DMListener(tweepy.StreamListener):

    @staticmethod
    def _get_api():
        auth = tweepy.OAuthHandler(
            keys.TEST_CONSUMER_KEY,
            keys.TEST_CONSUMER_SECRET)
        auth.set_access_token(keys.TEST_ACCESS_KEY, keys.TEST_ACCESS_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api

    @staticmethod
    def _get_mlkshk_api():
        mlkshk_api = Api(
            keys.MLKSHK_CLIENT_KEY,
            keys.MLKSHK_CLIENT_SECRET,
            keys.MLKSHK_ACCESS_TOKEN,
            keys.MLKSHK_ACCESS_SECRET)
        return mlkshk_api

    @staticmethod
    def save_video(video_url):
            """
            Saves a video file to the file system.

            Args:
                video_url (str): URL of the MP4 to save to the file system.

            Returns:
                Filename (not path) of saved video as a string.
            """

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
        """
        Using ffmpeg, bundle, for lack of a better word, all the frames in the
        specified folder into a GIF.

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
        return gif_path

    @staticmethod
    def delete_tmp_files_from_system(video, gif):
        try:
            remove(video)
            remove(gif)
        except:
            post_slack('Files not deleted: video: {0}, gif: {1}'.format(video, gif))
        return False

    def upload_gif(self, gif):
        """
        Upload the new gif to Imgur

        Args:
            gif (str): path to the GIF file.

        Returns:
            Response from Imgur, which will contain some information, most
            importantly the link to the uploaded GIF.

        """
        moved_gif = shutil.move(gif, keys.GIF_DIR)
        gif_name = basename(moved_gif)
        return "https://iseverythingstilltheworst.com/gifs/{0}".format(gif_name)

    def send_error_msg(self, sender_id=None, msg=None):
        """
        Args:
            sender_id (int): Twitter ID of the sender of the Direct Message (i.e.,
                the person that requested the GIF be made).
            msg (str): Direct Message to send back to the requestor explaining(ish)
                what went wrong.
        Returns:
            True

        """
        self.api.send_direct_message(user_id=sender_id, text=msg)
        post_slack('Encountered an error:\n{0}\n{1}'.format(sender_id, msg))
        return True

    def send_success_gif(self, sender_id=None, gif=None):
        """
        Args:
            sender_id (int): Twitter ID of the sender of the Direct Message
                (the person that requested the GIF be made).
            gif (str): URL of the MP4 to be converted to a GIF (this is slightly
                backwards).
        Returns:
            True

        """
        post_slack("Making a GIF!")

        saved_video = self.save_video(gif)
        gif_path = self.frames_to_gif(saved_video)

        try:
            uploaded_image = self.upload_gif(gif_path)
            text = "I am good bot!! I made you a GIF: {0} !".format(uploaded_image)
            self.api.send_direct_message(user_id=sender_id, text=text)

        except Exception as e:
            post_slack(e)
        return True

    def on_connect(self):
        self.api = self._get_api()
        self.mlkshk_api = self._get_mlkshk_api()
        print('Connected YAY!')

    def on_status(self, status):
        pass

    def on_event(self, event):
        """ Auto follow back """

        # Exclude events that originate with us.
        if event.source['id_str'] == str(4012966701) or event.source['id_str'] == str(3206731269):
            return True

        try:
            if event.event == 'follow':
                follower = event.source['id_str']
                self.api.create_friendship(user_id=follower)
                logger.debug("{0}: Followed {1}".format(now(), follower))
            else:
                return True
        except:
            return True

    def on_direct_message(self, status):
        try:
            sender = status.direct_message['sender']['id']
        except Exception as e:
            logger.debug("{0}: Couldn't find sender. {1}".format(now(), e))
            return True

        # Check to see if TheGIFingBot is the sender. If so, pass & don't do
        # anything.
        print(sender)
        if sender == 4012966701 or sender == 3206731269:
            return True
        dm = status._json
        print(dm)

        # Check to make sure there's an attached tweet. The regex looks for
        # text along the lines of status/12437385203, which should be the
        # linked tweet.
        try:
            shared_tweet = dm['direct_message']['entities']['urls'][0]['expanded_url']
            match = re.search('status\/(\d+)', shared_tweet)
            if match:
                shared_id = match.groups()[0]
        except Exception as e:
            logger.debug("{0}: Exception occurred: {1}".format(now(), e))
            self.send_error_msg(sender_id=sender, msg=keys.MGS['need_shared'])
            return True

        if shared_id:
            original_tweet = self.api.get_status(shared_id)._json
        else:
            return True

        # Next check to make sure that the original tweet had a GIF in it.
        # At the moment, it seems you can only attach one GIF. This *should*
        # take care of the possibility that you can attach more later.
        gifs = []

        extended_entities = original_tweet.get('extended_entities', None)

        if not extended_entities:
            logger.debug("{0}: Could not find extended_entities".format(now()))
            self.send_error_msg(sender_id=sender, msg=keys.MGS['no_gif'])
            return True
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
                    video = sorted(
                        videos, key=lambda video: videos[0]['bitrate']
                    )[-1]
                    gifs.append(video['url'])

        if not gifs:
            self.send_error_msg(sender_id=sender, msg=keys.MGS['no_gif'])
            return True

        # Yay, we're actually doing this!
        for gif in gifs:
            try:
                self.send_success_gif(sender_id=sender, gif=gif)
            except Exception as e:
                post_slack(msg=e)
        return True


def main():
    auth = tweepy.OAuthHandler(
        keys.TEST_CONSUMER_KEY,
        keys.TEST_CONSUMER_SECRET)
    auth.set_access_token(keys.TEST_ACCESS_KEY, keys.TEST_ACCESS_SECRET)

    stream = tweepy.Stream(auth, DMListener())
    stream.userstream()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLater, alligator\n\n")

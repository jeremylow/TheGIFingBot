from __future__ import print_function

import datetime
import json
import logging
import logging.handlers
from os.path import abspath, dirname, join
import re
import requests

import tweepy

import keys

from gifing_bot_tasks import (
    send_success_gif,
    send_error_msg,
)

BASE_DIR = dirname(abspath(__file__))
LOGFILE = join(BASE_DIR, 'GifingBot.log')


def now():
    return datetime.datetime.utcnow().isoformat()

logger = logging.getLogger('GifingBot')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOGFILE,
                                               maxBytes=1048576,
                                               backupCount=5)
logger.addHandler(handler)
logger.debug("{0}: Initialized Gifing Bot".format(now()))


def post_slack(msg):
    payload = {'text': msg}
    try:
        requests.post(
            keys.SLACK_URL,
            json.dumps(payload),
            headers={'content-type': 'application/json'})
    except Exception as e:
        logger.debug("{0}: {1}".format(now(), e))


class DMListener(tweepy.StreamListener):

    def _get_api(self):
        auth = tweepy.OAuthHandler(
            keys.CONSUMER_KEY,
            keys.CONSUMER_SECRET)
        auth.set_access_token(keys.ACCESS_KEY, keys.ACCESS_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api

    def on_connect(self):
        self.api = self._get_api()
        print('Connected YAY!')

    def on_status(self, status):
        pass

    def on_event(self, event):
        """ Auto follow back """

        # Exclude events that originate with us.
        if event.source['id_str'] == str(3206731269):
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
        if sender == 3206731269:
            return True
        dm = status._json

        # Check to make sure there's an attached tweet. The regex looks for
        # text along the lines of status/12437385203, which should be the
        # linked tweet.
        try:
            shared_tweet = dm['direct_message']['entities']['urls'][0]['expanded_url']
            match = re.search('status\/(\d+)', shared_tweet)
            if match:
                shared_id = match.groups()[0]
        except Exception as e:
            logger.debug("{0}: Key error. {1}".format(now(), e))
            send_error_msg(sender_id=sender, msg=keys.MGS['unknown'])
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
            send_error_msg.apply_async(
                args=[sender, keys.MGS['no_gif']],
                queue='gifing_bot',
                routing_key='gifing_bot')
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
            send_error_msg.apply_async(
                args=[sender, keys.MGS['no_gif']],
                queue='gifing_bot',
                routing_key='gifing_bot')
            return True

        # Yay, we're actually doing this!
        for gif in gifs:
            try:
                send_success_gif.apply_async(
                    args=[sender, gif],
                    queue='gifing_bot',
                    routing_key='gifing_bot')
            except Exception as e:
                post_slack(msg=e)
                send_error_msg.apply_async(
                    args=[sender, keys.MGS['unknown']],
                    queue='gifing_bot',
                    routing_key='gifing_bot')
        return True


def main():
    post_slack(msg="Connected!")
    auth = tweepy.OAuthHandler(
        keys.CONSUMER_KEY,
        keys.CONSUMER_SECRET)
    auth.set_access_token(keys.ACCESS_KEY, keys.ACCESS_SECRET)

    stream = tweepy.Stream(auth, DMListener())
    stream.userstream()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLater, alligator\n\n")

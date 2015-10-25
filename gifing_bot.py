from __future__ import print_function

import tweepy

import gb_config as gb_config

from gifing_bot_tasks import (
    send_success_gif,
    send_error_msg,
)


class DMListener(tweepy.StreamListener):

    def _get_api(self):
        auth = tweepy.OAuthHandler(
            gb_config.CONSUMER_KEY,
            gb_config.CONSUMER_SECRET)
        auth.set_access_token(gb_config.ACCESS_KEY, gb_config.ACCESS_SECRET)
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
                self.api.create_friendship(
                    user_id=event.source['id_str'])

            # Not sure that this works the way I think it works... Yeah, it
            # doesn't. Twitter doesn't have an unfollow event. Saved here for
            # posterity.

            # elif event.event == 'unfollow':
            #     self.api.destroy_friendship(
            #         user_id=event.source['id_str'])

            else:
                return True
        except:
            return True

    def on_direct_message(self, status):
        try:
            sender = status.direct_message['sender']['id']
        except:
            print("Could not determine sender")
            return True

        # Check to see if TheGIFingBot is the sender. If so, pass & don't do
        # anything.
        if sender == 3206731269:
            return True
        dm = status._json

        # Check to make sure there's an attached tweet.
        try:
            shared_tweet = dm[
                'direct_message']['entities']['urls'][0]['expanded_url']
            shared_tweet_status_id = shared_tweet.split('/')[-1]

        except Exception as e:
            print(e)
            # Send back a DM that something went wrong.
            send_error_msg(sender_id=sender, msg=gb_config.MGS['unknown'])
            return True

        original_tweet = self.api.get_status(shared_tweet_status_id)._json

        # Next check to make sure that the original tweet had a GIF in it.
        # At the moment, it seems you can only attach one GIF. This *should*
        # take care of the possibility that you can attach more later.
        gifs = []
        if 'extended_entities' not in original_tweet.keys():
            send_error_msg.apply_async(
                args=[sender, gb_config.MGS['no_gif']],
                queue='gifing_bot',
                routing_key='gifing_bot')
            return True

        else:
            for media in original_tweet['extended_entities']['media']:
                if media['type'] == 'animated_gif':
                    gifs.append(media['video_info']['variants'][0]['url'])
                elif media['type'] == 'video':
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
                args=[sender, gb_config.MGS['no_gif']],
                queue='gifing_bot',
                routing_key='gifing_bot')
            return True

        # Yay, we're actually doing this!
        for gif in gifs:
            send_success_gif.apply_async(
                args=[sender, gif],
                queue='gifing_bot',
                routing_key='gifing_bot')
        return True


def main():
    auth = tweepy.OAuthHandler(
        gb_config.CONSUMER_KEY,
        gb_config.CONSUMER_SECRET)
    auth.set_access_token(gb_config.ACCESS_KEY, gb_config.ACCESS_SECRET)
    api = tweepy.API(auth)

    stream = tweepy.Stream(auth, DMListener())
    stream.userstream()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLater, alligator\n\n")

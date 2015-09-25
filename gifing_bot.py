from __future__ import print_function

import os
import requests
import subprocess
import shlex
import shutil

# Working with threads
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
    
from threading import Thread
import multiprocessing

import random
from hashlib import sha1

import tweepy
from imgurpython import ImgurClient

import gb_config as gb_config


conversion_queue = Queue()
CPU_COUNT = multiprocessing.cpu_count()


def random_string(n=15):
    return sha1(str(random.random()).encode('utf-8')).hexdigest()[:n]


def save_video(video_url):
    req = requests.get(video_url, stream=True)
    video_name = "{}.mp4".format(random_string())
    with open(video_name, 'wb') as video_file:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)
                video_file.flush()
    # print("Saved Video File as {}".format(video_name))
    return video_name


def video_to_frames(video_name):
    temp_folder = video_name[:-4]
    if os.path.exists(temp_folder):
        os.rmdir(temp_folder)
    os.mkdir(temp_folder)

    command = (
        'ffmpeg '
        '-i {video} '
        '-vf scale="500:-1" '
        '-r 10 '
        '{folder}/frames%03d.png'.format(
            video=video_name,
            folder=temp_folder))
    with open(os.devnull) as FNULL:
        subprocess.call(shlex.split(command), stdout=FNULL, stderr=FNULL)
    return temp_folder


def frames_to_gif(folder_name):
    command = "convert -delay 10 -loop 0 {}/frames*.png {}/output.gif".format(
        folder_name,
        folder_name)
    subprocess.check_output(shlex.split(command))
    gif_path = os.path.realpath("{0}/output.gif".format(folder_name))
    return gif_path


def upload_to_imgur(gif):
    uploaded_image = imgur_client.upload_from_path(
        gif,
        config=gb_config.IMGUR_UPLOAD_CONFIG,
        anon=False)
    return uploaded_image


def delete_tmp_files_from_system(video, frames_folder):
    try:
        os.remove(video)
        shutil.rmtree(frames_folder)
        print("Something went right, files deleted")
    except:
        print("Something went wrong, files not deleted")
    return


def full_conversion(video_name):
    saved_video = save_video(video_name)
    frames_folder = video_to_frames(saved_video)
    gif_path = frames_to_gif(frames_folder)
    uploaded_image = upload_to_imgur(gif_path)
    print("I WORKED I AM A GOOD BOT")
    delete_tmp_files_from_system(saved_video, frames_folder)
    return uploaded_image


class DMListener(tweepy.StreamListener):

    def on_connect(self):
        print('Connected YAY!')

    def on_status(self, status):
        pass

    def on_direct_message(self, status):
        try:
            sender = status.direct_message['sender']['id']
        except:
            print("Could not determine sender")
            return

        # if status.text == "help":
        #    api.send_direct_message(sender, config.MSG['instructions'])

        # Check to see if TheGIFingBot is the sender
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
            api.send_direct_message(
                user_id=sender,
                text=gb_config.MGS['unknown'])
            return True

        original_tweet = api.get_status(shared_tweet_status_id)._json

        # Next check to make sure that the original tweet had a GIF in it.
        # At the moment, it seems you can only attach one GIF. This should take
        # care of the possibility that you can attach more later.
        gifs = []
        if 'extended_entities' not in original_tweet.keys():
            api.send_direct_message(
                user_id=sender,
                text=gb_config.MGS['no_gif'])
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
            api.send_direct_message(
                user_id=sender,
                text=gb_config.MGS['no_gif'])
            return True

        # Yay, we're actually doing this!
        for gif in gifs:
            uploaded_image = full_conversion(gif)
            gif_link = uploaded_image['link']

            # Success!
            text = "I am good bot!! I made you a GIF: {}!!!".format(gif_link)

            api.send_direct_message(user_id=sender, text=text)
        return True


def main():
    imgur_client = ImgurClient(
        gb_config.IMGUR_CLIENT_ID,
        gb_config.IMGUR_CLIENT_SECRET,
        gb_config.IMGUR_ACCESS_TOKEN,
        gb_config.IMGUR_REFRESH_TOKEN)

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

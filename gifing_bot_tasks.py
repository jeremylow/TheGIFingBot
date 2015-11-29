from __future__ import print_function

import os
from os.path import abspath, basename, dirname, splitext, join
import datetime
from hashlib import sha1
import json
import logging
import logging.handlers
import random
import requests
import subprocess

import tweepy
from imgurpython import ImgurClient
from imgurpython.client import ImgurClientError

from celery_app import app

import keys

BASE_DIR = dirname(abspath(__file__))
LOGFILE = join(BASE_DIR, 'GifingBot.log')

with open('bot_worker.pid', 'w') as pidfile:
    pidfile.write(str(os.getpid()))


def now():
    return datetime.datetime.utcnow().isoformat()

logger = logging.getLogger('GifingBot')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    LOGFILE,
    maxBytes=1024*1024,
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
    except:
        return True


def _get_api():
    auth = tweepy.OAuthHandler(
        keys.CONSUMER_KEY,
        keys.CONSUMER_SECRET)
    auth.set_access_token(keys.ACCESS_KEY, keys.ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api


def _get_imgur_client():
    imgur_client = ImgurClient(
        keys.IMGUR_CLIENT_ID,
        keys.IMGUR_CLIENT_SECRET,
        keys.IMGUR_ACCESS_TOKEN,
        keys.IMGUR_REFRESH_TOKEN)
    return imgur_client


def random_string(n=15):
    return sha1(str(random.random()).encode('utf-8')).hexdigest()[:n]


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
    print("Saved Video File as {0}".format(video_name))
    return video_name


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

    gif_path = os.path.realpath(gif)
    return gif_path


def upload_to_imgur(gif):
    """
    Upload the new gif to Imgur

    Args:
        gif (str): path to the GIF file.

    Returns:
        Response from Imgur, which will contain some information, most
        importantly the link to the uploaded GIF.

    """
    imgur_client = _get_imgur_client()
    uploaded_image = imgur_client.upload_from_path(
        gif,
        config=keys.IMGUR_UPLOAD_CONFIG,
        anon=False)
    return uploaded_image


def delete_tmp_files_from_system(video, gif):
    try:
        os.remove(video)
        os.remove(gif)
    except:
        post_slack('Some files were not deleted: video: {}, gif: {}'.format(
            video,
            gif))
    return


def full_conversion(video_name):
    saved_video = save_video(video_name)
    gif_path = frames_to_gif(saved_video)

    uploaded_image = upload_to_imgur(gif_path)
    delete_tmp_files_from_system(saved_video, gif_path)
    return uploaded_image


@app.task
def send_success_gif(sender_id=None, gif=None):
    """
    Args:
        sender_id (int): Twitter ID of the sender of the Direct Message (i.e.,
            the person that requested the GIF be made).
        gif (str): URL of the MP4 to be converted to a GIF (this is slightly
            backwards).

    Returns:
        True

    """
    post_slack("Making a GIF!")
    api = _get_api()

    saved_video = save_video(gif)
    gif_path = frames_to_gif(saved_video)

    try:
        uploaded_image = upload_to_imgur(gif_path)
    except ImgurClientError as e:
        send_error_msg.apply_async(
            args=[sender_id, keys.MGS['ImgurError']],
            queue='gifing_bot',
            routing_key='gifing_bot')
        post_slack(e)

    uploaded_image = full_conversion(gif)
    text = "I am good bot!! I made you a GIF: {0} !".format(
        uploaded_image['link'])
    api.send_direct_message(user_id=sender_id, text=text)
    post_slack("I made a GIF!!!")

    delete_tmp_files_from_system(saved_video, gif_path)

    return True


@app.task
def send_error_msg(sender_id=None, msg=None):
    """
    Args:
        sender_id (int): Twitter ID of the sender of the Direct Message (i.e.,
            the person that requested the GIF be made).
        msg (str): Direct Message to send back to the requestor explaining(ish)
            what went wrong.

    Returns:
        True

    """
    api = _get_api()
    api.send_direct_message(
        user_id=sender_id,
        text=msg)
    post_slack('Encountered an error:\n{0}\n{1}'.format(
        sender_id,
        msg))
    return True

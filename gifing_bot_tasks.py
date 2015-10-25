import os
import requests
import subprocess
import shlex
from shutil import rmtree

import random
from hashlib import sha1

import tweepy
from imgurpython import ImgurClient
from imgurpython.client import ImgurClientError

from celery_app import app

import gb_config


def _get_api():
    auth = tweepy.OAuthHandler(
        gb_config.CONSUMER_KEY,
        gb_config.CONSUMER_SECRET)
    auth.set_access_token(gb_config.ACCESS_KEY, gb_config.ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api


def _get_imgur_client():
    imgur_client = ImgurClient(
        gb_config.IMGUR_CLIENT_ID,
        gb_config.IMGUR_CLIENT_SECRET,
        gb_config.IMGUR_ACCESS_TOKEN,
        gb_config.IMGUR_REFRESH_TOKEN)
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
    video_name = "{}.mp4".format(random_string())
    with open(video_name, 'wb') as video_file:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)
                video_file.flush()
    print("Saved Video File as {}".format(video_name))
    return video_name


def video_to_frames(video_name):
    """
    Extracts all frames from a video file and saves them to the file system
    under the folder name of the originally saved file.

    Args:
        video_name (str): Name of the saved video from which to extract
        the individual frames.

    Returns:
        Name of folder into which the frames were saved.

    """
    temp_folder = video_name[:-4]
    if os.path.exists(temp_folder):
        os.rmdir(temp_folder)
    os.mkdir(temp_folder)
    cmd = 'ffmpeg -i {v} -vf scale="500:-1" -r 10  {f}/frames%03d.png'.format(
        v=video_name,
        f=temp_folder)
    subprocess.call(shlex.split(cmd))
    return temp_folder


def frames_to_gif(folder_name):
    """
    Using imagemagik, bundle, for lack of a better word, all the frames in the
    specified folder into a GIF.

    Args:
        folder_name (str): Name of the folder containing all the frames
        extracted from the original video.

    Returns:
        Full path of the newly-created GIF on the file system.

    """
    cmd = "convert -delay 10 -loop 0 {0}/frames*.png {1}/output.gif".format(
        folder_name, folder_name)
    subprocess.call(shlex.split(cmd))
    gif_path = os.path.realpath("{0}/output.gif".format(folder_name))
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
    try:
        uploaded_image = imgur_client.upload_from_path(
            gif,
            config=gb_config.IMGUR_UPLOAD_CONFIG,
            anon=False)
    except ImgurClientError as e:
        print(e)
    return uploaded_image


def delete_tmp_files_from_system(video, frames_folder):
    try:
        os.remove(video)
        rmtree(frames_folder)
        print("Something went right, files deleted")
    except:
        print("Something went wrong, files not deleted")
    return


def full_conversion(video_name):
    saved_video = save_video(video_name)
    frames_folder = video_to_frames(saved_video)
    gif_path = frames_to_gif(frames_folder)
    uploaded_image = upload_to_imgur(gif_path)
    delete_tmp_files_from_system(saved_video, frames_folder)
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
    api = _get_api()
    uploaded_image = full_conversion(gif)
    text = "I am good bot!! I made you a GIF: {} !".format(
        uploaded_image['link'])
    api.send_direct_message(user_id=sender_id, text=text)
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
    return True

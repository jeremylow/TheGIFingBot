import os
import requests
import subprocess
import shlex
from shutil import rmtree

import random
from hashlib import sha1

from imgurpython import ImgurClient

CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_KEY = os.environ["ACCESS_KEY"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]

IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
IMGUR_CLIENT_SECRET = os.environ["IMGUR_CLIENT_SECRET"]

IMGUR_ACCESS_TOKEN = os.environ["IMGUR_ACCESS_TOKEN"]
IMGUR_REFRESH_TOKEN = os.environ["IMGUR_REFRESH_TOKEN"]

imgur_client = ImgurClient(
    IMGUR_CLIENT_ID,
    IMGUR_CLIENT_SECRET,
    IMGUR_ACCESS_TOKEN,
    IMGUR_REFRESH_TOKEN)

# Pretty basic for now, but maybe add more info in future.
IMGUR_UPLOAD_CONFIG = {
    'album': 'hWz3K',
}


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
    print("Saved Video File as {}".format(video_name))
    return video_name


def video_to_frames(video_name):
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
    cmd = "convert -delay 10 -loop 0 {0}/frames*.png {1}/output.gif".format(
        folder_name, folder_name)
    subprocess.call(shlex.split(cmd))
    gif_path = os.path.realpath("{0}/output.gif".format(folder_name))
    return gif_path


def upload_to_imgur(gif):
    uploaded_image = imgur_client.upload_from_path(
        gif,
        config=IMGUR_UPLOAD_CONFIG,
        anon=False)
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
    print("I WORKED I AM A GOOD BOT")
    delete_tmp_files_from_system(saved_video, frames_folder)
    return uploaded_image

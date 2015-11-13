import os

MGS = {
    'unknown': "Something went wrong! I'm a bad bot! Sad face!!!!",
    'no_gif': "I looked and looked and I can't find a GIF!",
    'success': "I AM A GOOD BOT!!!",
    'help': (
        'You can ask for help at any time by just DMing the message "help"'),
    'instructions': (
        'Instructions are here: '
        'http://iseverythingstilltheworst.com/the-gifing-bot/'),
    'ImgurError': 'I had a problem uploading your GIF to Imgur! It might be too big. I\'m sorry :( :('
}

CONSUMER_KEY = os.getenv("GB_CONSUMER_KEY", "test")
CONSUMER_SECRET = os.getenv("GB_CONSUMER_SECRET", "test")
ACCESS_KEY = os.getenv("GB_ACCESS_KEY", "test")
ACCESS_SECRET = os.getenv("GB_ACCESS_SECRET", "test")

IMGUR_CLIENT_ID = os.getenv("GB_IMGUR_CLIENT_ID", "test")
IMGUR_CLIENT_SECRET = os.getenv("GB_IMGUR_CLIENT_SECRET", "test")

IMGUR_ACCESS_TOKEN = os.getenv("GB_IMGUR_ACCESS_TOKEN", "test")
IMGUR_REFRESH_TOKEN = os.getenv("GB_IMGUR_REFRESH_TOKEN", "test")

# Pretty basic for now, but maybe add more info in future.
IMGUR_UPLOAD_CONFIG = {
    'album': os.getenv("GB_IMGUR_ALBUM", "test"),
}

SLACK_URL = os.getenv("GB_SLACK_URL", "test")

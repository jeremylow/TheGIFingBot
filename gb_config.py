import os

MGS = {
    'unknown': "Something went wrong! I'm a bad bot! Sad face!!!!",
    'no_gif': "I looked and looked and I can't find a GIF!",
    'success': "I AM A GOOD BOT!!!",
    'help': 'You can ask for help at any time by just DMing the message "help"',
    'instructions': 'Instructions are here: http://iseverythingstilltheworst.com/the-gifing-bot/'
}

CONSUMER_KEY = os.getenv("CONSUMER_KEY", "test")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET", "test")
ACCESS_KEY = os.getenv("ACCESS_KEY", "test")
ACCESS_SECRET = os.getenv("ACCESS_SECRET", "test")

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "test")
IMGUR_CLIENT_SECRET = os.getenv("IMGUR_CLIENT_SECRET", "test")

IMGUR_ACCESS_TOKEN = os.getenv("IMGUR_ACCESS_TOKEN", "test")
IMGUR_REFRESH_TOKEN = os.getenv("IMGUR_REFRESH_TOKEN", "test")

# Pretty basic for now, but maybe add more info in future.
IMGUR_UPLOAD_CONFIG = {
    'album': os.getenv("IMGUR_ALBUM", "test"),
}

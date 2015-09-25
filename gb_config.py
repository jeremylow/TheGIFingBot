import os

MGS = {
    'unknown': "Something went wrong! I'm a bad bot! Sad face!!!!",
    'no_gif': "I looked and looked and I can't find a GIF!",
    'success': "I AM A GOOD BOT!!!",
    'help': 'You can ask for help at any time by just DMing the message "help"',
    'instructions': 'Instructions are here: http://iseverythingstilltheworst.com/the-gifing-bot/'
}

CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_KEY = os.environ["ACCESS_KEY"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]

IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
IMGUR_CLIENT_SECRET = os.environ["IMGUR_CLIENT_SECRET"]

IMGUR_ACCESS_TOKEN = os.environ["IMGUR_ACCESS_TOKEN"]
IMGUR_REFRESH_TOKEN = os.environ["IMGUR_REFRESH_TOKEN"]

# Pretty basic for now, but maybe add more info in future.
IMGUR_UPLOAD_CONFIG = {
    'album': os.environ["IMGUR_ALBUM"],
}

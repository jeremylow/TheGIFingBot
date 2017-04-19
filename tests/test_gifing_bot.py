import json
import re

import twitter
import responses

from gifing_bot import bot


def test_parse_sender():
    with open('test_data/incoming_dm.json', 'r') as f:
        tweet = json.loads(f.read())
    dm = twitter.models.DirectMessage.NewFromJsonDict(tweet)
    sender_id = bot.parse_sender(dm)
    assert sender_id == 1230921831


def test_get_shared_tweet():
    with open('test_data/incoming_dm.json', 'r') as f:
        tweet = json.loads(f.read())
    dm = twitter.models.DirectMessage.NewFromJsonDict(tweet)
    shared_id = bot.get_shared_tweet(dm)
    assert shared_id == 854322543364382720

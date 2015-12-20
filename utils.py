import datetime
from uuid import uuid4
import requests
import json

import keys


def post_slack(msg):
    payload = {'text': msg}
    try:
        requests.post(
            keys.SLACK_URL,
            json.dumps(payload),
            headers={'content-type': 'application/json'})
    except:
        return True


def now():
    return datetime.datetime.utcnow().isoformat()


def random_string(n=15):
    return uuid4().hex[:n]

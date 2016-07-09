import datetime
from random import choice

import requests
import json

import keys


GREEKS = []
OCCUPATIONS = []

for f in ['greek_gods', 'greek_monsters', 'greek_titans']:
    with open('names/{0}.json'.format(f)) as fp:
        GREEKS += json.load(fp)[f]

with open('names/occupations.json') as f:
    OCCUPATIONS = [occ.title().replace(' ', '') for occ in json.load(f)['occupations']]


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


def random_string():
    name = choice(GREEKS) + "The" + choice(OCCUPATIONS)
    return name
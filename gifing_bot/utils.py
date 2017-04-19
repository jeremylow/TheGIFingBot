import datetime
from random import choice

import requests
import json


GREEKS = []
OCCUPATIONS = []

for f in ['greek_gods', 'greek_monsters', 'greek_titans']:
    with open('gifing_bot/names/{0}.json'.format(f)) as fp:
        GREEKS += json.load(fp)[f]

with open('gifing_bot/names/occupations.json') as f:
    OCCUPATIONS = [occ.title().replace(' ', '') for occ in json.load(f)['occupations']]


def random_string():
    name = choice(GREEKS) + "The" + choice(OCCUPATIONS)
    return name

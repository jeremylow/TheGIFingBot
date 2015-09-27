from __future__ import absolute_import

from celery import Celery

# instantiate Celery object
celery = Celery(include=['gifing_bot_tasks'])

# import celery config file
celery.config_from_object('celeryconfig')

if __name__ == '__main__':
    celery.start()

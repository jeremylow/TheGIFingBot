from __future__ import absolute_import
from celery import Celery

# instantiate Celery object
app = Celery(
    'TheGIFingBot',
    broker='amqp://',
    backend='amqp://',
    include=['gifing_bot_tasks'])

# import celery config file
app.config_from_object('celery_config')

if __name__ == '__main__':
    app.start()

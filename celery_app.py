from __future__ import absolute_import
from celery import Celery

from kombu import Exchange, Queue

# instantiate Celery object
app = Celery(
    'TheGIFingBot',
    broker='amqp://',
    backend='amqp://',
    include=['gifing_bot_tasks'])

CELERY_IMPORTS = ('TheGIFingBot.gifing_bot_tasks', )

CELERY_DEFAULT_QUEUE = 'gifing_bot'

CELERY_QUEUES = (
    Queue('gifing_bot', Exchange('gifing_bot'), routing_key='gifing_bot'),
)

CELERY_ROUTES = {
    'gifing_bot_tasks.send_success_gif': {'queue': 'gifing_bot'},
    'gifing_bot_tasks.send_error_msg': {'queue': 'gifing_bot'},
}

CELERY_DEFAULT_QUEUE = 'gifing_bot'

if __name__ == '__main__':
    app.start()

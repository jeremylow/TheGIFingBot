# Config file for our Celery daemon.

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'
CELERY_IMPORTS = ('TheGIFingBot.gifing_bot_tasks', )

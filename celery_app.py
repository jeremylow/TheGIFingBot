from celery import Celery

# instantiate Celery object
app = Celery(include=['gifing_bot_tasks'])

# import celery config file
app.config_from_object('celeryconfig')

if __name__ == '__main__':
    pass

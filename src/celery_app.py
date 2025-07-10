from celery import Celery
from celery.schedules import crontab
from const import DbType
from env import REDIS_HOST

app = Celery('celery_app', broker=REDIS_HOST)
app.conf.update(
    result_backend=REDIS_HOST,
    beat_schedule={
        'update_male_monologues': {
            'task': 'tasks.update_monologues',
            'schedule': crontab(hour='0', minute='10'),
            'args': (DbType.MALE,)
        },
        'update_female_monologues': {
            'task': 'tasks.update_monologues',
            'schedule': crontab(hour='1', minute='10'),
            'args': (DbType.FEMALE,)
        }
    },
    include=['tasks']
)

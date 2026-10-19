import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

celery_app = Celery(
    "geo_gap_probing",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_acks_late=True,
    task_track_started=True,
    imports=("app.probing.tasks",),
    beat_schedule={
        "scheduled-geo-gap-probing": {
            "task": "app.probing.tasks.dispatch_batch",
            "schedule": crontab(
                hour=9,
                minute=0,
                day_of_week="mon",
            ),
            "options": {"queue": "celery"},
        },
    },
    timezone="Asia/Kolkata",
    enable_utc=True,
)
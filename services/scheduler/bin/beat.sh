#!/usr/bin/env bash
python -m celery -A app.main.scheduler beat -S sqlalchemy_celery_beat.schedulers:DatabaseScheduler -l info

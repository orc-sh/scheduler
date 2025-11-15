#!/usr/bin/env bash
python -m celery -A app.main.scheduler worker -E -l info

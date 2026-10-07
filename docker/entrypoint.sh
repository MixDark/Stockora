#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec waitress-serve --listen="${APP_HOST:-0.0.0.0}:${APP_PORT:-7000}" core.wsgi:application

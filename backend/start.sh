#!/usr/bin/env bash
set -o errexit
python manage.py migrate --noinput
python manage.py bootstrap_admin
# Sync worker isi service ke andar chalta hai (free plan ke liye). Alag worker ho to RUN_WORKER=0 karo.
if [ "${RUN_WORKER:-1}" = "1" ]; then
  python manage.py run_sync_worker &
fi
exec gunicorn omnisell_core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 60

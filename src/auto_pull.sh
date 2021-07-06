#!/bin/sh
source ../../venv/bin/activate
git pull
python manage.py migrate
supervisorctl restart supersonic_admin
supervisorctl restart supersonic_bot
exit
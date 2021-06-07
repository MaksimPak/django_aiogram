#!/bin/sh
source ../../venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
supervisorctl restart supersonic_admin
supervisorctl restart supersonic_bot
exit
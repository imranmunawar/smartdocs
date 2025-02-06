#!/bin/bash

set -o errexit -o nounset -o pipefail

python manage.py migrate
python manage.py runserver 0.0.0.0:8000

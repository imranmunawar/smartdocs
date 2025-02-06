#!/bin/bash

# Exit immediately if a command exits with a non-zero status
# set -e

# Run database migrations
python manage.py migrate --settings document_generator.settings_launchflow

# Collect static files
python manage.py collectstatic --noinput --settings document_generator.settings_launchflow

#check deployability
python manage.py check --deploy --settings document_generator.settings_launchflow

#run gunicorn
python manage.py runserver 0.0.0.0:8080 --settings document_generator.settings_launchflow

# Run the Django development server
exec "$@"
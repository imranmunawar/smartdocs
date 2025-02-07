from datetime import datetime

import requests
import re
from ..models import Template
from django.utils import timezone


def get_user_access_levels(role):
    access_levels = ['level-0']
    try:
        if role == 'level-3':
            access_levels.extend(['level-1', 'level-2', 'level-3'])
        elif role == 'level-2':
            access_levels.extend(['level-1', 'level-2'])
        elif role == 'level-1':
            access_levels.append('level-1')
    except requests.RequestException as e:
        print(f"An Exception occurred: {e}")
    return access_levels


def get_subscription_expiration_date(datetime_string):
    return datetime.strptime(datetime_string, '%Y-%m-%d')


def validate_vimeo_link(vimeo_link):
    vimeo_pattern = re.compile(r'https:\/\/.*vimeo\.com.*')
    return bool(vimeo_pattern.match(vimeo_link))


def placeholder_validation(value):
    pattern = r'^\$\{[a-zA-Z0-9_]+\}$'
    return bool(re.match(pattern, value))


def template_modified(template_id):
    try:
        new_template = Template.objects.get(
                    id=template_id)
        new_template.last_modified = timezone.now() 
        new_template.save()
    except Exception as e:
                print('Template not found.')


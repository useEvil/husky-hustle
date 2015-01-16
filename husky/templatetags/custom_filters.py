import re

from django import template
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from datetime import datetime

from husky.helpers import *

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.filter(name='date_format')
def date_format(value, format='%m/%d/%Y @ %I:%M%p'):
    return value.strftime(format)

@register.filter(name='date_format_google')
def date_format_google(value, format='%m/%d/%Y @ %I:%M%p'):
    try:
        value = re.sub('(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.\d{3}(-\d{2}:\d{2})*$', '\\1', value)
        date  = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
    except:
        format = '%m/%d/%Y'
        value  = re.sub('(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}\.\d{3})*(-\d{2}:\d{2})*$', '\\1', value)
        date   = datetime.strptime(value, '%Y-%m-%d')
    return date.strftime(format)

@register.filter(name='goal_reached')
def goal_reached(value):
    if not value: return ''
    percentage = float(value) / settings.MAX_ARROW_HEIGHT
    if percentage > 1:
        return 'display: none;'
    return ''

@register.filter(name='get_facebook')
def get_facebook(object):
    return object.facebook(request.user.id)

@register.filter(name='get_twitter')
def get_twitter(object):
    return object.twitter(request.user.id)

@register.filter(name='prev_photo_id')
def prev_photo_id(object, index=0):
    return prevPhoto(object, index)

@register.filter(name='next_photo_id')
def next_photo_id(object, index=0):
    return nextPhoto(object, index)

@register.filter(name='prev_index')
def prev_index(object, index=0):
    index = int(index) - 1
    try:
        if index >= 0:
            return '?index=%s' % index
    except:
        pass
    return ''

@register.filter(name='next_index')
def next_index(object, index=0):
    index = int(index) + 1
    try:
        if object[index]:
            return '?index=%s' % index
    except:
        pass
    return ''

@register.filter(name='fix_err_msg')
def fix_err_msg(text=None):
    text = str(text)
    text = text.replace('username', 'email address')
#    texts = re.findall('<[^>]+>(.+)</[^>]+>', text)
    return text

@register.filter(name='object_name')
def object_name(object):
    if object.__class__.__name__ == 'Shirt':
        return '%s %s' % (object.type_display(), object.size_display())
    else:
        if object.last_name == 'teacher':
            return '%s for %s' % (object.first_name, object.student.full_name())
        else:
            return object.student.full_name()

import datetime
from django import template
from django.conf import settings
import urllib.parse, hashlib

register = template.Library()

@register.simple_tag
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
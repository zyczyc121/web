import datetime
from django import template
from django.conf import settings
import urllib.parse, hashlib

register = template.Library()


@register.simple_tag
def gravatar_url(email):
    # Set your variables here
    #default_url = settings.SITE_URL + '/media/default-avatar.jpg'
    #rint(default_url)
    default_url = 'http://aftr2015.com/files/images/default-avatar.jpg'
    size = 200

    # construct the url
    gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.encode('utf8').lower()).hexdigest() + "?"
    gravatar_url += urllib.parse.urlencode({'d': default_url, 's': str(size)})
    return gravatar_url

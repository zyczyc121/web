from django.utils.timezone import now
from user.models import UserInfo
import string 

class UserLastvisitMiddleware(object):
    def process_response(self, request, response):
        if hasattr(request, 'user'):
            if request.user.is_authenticated():
            # Update last visit time after request finished processing.
                UserInfo.objects.filter(user=request.user).update(last_visit=now())
        return response

# Create your tests here.

from django.test import TestCase
from user.models import *
from django.contrib.auth.models import *
from django.utils import timezone
from user.util import *
import datetime


class MailTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="npbool", email="npbool_test@163.com", password="123456789")
        info = UserInfo.objects.create(user=user, display_name="NPBOOL", avatar="", status=UserInfo.PENDING)

    def test_activation_mail(self):
        act = UserModification.objects.create(user=User.objects.get(username="npbool"), key="AAAA",
                                              action=UserModification.ACTIVATION,
                                              expire_datetime=timezone.now() + datetime.timedelta(days=3))

        stat, msg = send_activation_mail(act)
        self.assertEqual(stat, True)
        act.delete()

import string
import random
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import get_template
from urllib.parse import urlencode
import smtplib
import logging
from django.utils.translation import ugettext as _

logger = logging.getLogger(__name__)


def random_str(length):
    base = string.hexdigits
    return ''.join([base[random.randint(0, len(base) - 1)] for i in range(length)])

def update_skills(u, submit_set, manager, cls):
    to_remove = []
    for x in manager.all():
        if x.name in submit_set:
            submit_set.remove(x.name)
        else:
            to_remove.append(x)
    manager.remove(*to_remove)
    to_add = [cls.objects.get_or_create(name=name)[0] for name in submit_set]
    manager.add(*to_add)


def send_mail_checked(*args, **kwargs):
    try:
        if send_mail(*args, **kwargs) == 1:
            return True, ""
        else:
            return False, _("Unknown error")
    except smtplib.SMTPRecipientsRenused:
        return False, _("Email doesn't exist")
    except Exception as e:
        logger.error(e)
        return False, _("Unknown error")
    return True, ""


def send_reset_password_mail(target, key):
    send_mail(_("Reset your password"),
              _("Click following link to reset your password:\n")+" %s/user/reset-password?key=%s" % (settings.SITE_URL, key),
              settings.EMAIL_FROM, [target])


def send_activation_mail(activation):
    subject = _("Activate your account")
    url = settings.SITE_URL + reverse("user:activate") + "?" + urlencode({
        'id': activation.id,
        'key': activation.key
    })
    plain_text = _("Visit following link to activate your account. \n") + url
    html_text = _('Click')+' <a href="%s">here</a> ' %url +_('to activate your account. If the link doesn\'t work, ')+_('please copy the following address to your browser. %s') %url
    status, msg = send_mail_checked(subject=subject, message=plain_text, html_message=html_text,
                             from_email=settings.EMAIL_FROM, recipient_list=[activation.user.email])

    return status, msg


def send_mail_template(target, temp_name):
    context = {
        'url': reverse('index'),
        'name': _('User Unknown')
    }
    template = get_template(temp_name)
    html_text = template.render(context)
    title = _("Update")
    plain_text = _("Account update")
    send_mail_checked(subject=title,
                      message=plain_text,
                      html_message=html_text,
                      from_email=settings.EMAIL_FROM, recipient_list=[target])


def send_html_mail(title, target, name):
    plain_text = _("Plain text")
    with open("/Users/npbool/Projects/mailupdate/%s.html" % name, 'r', encoding='utf8') as f:
        html_text = f.read()
    # email = EmailMultiAlternatives("Update", plain, 'npbool_test@163.com', to=[target])
    # email.attach_alternative(html_text, 'text/html')
    # email.send();
    status, msg = send_mail_checked(subject=title,
                                    message=plain_text,
                                    html_message=html_text,
                                    from_email=settings.EMAIL_FROM, recipient_list=[target])
    return status, msg

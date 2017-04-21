from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.utils import ErrorList
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.template import RequestContext
from crispy_forms.utils import render_crispy_form
import datetime
from .models import *
from .forms import *
from .util import *
import ujson as json
from ipware.ip import get_ip
from django.utils.translation import ugettext as _
from competition.util import active_user_count

# Create your views here.
def register(request):
    active_users = request.session.get('active_users', active_user_count())

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            display_name = form.cleaned_data['display_name']
            real_name = form.cleaned_data['real_name']
            organization = form.cleaned_data['organization']

            receive_update = form.cleaned_data['receive_update']

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_active=False
            )
            user_info = UserInfo(user=user,
                                 display_name=display_name,
                                 real_name=real_name,
                                 organization=organization,
                                 status=UserInfo.PENDING,
                                 receive_update=receive_update,
                                 remote_addr=get_ip(request),
                                 )
            activation = UserModification(user=user, key=random_str(64),
                                          expire_datetime=timezone.now() + datetime.timedelta(days=3),
                                          action=UserModification.ACTIVATION)

            user.save()
            user_info.save()
            activation.save()

            send_activation_mail(activation)
            return HttpResponseRedirect(reverse('user:confirm'))

    else:
        form = RegisterForm()
    return render(request, 'user/register.html', {
        'form': form,
        'active_users': active_users,
    })


@require_http_methods(['GET', 'POST'])
def activate(request):
    if request.method == 'GET':
        key = request.GET.get('key', '')
        entry = get_object_or_404(UserModification, action=UserModification.ACTIVATION, key=key)
        entry.user.info.status = UserInfo.ACTIVE
        entry.user.is_active = True

        entry.user.save()
        entry.user.info.save()
        entry.delete()

        messages.success(request, _("Activation complete! You can login now."))
        return HttpResponseRedirect(reverse('user:login'))


@require_http_methods(["GET", 'POST'])
def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is None:
                try:
                    user_attempt = User.objects.get(email=username)
                    user = authenticate(username=user_attempt.username, password=password)
                except User.DoesNotExist:
                    user = None

                if user is None:
                    user = authenticate(username=username, password="data_competition_password_"+password)

            if user is not None:
                if user.info.status == UserInfo.PENDING:
                    activation = get_object_or_404(UserModification, user=user, action=UserModification.ACTIVATION)
                    send_activation_mail(activation)
                    return HttpResponseRedirect(reverse('user:pending'))

                if not form.cleaned_data['remember']:
                    request.session.set_expiry(0)
                django_login(request, user)
                next_url = form.cleaned_data['next']
                if next_url == '':
                    return HttpResponseRedirect(reverse("index"))
                else:
                    return HttpResponseRedirect(next_url)
            else:
                # fall through; render login page
                form.add_error(None, _("Invalid username/email or password"))

    else:
        next = request.GET.get('next', '')

        form = LoginForm(initial={
            'next': next,
        })

    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/login.html', {
        'form': form,
        'active_users': active_users,
    })


@login_required
def profile(request):
    user = request.user
    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/profile.html', {'view_otheruser': user, 'self': True, 'active_users': active_users})


def view_user(request, id):
    u = get_object_or_404(User, pk=id)
    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/profile.html', {'view_otheruser': u, 'self': False, 'active_users': active_users})


@require_http_methods(['POST', 'GET'])
@login_required
def edit_profile(request):
    if request.method == 'GET':
        user_tools = ','.join((tool.name for tool in request.user.tools.all()))
        user_interests = ','.join((interest.name for interest in request.user.interests.all()))

        form = ProfileEditForm(instance=request.user.info, initial={
            'interests': user_interests,
            'tools': user_tools
        })
    else:
        form = ProfileEditForm(request.POST, instance=request.user.info)

        origin_organization = request.user.info.organization
        if form.is_valid():
            form.save()

            now_organization = request.user.info.organization
            if now_organization != origin_organization:
                user_modify = UserModifyProfile(user=request.user,
                                action='organization',
                                modify_datetime=timezone.now(),
                                modify_before=origin_organization,
                                modify_after=now_organization,
                                remote_addr=get_ip(request),
                                )
                user_modify.save()

            submit_interests = {x.strip() for x in form.cleaned_data['interests'].split(',') if len(x.strip())>0}
            if len(submit_interests)>0:
                user_interests = request.user.interests
                update_skills(request.user, submit_interests, user_interests, Interest)
            submit_tools = {x.strip() for x in form.cleaned_data['tools'].split(',') if len(x.strip())>0}
            if len(submit_tools)>0:
                user_tools = request.user.tools
                update_skills(request.user, submit_tools, user_tools, Tool)            
            return HttpResponseRedirect(reverse('user:profile'))

    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/edit_profile.html', {'form': form, 'active_users': active_users})


@login_required
def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse("index"))


@require_http_methods(['POST', 'GET'])
def forget_password(request):
    if request.method == 'POST':
        form = ForgetPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                usermod = UserModification(
                    user=user,
                    action=UserModification.RESET_PASSWORD,
                    key=random_str(64),
                    expire_datetime=timezone.now() + timezone.timedelta(days=3),
                )
                send_reset_password_mail(email, usermod.key)
                usermod.save()
                messages.info(request, _("A password reset message has been sent to ") + email + ".")
                return HttpResponseRedirect(reverse("index"))

            except User.DoesNotExist:
                messages.warning(request, _("Sorry. This email address hasn't been registered."))
            except Exception as e:
                print(e)
                messages.error(request, _("An error occur when sending reset mail"))
    else:
        form = ForgetPasswordForm()

    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/forget_password.html', {
        'form': form,
        'active_users': active_users,
    })


@require_http_methods(['POST', 'GET'])
def reset_password(request):
    if request.method == 'GET':
        key = request.GET.get('key', '')
        form = ResetPasswordForm(initial={'key': key})
    else:
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            mod = get_object_or_404(UserModification, action=UserModification.RESET_PASSWORD,
                                    key=form.cleaned_data['key'])
            password = form.cleaned_data['password']
            mod.user.password = make_password(password)
            mod.user.save()
            mod.delete()
            messages.info(request, _('Password has been reset'))
            return HttpResponseRedirect(reverse('user:login'))

    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/reset_password.html', {
        'form': form,
        'active_users': active_users,
    })

def pending(request):
    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/pending.html', {'active_users': active_users})


def confirm(request):
    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'user/confirm.html', {'active_users': active_users})

@cache_page(10*30)
def auto_complete_interest(request):
    p = request.GET.get('p', None)
    if p is None:
        return JsonResponse([], safe=False)
    l = [x.name for x in Interest.objects.filter(name__istartswith=p)]
    return JsonResponse(l, safe=False)

@cache_page(10*30)
def auto_complete_tool(request):
    p = request.GET.get('p', None)
    if p is None:
        return JsonResponse([],safe=False)
    l = [x.name for x in Tool.objects.filter(name__istartswith=p)]
    return JsonResponse(l, safe=False)

from urllib.parse import urlencode
import os.path
import csv
import io
import uuid
import datetime
import time 
from django.views.decorators.cache import cache_page

from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from django.db.models import Max, Min, Count

from .models import *
from competition.scoring import enqueue_submission, SMP_score, NDCG_score, SOHU_score, ML3_score

from .util import *
from user.models import UserInfo, UserModification
import user.util
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib import messages
from django.core.cache import cache
import ujson as json
import logging
from ipware.ip import get_ip
from django.utils.translation import ugettext as _ 

# Decorators


# Convert competition_pk to competition
def participation_required(viewfunc):
    @login_required
    def inner(request, competition_pk, *args, **kwargs):
        comp = get_object_or_404(Competition, uid=competition_pk)
        if not comp.has_participant(request.user):
            messages.info(request, _("You must accept competition rules to continue"))
            return HttpResponseRedirect(reverse('competition:rules', args=(competition_pk,)) + '?' +
                                        urlencode({'next_url': request.path}))
        return viewfunc(request, comp, *args, **kwargs)

    return inner


def team_required(viewfunc):
    @participation_required
    def inner(request, competition, *args, **kwargs):
        participation = Participation.objects.filter(user=request.user, competition=competition).get()
        if participation.team is None:
            return HttpResponseRedirect(reverse('competition:submit_as', args=(competition.uid,)))

        return viewfunc(request, competition, participation.team, *args, **kwargs)

    return inner


def json_view(viewfunc):
    def inner(request, *args, **kwargs):
        res = viewfunc(request, *args, **kwargs)
        if isinstance(res, dict):
            return JsonResponse(res)
        return res

    return inner


# Create your views here.

def timeline(request, competition_pk):
    competition = get_object_or_404(Competition, uid=competition_pk)

def index(request):
    active_users = request.session.get('active_users', active_user_count())

    over_competitions = Competition.objects.filter(end_datetime__lt = timezone.now()).order_by("-start_datetime")
    go_competitions = Competition.objects.filter(start_datetime__gt = timezone.now()).order_by("-start_datetime")
    in_competitions = Competition.objects.filter(start_datetime__lte = timezone.now(), end_datetime__gte = timezone.now()).order_by("-start_datetime")

    render_context = {
        "over_competitions": over_competitions,
        "go_competitions": go_competitions,
        "in_competitions": in_competitions,
        "over_num": over_competitions.count(),
        "go_num": go_competitions.count(),
        "in_num": in_competitions.count(),
        "active_users": active_users,
    } 

    if(request.user.is_authenticated()):
        attend_competitions = request.user.participate_competitions.all().order_by("-start_datetime")
        render_context["attend_competitions"] = attend_competitions
        render_context["attend_num"] = attend_competitions.count()
    return render(request, "competition/index.html", render_context)


def detail(request, competition_pk, slug=''):
    competition = get_object_or_404(Competition, uid=competition_pk)

    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    if slug != '':
        try:
            comp_detail = competition.detail_set.get(slug=slug)

            if request.LANGUAGE_CODE.startswith('zh'): 
                title = comp_detail.title
                content = comp_detail.content

            else:
                title = comp_detail.title_en
                content = comp_detail.content_en

        except ObjectDoesNotExist:
            return Http404
    else:
        if request.LANGUAGE_CODE.startswith('zh'):
            content = competition.introduction
        else:
            content = competition.introduction_en
        title = _("Introduction")

    active_users = request.session.get('active_users', active_user_count())

    return render(request, "competition/detail.html", {
        'competition': competition,
        'content': content,
        'title': title,
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime), 
    })


def winners(request, competition_pk):
    active_users = request.session.get('active_users', active_user_count())
    competition = get_object_or_404(Competition, uid=competition_pk)

    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    if timezone.now() <= competition.ShowWinner_datetime:
        messages.info(request, _('the final winners list hasn\'t been released'))
        return HttpResponseRedirect(reverse("competition:leaderboard", args=(competition.uid,)))

    render_context = {
        'competition': competition,
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    }

    return render(request, 'competition/winners.html', render_context)


@login_required
def rules(request, competition_pk):
    next_url = request.GET.get('next_url')
    competition = get_object_or_404(Competition, uid=competition_pk)

    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    has_accepted = competition.has_participant(request.user)
    
    active_users = request.session.get('active_users', active_user_count())
    return render(request, 'competition/rules.html', {
        'competition': competition,
        'has_accepted': has_accepted,
        'next_url': next_url,
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    })


@login_required
def accept_rules(request, competition_pk):
    competition = get_object_or_404(Competition, uid=competition_pk)
    user = request.user
    default_next_url = reverse('competition:index', args=(competition_pk,))
    next_url = request.POST.get('next_url', default_next_url)

    if 'accept' in request.POST:
        try:
            participation = Participation(
                competition=competition,
                user=user,
                team=None,
                join_datetime=timezone.now()
            )
            participation.save()
        except ValidationError:
            pass
    else:
        HttpResponseRedirect(default_next_url)
    return HttpResponseRedirect(next_url)


@participation_required
def data(request, competition, name=''):
    active_users = request.session.get('active_users', active_user_count())

    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    if name == '':
        context = {
            'competition': competition,
            'active_users': active_users,
            'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
            'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
            'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
        }
        return render(request, "competition/data.html", context)
    else:
        try:
            data = competition.data.get(name=name)
            res = HttpResponse()
            res["Content-Disposition"] = "attachment; filename={0}".format(data.name)
            res['X-Accel-Redirect'] = "/data/{0}".format(data.content)
            res['active_users'] = active_users
            return res
        except Exception as e:
            return Http404


@participation_required
def submit_as(request, competition):
    return render(request, 'competition/submit_as.html', {
        'competition': competition
    })


@participation_required
def create_team(request, competition, option):
    try:
        participation = Participation.objects.get(competition=competition, user=request.user)
        if option == 'single':
            is_single = True
        else:
            is_single = False
        if participation.team is None:
            team = Team(name=request.user.info.display_name,
                        competition=competition,
                        leader=request.user,
                        create_datetime=timezone.now(),
                        final_score=-1
                        )
            team.save()
            participation.team = team
            participation.save()
        if is_single:
            return HttpResponseRedirect(reverse('competition:make_submission', args=(competition.uid,)))
        else:
            return HttpResponseRedirect(reverse('competition:my_team', args=(competition.uid,)))

    except ObjectDoesNotExist:
        print("ERROR")
        return HttpResponseBadRequest()


@require_GET
@login_required
def join_team(request, competition_pk):
    logger = logging.getLogger(__name__)
    user = request.user
    if 'id' not in request.GET or 'key' not in request.GET:
        messages.error(request, _("Invalid invitation link"))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))

    id = request.GET.get('id', -1)
    key = request.GET.get('key', '')
    try:
        competition = Competition.objects.get(uid=competition_pk)
        act = UserModification.objects.get(pk=id, key=key, user=user, action=UserModification.JOIN_TEAM)

        inviter_team_id = act.arg1
        inviter_team = Team.objects.get(pk=inviter_team_id)
        participation = get_object_or_404(Participation, user=user, competition=competition)

        ok, msg = check_can_join(competition, inviter_team=inviter_team, invitee=user, invitee_team=participation.team)
        if ok:
            if participation.team is not None:
                Participation.objects.filter(team=participation.team).update(team=inviter_team)
                Submission.objects.filter(team=participation.team).update(team=inviter_team)
            else:
                Submission.objects.filter(user=user).update(team=inviter_team)
                participation.team = inviter_team
                participation.save()

            messages.success(request, _("You have successfully joined the team %s.") % inviter_team.name)
            act.delete()
            return HttpResponseRedirect(reverse("competition:my_team", args=(competition_pk,)))
        else:
            messages.error(request, msg)
            return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))
    except Team.DoesNotExist:
        messages.error(request, _("The team doesn't exist."))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))
    except Competition.DoesNotExist:
        messages.error(request, _("Competition not found"))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))
    except UserModification.DoesNotExist:
        messages.error(request, _("Invitation not found."))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))
    except Participation.DoesNotExist:
        messages.error(request, _("You haven't participated the competition"))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))
    except Exception as e:
        logger.critical(
            "Join team: {username} {id} {key}. {msg}".format(username=user.username, id=id, key=key, msg=str(e)))
        messages.error(request, _("Unknown error. Please contact site administrator."))
        return HttpResponseRedirect(reverse("competition:index", args=(competition_pk,)))


def err_response(msg):
    return JsonResponse({
        'status': 'error',
        'msg': msg
    })


def ok_response(msg=''):
    return JsonResponse({
        'status': 'ok',
        'msg': msg
    })


@team_required
def ajax_invite_user(request, competition, team, email):
    if request.user != team.leader:
        return err_response(_('You are not the team leader!'))

    if email == request.user.email:
        return err_response(_("You can't invite yourself!"))
    if any(map(lambda m: m.email == email, team.members.all())):
        return err_response(_("User ") + email + _(" is your team member!"))

    try:
        invitee = User.objects.get(email=email)

        if invitee.info.status != UserInfo.ACTIVE:
            return err_response(_("User ") + email + _(" hasn't activated his/her account."))

        participation = Participation.objects.get(user=invitee, competition=competition)
        ok, msg = check_can_join(competition, team, invitee, participation.team)
        if ok:
            invitation = UserModification.objects.create(
                user=invitee,
                key=user.util.random_str(64),
                action=UserModification.JOIN_TEAM,
                arg1=team.pk,
                expire_datetime=timezone.now() + datetime.timedelta(days=7)
            )
            ok, msg = send_team_invitation_mail(competition.uid, invitee, team, invitation)
            if ok:
                return ok_response(_("Invitation sent."))
            else:
                invitation.delete()
                return err_response("Failed. " + msg)
        else:
            return err_response(msg)

    except User.DoesNotExist:
        return err_response(_("User ") + email + _(" not found."))

    except Participation.DoesNotExist:
        return err_response(_("User ") + email + _(" hasn't participated the competition."))


@team_required
def ajax_alter_team_name(request, competition, team, name):
    if team.leader != request.user:
        return JsonResponse({
            'status': 'error',
            'msg': _('You are not the team leader!')
        })
    else:
        team.name = name
        team.save()
        return JsonResponse({
            'status': 'ok',
            'msg': 'Success'
        })


@team_required
def make_submission(request, competition, team):
    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    active_users = request.session.get('active_users', active_user_count())
    usercourse_final_submit = finalsubmit_time(competition, request.user)

    #messages.info(request, usercourse_final_submit)

    if timezone.now() < competition.start_datetime:
        return render(request, "competition/submission_forbidden.html", {
            'message': _('the competition is not start yet'),
            'competition': competition,
            'active_users': active_users,
            'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
            'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
            'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
        })
    elif (timezone.now() >= competition.valid_end_datetime):
        if (not competition.allow_overdue_submission) and (timezone.now() >= usercourse_final_submit):
            return render(request, "competition/submission_forbidden.html", {
                'message': _('the validate submission is over'),
                'competition': competition,
                'active_users': active_users,
                'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
                'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
                'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
            })

    if request.method == 'GET':
        if (timezone.now() >= competition.valid_end_datetime):
            messages.info(request, _('Allow submissions on the validation set after the competition(don\'t change leaderboard)'))

        context = {
            'competition': competition,
            'team': team,
            'times_left': (competition.submit_per_day - team.submission_count_today()),
            'active_users': active_users,
            'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
            'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
            'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
        }
        return render(request, 'competition/make_submission.html', context)
    else:
        if not request.FILES:
            return HttpResponseBadRequest(_('Must upload a file'))
        file = request.FILES['submissionFile']
        response_data = {
            "name": file.name,
            "size": file.size,
            "type": file.content_type,
        }

        if not file.name.endswith(competition.filetype):
            return JsonResponse({'success': False, 'msg': _('File type not supported')})

        dest_dir = os.path.join(settings.SUBMISSION_ROOT, str(competition.id))

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        while True:
            filename = os.path.join(dest_dir, str(uuid.uuid4()) + file.name)
            if not os.path.exists(filename):
                break

        destination = open(filename, "wb+")
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()

        if team.submission_count_today() >= competition.submit_per_day:
            return JsonResponse({'success': False, 'msg': _('Exceeds limit')})

        submission = Submission(
            content=filename,
            display_name=file.name,
            submit_datetime=timezone.now(),
            message="Pending",
            status=Submission.PENDING,
            user=request.user,
            team=team,
            competition=competition,
            public_score=-1,
            private_score=-1,
            final_submit=False,
            remote_addr=get_ip(request),
        )

        sohu_weektime = False
        if sohu_truth_file() > 0:#如果是在搜狐周冠军时间内
            sohu_weektime = True

        if competition.evaluation == 'SMP':
            result = SMP_score(filename, competition.public_truth)
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.public_score = result.score
                submission.private_score = result.score
        elif competition.evaluation == 'NDCG':
            result = NDCG_score(filename, competition.public_truth)
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.public_score = result.score
                submission.private_score = result.score
        elif competition.evaluation == 'SOHU':
            result = SOHU_score(filename, competition.public_truth, sohu_truth_file())
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.public_score = result.score
                if not sohu_weektime:#如果是周冠军时间，则没有分数
                    submission.private_score = result.score
        elif competition.evaluation == 'RMSE':
            result = ML3_score(filename, competition.public_truth)
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.public_score = result.score
                submission.private_score = result.score
        else:
            enqueue_submission(submission)

        submission.save()

        response_data['submission_id'] = submission.id
        response_data['query_url'] = reverse("competition:query_submission", args=[submission.id])


        if (timezone.now() >= competition.valid_end_datetime):
            response_data['res_url'] = reverse("competition:my_submission", args=[competition.uid])
        else:
            if (competition.uid == 'luckydata') and sohu_weektime:
                response_data['res_url'] = reverse("competition:my_submission", args=[competition.uid])
            else:
                response_data['res_url'] = reverse("competition:leaderboard_submission", args=(competition.uid, submission.id))
        if competition.uid == 'Tsinghua_course3':
            response_data['res_url'] = reverse("competition:leaderboard_submission", args=(competition.uid, submission.id))

        response_data['err_url'] = reverse("competition:my_submission", args=[competition.uid])
        response_data['success'] = True

        return JsonResponse(response_data)



@team_required
def final_submission(request, competition, team):
    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    active_users = request.session.get('active_users', active_user_count())

    if timezone.now() <= competition.final_submit_datetime:
        messages.info(request, _('the final submisson hasn\'t been released'))
        return HttpResponseRedirect(reverse("competition:make_submission", args=(competition.uid,)))
    elif timezone.now() >= competition.end_datetime:
        messages.info(request, _('the competition is over'))
        return HttpResponseRedirect(reverse("competition:make_submission", args=(competition.uid,)))

    if competition.uid == 'luckydata':
        try:
            limit_users = Sub_limt.objects.get(competition=competition, user=request.user, is_valid=True)
        except Sub_limt.DoesNotExist:
            messages.info(request, _('you are not allowed to participate in the 2nd round'))
            return HttpResponseRedirect(reverse("competition:make_submission", args=(competition.uid,)))

    if request.method == 'GET':
        context = {
            'competition': competition,
            'team': team,
            'current_submission': team.final_submission_name,
            'final_times_left': (competition.final_submit_count - team.final_submission_count_today()),
            'active_users': active_users,
            'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
            'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
            'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
        }
        return render(request, "competition/final_submission.html", context)
    else:
        context = {
            'competition': competition,
            'team': team,
            'current_submission': team.final_submission_name,
            'final_times_left': (competition.final_submit_count - team.final_submission_count_today()),
            'active_users': active_users,
            'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
            'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
            'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
        }

        if not request.FILES:
            return HttpResponseBadRequest(_('Must upload a file'))
        file = request.FILES['submissionFile']
        response_data = {
            "name": file.name,
            "size": file.size,
            "type": file.content_type,
        }

        if not file.name.endswith(competition.filetype):
            messages.info(request, _('File type not supported'))
            return render(request, "competition/final_submission.html", context)

        dest_dir = os.path.join(settings.SUBMISSION_ROOT, str(competition.id))
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        while True:
            filename = os.path.join(dest_dir, str(uuid.uuid4()) + file.name)
            if not os.path.exists(filename):
                break

        destination = open(filename, "wb+")
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()
        
        if team.final_submission_count_today() >= competition.final_submit_count:
            messages.info(request, _('Exceeds limit'))
            return render(request, "competition/final_submission.html", context)
            
        submission = Submission(
            content=filename,
            display_name=file.name,
            submit_datetime=timezone.now(),
            message="Pending",
            status=Submission.PENDING,
            user=request.user,
            team=team,
            competition=competition,
            public_score=-1,
            private_score=-1,
            final_submit=True,
            remote_addr=get_ip(request),
        )
        
        if competition.evaluation == 'SMP':
            result = SMP_score(filename, competition.private_truth)             
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
                messages.info(request, result[1])
                return render(request, "competition/final_submission.html", context)
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.private_score = result.score
                team.final_submission_name = file.name
                team.final_submission_path = filename
                team.save()                 
        elif competition.evaluation == 'NDCG':
            result = NDCG_score(filename, competition.private_truth)
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
                messages.info(request, result[1])
                return render(request, "competition/final_submission.html", context)
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.private_score = result.score
                team.final_submission_name = file.name
                team.final_submission_path = filename
                team.save() 
        elif competition.evaluation == 'SOHU':
            result = SOHU_score(filename, competition.private_truth)
            if result.message:
                submission.status = Submission.ERROR
                submission.message = result[1]
                messages.info(request, result[1])
                return render(request, "competition/final_submission.html", context)
            else:
                submission.status = Submission.SUCCESS
                submission.message = 'success'
                submission.public_score = result.score
                submission.private_score = result.score
        else:
            enqueue_submission(submission)
            
        submission.save()       
        messages.info(request, _('Submission Uploaded Successfully')) 
        return HttpResponseRedirect(reverse("competition:my_submission", args=(competition.uid,)))

@team_required
def my_submission(request, competition, team):
    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    active_users = request.session.get('active_users', active_user_count())

    if request.user == team.leader:
        submissions = team.submissions.order_by('submit_datetime')
    else:
        submissions = request.user.submissions.filter(
            competition=competition
        ).order_by('submit_datetime')

    return render(request, 'competition/my_submission.html', {
        'competition': competition,
        'submissions': submissions,
        'team': team,
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    })


@json_view
@login_required
def ajax_edit_submission_description(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    if not submission.competition.is_active():
        return {'success': False, 'msg': _('Competition has ended.')}
    if not submission.is_editable(request.user):
        return {'success': False, 'msg': _("Not authorized.")}

    des = request.GET.get('description', '')
    submission.description = des[: min(100, len(des))]
    submission.save()
    return {'success': True}


@json_view
@team_required
def ajax_final_submit(request, competition, team):
    try:
        sub_list = [int(pk) for pk in request.GET.get('sub_list', '').split(',')]
        if len(sub_list) > competition.final_submit_count:
            return {'success': False, 'msg': _("Exceeds limit")}
        if request.user != team.leader:
            return {'success': False, 'msg': _("Not authorized.")}
        Submission.objects.filter(user__in=team.members.all()).update(final_submit=False)
        Submission.objects.filter(user__in=team.members.all(), pk__in=sub_list).update(final_submit=True)
    except ValueError as e:
        # print(e)
        return {'success': False, 'msg': _('Syntax error')}
    except Exception as e:
        # print(e)
        return {'success': False, 'msg': _('Database error')}
    return {'success': True}


@team_required
def my_team(request, competition, team):
    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    active_users = request.session.get('active_users', active_user_count())

    return render(request, 'competition/my_team.html', {
        'competition': competition,
        'team': team,
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    })


def ajax_query_submission(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)
    if submission.status == submission.PENDING:
        return JsonResponse({'status': 'pending'})
    elif submission.status == submission.ERROR:
        return JsonResponse({'status': 'error', 'msg': submission.message})
    else:
        return JsonResponse({'status': 'ok'})


def leaderboard(request, competition_pk, submission_pk=None):
    active_users = request.session.get('active_users', active_user_count())

    competition = get_object_or_404(Competition, uid=competition_pk)
    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    if competition_pk == 'kddcup2015':
        return HttpResponseRedirect("http://biendata.com/competition/kddcup2015/rank/")

    cache_key = request.get_full_path()

    lst = []
    for i in range(1,competition.week_winnernum + 1):
        lst.append(i)

    render_context = {
        'competition': competition,
        'rank': load_leaderboard_data(cache_key, competition),
        'active_users': active_users,
        'week_winner': load_leaderboard_data_week(competition),
        'winner_num': lst,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    }

    #render_context['rank_lastweek']= load_leaderboard_data_week(competition, 1)
    #render_context['week_winner']= load_leaderboard_data_week(competition)

    submission = None
    if submission_pk:
        try:
            submission = Submission.objects.get(pk=int(submission_pk))
        except:
            raise Http404
        if submission.user != request.user:
            raise Http404

    if submission:
        render_context.update({
            'submission': submission,
            # 'improved': improved,
            'target_tid': submission.get_team().id
        })

    return render(request, 'competition/leaderboard.html', render_context)


def leaderboard_raw_data(request, competition_pk):
    competition = get_object_or_404(Competition, uid=competition_pk)

    cache_key = "leaderboard_raw_" + str(competition.pk)
    content = cache.get(cache_key)
    if content is None:
        submission_list = Submission.objects.filter(competition=competition, status=Submission.SUCCESS).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['team_id', 'team_name', 'public_score', 'submission_time'])
        for submission in submission_list:
            team = submission.get_team()
            row = [
                team.id,
                team.name if team.members.count() > 1 else team.leader.info.display_name,
                submission.public_score,
                submission.submit_datetime
            ]
            writer.writerow(row)
        content = output.getvalue()
        cache.set(cache_key, content, 60)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leaderboard.csv"'
    response.write(content)
    return response


def final_leaderboard(request, competition_pk):
    active_users = request.session.get('active_users', active_user_count())

    competition = get_object_or_404(Competition, uid=competition_pk)

    if competition.invisible:
        messages.info(request, _('This competition is not accessible now'))
        return HttpResponseRedirect("http://biendata.com")

    if timezone.now() <= competition.finalCaculate_datetime:
        messages.info(request, _('the final leaderboard hasn\'t been released'))
        return HttpResponseRedirect(reverse("competition:leaderboard", args=(competition.uid,)))
    
    if competition_pk == 'kddcup2015':
        return HttpResponseRedirect("http://biendata.com/competition/kddcup2015/rank/")

    cache_key = request.get_full_path()
    render_context = {
        'competition': competition,
        'rank': final_leaderboard_data(competition, competition.final_showwinners_count),
        'active_users': active_users,
        'is_final': timecompare(timezone.now(),competition.finalCaculate_datetime),
        'is_showwinners': timecompare(timezone.now(),competition.ShowWinner_datetime),
        'is_final_submit': timecompare(timezone.now(),competition.final_submit_datetime),
    }

    return render(request, 'competition/final_leaderboard.html', render_context)

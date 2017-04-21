from .models import *
from user.models import UserModification
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.mail import send_mail
from urllib.parse import urlencode
from user.util import send_mail_checked
from django.db.models import Max, Min, Count
from django.core.cache import cache
import ujson as json
import datetime
import time 
from django.utils.translation import ugettext as _ 
from user.models import UserInfo

def get_team_rank(competition, deadline, addition, reverse):
    add1, add2 = '<', 'desc'
    if reverse:
        add1, add2 = '>', ''

    result = Team.objects.raw('''
        WITH submissions AS (SELECT * from competition_submission sub WHERE sub.competition_id=%s and sub.submit_datetime<%s 
        ''' + addition + ''' and sub.status=2 and sub.final_submit=False)
        SELECT team.*, r1.public_score as score, r1.submit_datetime as last_submission, cnt_table.entries from submissions r1
        LEFT JOIN submissions r2 on r1.team_id=r2.team_id and
                                            ( r1.public_score'''+add1+'''r2.public_score or
                                             (r1.public_score=r2.public_score and r1.submit_datetime>r2.submit_datetime) or
                                             (r1.public_score=r2.public_score and r1.submit_datetime=r2.submit_datetime and r1.id<r2.id)
                                            )
        INNER JOIN (SELECT sub.team_id, COUNT(*) as entries FROM submissions sub GROUP BY sub.team_id) cnt_table on r1.team_id=cnt_table.team_id
        INNER JOIN competition_team team on team.id = r1.team_id
        WHERE r2.team_id is NULL ORDER BY score '''+add2+''', last_submission
    ''', [competition.pk, deadline])
    return result

def load_leaderboard_data(key, competition):
    json_data = cache.get(key)
    if json_data:
        return json.loads(json_data)

    deadline = timezone.now()
    if (timezone.now() > competition.valid_end_datetime):
        deadline = competition.valid_end_datetime
    if competition.uid == 'Tsinghua_course3':
        deadline = competition.end_datetime

    addition = ""
    if competition.uid == 'luckydata':
        addition = 'and sub.private_score>-1'
    rank_now = get_team_rank(competition, deadline, addition, competition.evaluate_reverse)
    rank_old = get_team_rank(competition, deadline - datetime.timedelta(days=1), addition, competition.evaluate_reverse)
    leaderboard_data = []

    team_rank_old = {r.id: i for i, r in enumerate(rank_old)}
    for i, t in enumerate(rank_now):
        row = {
            "rank": i + 1,
            "team_name": t.name,
            "team_id": t.id,
            "leader_name": t.leader.info.display_name,
            "leader_id": t.leader.id,
            "single": t.members.count() == 1,
            "members": [{"id": m.id, "name": m.info.display_name} for m in t.members.all()],
            "score": t.score,
            "entries": t.entries,
            "last_submission": t.last_submission,
        }
        if t.id in team_rank_old:
            row['delta'] = i - team_rank_old[t.id]
            row['new'] = False
        else:
            row['new'] = True
        leaderboard_data.append(row)
    cache.set(key, json.dumps(leaderboard_data), 60*10)
    return leaderboard_data

#get the monday date of this week   
def first_day_of_week():
    return datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())

def timecompare(t1,t2):
    value = False
    if t1 > t2:
        value = True
    return value

def get_week_rank(competition, start, end, addition, reverse):
    add1, add2 = '<', 'desc'
    if reverse:
        add1, add2 = '>', ''

    result = Team.objects.raw('''
        WITH submissions AS (SELECT * from competition_submission sub WHERE sub.competition_id=%s and sub.submit_datetime>%s and sub.submit_datetime<%s
        ''' + addition + '''  and sub.status=2 and sub.final_submit=False)
        SELECT team.*, r1.public_score as score, r1.submit_datetime as last_submission, cnt_table.entries from submissions r1
        LEFT JOIN submissions r2 on r1.team_id=r2.team_id and
                                            ( r1.public_score'''+add1+'''r2.public_score or
                                             (r1.public_score=r2.public_score and r1.submit_datetime>r2.submit_datetime) or
                                             (r1.public_score=r2.public_score and r1.submit_datetime=r2.submit_datetime and r1.id<r2.id)
                                            )
        INNER JOIN (SELECT sub.team_id, COUNT(*) as entries FROM submissions sub GROUP BY sub.team_id) cnt_table on r1.team_id=cnt_table.team_id
        INNER JOIN competition_team team on team.id = r1.team_id
        WHERE r2.team_id is NULL ORDER BY score '''+add2+''', last_submission
    ''', [competition.pk, start, end])
    return result


def load_leaderboard_data_week(competition):
    #acquire all the week winner of the competition
    leaderboard_data_week = []

    start = datetime.datetime.combine(competition.winner_start_datetime.date(), datetime.time.min)
    now = datetime.datetime.utcnow()
    if (timezone.now() <= competition.winner_start_datetime):
        return leaderboard_data_week
    elif (timezone.now() > competition.winner_end_datetime):
        now = datetime.datetime.combine(competition.winner_end_datetime.date(), datetime.time.min)

    num = 1
    count = 1
    addition = ""
    if competition.uid == 'luckydata':
        addition = 'and sub.private_score=-1'
    while start < now - datetime.timedelta(days=1):
        start += datetime.timedelta(days=1)
        #it it is monday
        if start.strftime("%w") == "1":
            str_t = start - datetime.timedelta(days=7)
            end_t = start.strftime("%Y-%m-%d")+" 04:00:00"
        
            if competition.uid == 'luckydata':
                str_t = start - datetime.timedelta(days=1)
            rank_week = get_week_rank(competition, str_t.strftime("%Y-%m-%d")+" 04:00:00", end_t, addition, competition.evaluate_reverse)
        
            week_winners = []
            for i, t in enumerate(rank_week):
                row = {
                    "is_first": False,
                    "week": num,
                    "team_name": t.name,
                    "team_id": t.id,
                    "leader_name": t.leader.info.display_name,
                    "leader_id": t.leader.id,
                    "single": t.members.count() == 1,
                    "members": [{"id": m.id, "name": m.info.display_name} for m in t.members.all()],
                    "score": t.score,
                }

                if count == 1:
                    row["is_first"]=True

                if count <= competition.week_winnernum:
                    week_winners.append(row)
                    count = count + 1
                else:
                    break
            count = 1
            num += 1
            leaderboard_data_week.append(week_winners)
    return leaderboard_data_week

def get_final_rank(competition, start, end):
    result = Team.objects.raw('''
        WITH submissions AS (SELECT * from competition_submission sub WHERE sub.competition_id=%s and sub.submit_datetime>%s and sub.submit_datetime<%s and sub.status=2 and sub.final_submit=True)
        SELECT team.*, r1.private_score as score, r1.submit_datetime as last_submission, cnt_table.entries from submissions r1
        LEFT JOIN submissions r2 on r1.team_id=r2.team_id and
                                            ( r1.private_score<r2.private_score or
                                             (r1.private_score=r2.private_score and r1.submit_datetime>r2.submit_datetime) or
                                             (r1.private_score=r2.private_score and r1.submit_datetime=r2.submit_datetime and r1.id<r2.id)
                                            )
        INNER JOIN (SELECT sub.team_id, COUNT(*) as entries FROM submissions sub GROUP BY sub.team_id) cnt_table on r1.team_id=cnt_table.team_id
        INNER JOIN competition_team team on team.id = r1.team_id
        WHERE r2.team_id is NULL ORDER BY score desc, last_submission
    ''', [competition.pk, start, end])
    return result

def final_leaderboard_data(competition, num):
    start = competition.final_submit_datetime
    end = competition.end_datetime
    rank_final = get_final_rank(competition, start, end)
    leaderboard_data = []

    for i, t in enumerate(rank_final):
        row = {
            "rank": i + 1,
            "team_name": t.name,
            "team_id": t.id,
            "leader_name": t.leader.info.display_name,
            "leader_id": t.leader.id,
            "single": t.members.count() == 1,
            "members": [{"id": m.id, "name": m.info.display_name} for m in t.members.all()],
            "score": t.score,
            "entries": t.entries,
        }
        if i >= num:
            break;
        leaderboard_data.append(row)
    return leaderboard_data


def get_finalsubmit_time(competition, student):
    result = Team.objects.raw('''
        SELECT cour.id, cour.end_datetime as ft from course_course as cour,course_course_students as cs
        WHERE cour.id = cs.course_id and cour.competition_id=%s and cs.user_id=%s
        ORDER BY ft DESC
    ''', [competition.pk, student.pk])
    return result

def finalsubmit_time(competition, student):
    final_t = get_finalsubmit_time(competition, student)
    final_time = []

    for i, t in enumerate(final_t):
        final_time.append(t.ft)

    if final_time:
        return final_time[0]
    else:
        return competition.valid_end_datetime


def send_team_invitation_mail(competition_pk, invited, team, invitation):
    subject = _("Team %s Invites You to Join") % team.name
    url = settings.SITE_URL + reverse("competition:join_team", args=(competition_pk,)) + "?" + urlencode({
        "id": invitation.id,
        "key": invitation.key,
        "action": UserModification.JOIN_TEAM
    })
    plain_text = _("Visit following link to accept the invitation\n") + url
    html_text = _('Click')+' <a href="%s">here</a> ' %url +_('to accept the invitation. If the link doesn\'t work, please visit %s') %url
    return send_mail_checked(subject=subject, message=plain_text, html_message=html_text,
                             from_email=settings.EMAIL_FROM, recipient_list=[invited.email])

#calculate the active user number
def active_user_count():
    now = timezone.now()
    deadline = now - datetime.timedelta(minutes=60)
    #result = get_active_user(now - datetime.timedelta(minutes=10))
    count = UserInfo.objects.filter(last_visit__gte = deadline).count()
    return count


def check_can_join(competition, inviter_team, invitee, invitee_team):
    # inviter_team = Participation.objects.get(competition = competition, user=inviter).team
    # invitee_team = Participation.objects.get(competition = competition, user=invitee).team

    if timezone.now() >= competition.final_submit_datetime:
        return False, _("Team merging is not allowed after final submission date")

    if invitee_team != None:
        if invitee_team.leader != invitee:
            return False, _("User ") + invitee.email + _(" have joined another team.")
        if inviter_team.size() + invitee_team.size() > competition.max_team_size:
            return False, _("Team size exceeds limit")

        inviter_submission = inviter_team.submission_count_total()
        invitee_submission = invitee_team.submission_count_total()

        if timezone.now() >= competition.start_datetime and \
                                inviter_submission + invitee_submission > competition.submit_per_day * competition.ongoing_days():
            return False, _("Total submission entries exceed limit.")

    return True, "success"


def sohu_truth_file():
    '函数测试当前时间是否落在下表time_cap中某一项的一天前内，并返回一个数字代表第几项，若无符合则返回-1'
    time_cap = ['2017-04-03 04:00:00', '2017-04-10 04:00:00', '2017-04-17 04:00:00', 
 '2017-04-24 04:00:00', '2017-05-01 04:00:00', '2017-05-08 04:00:00']
    
    #这里将上述字符串时间转换为时间戳(距离1970-1-1的以秒为单位的偏移量)，方便数字计算
    cap = [] 
    for item in time_cap:
        cap.append(time.mktime(time.strptime(item, '%Y-%m-%d %H:%M:%S')))
    
    #这里判断当前时间是否落入区间.（当前 - 截止前一天 >= 0  并且 截止当天 - 当前 >= 0）
    for i, item in enumerate(cap):
        if time.time() - (item - 24*60*60) >= 0 and item - time.time() >= 0:
            return i+1
    
    #下面是测试用代码，把上面一段注释掉，更改test_time后面日期时间供测试
    #test_time = time.mktime(time.strptime('2017-05-08 12:00:00', '%Y-%m-%d %H:%M:%S'))
    #for i, item in enumerate(cap):
    #    if  test_time - (item - 24*60*60) >= 0 and item - test_time >= 0:
    #        return i
      
    
    return 0

# def check_can_join(competition, invited, current_team, team, pronoun):
#     if timezone.now() >= competition.final_submit_datetime:
#         return False, "Team merge is allowed after final submission date"
#     if current_team is None:
#         return True, ""
#     if current_team.leader != invited:
#         return False, pronoun + " have joined another team."
#
#     if current_team.size() + team.size() > competition.max_team_size:
#         return False, "Team size exceeds limit"
#
#     submission_total = team.submission_count_total()
#     current_submission_total = current_team.submission_count_total()
#
#     if timezone.now() >= competition.start_datetime and \
#                             submission_total + current_submission_total > competition.submit_per_day * competition.ongoing_days():
#         return False, "Total submission entries exceed limit."
#     return True, ""

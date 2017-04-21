from .models import *
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from urllib.parse import urlencode
from django.db.models import Max, Min, Count
from django.core.cache import cache
from competition.models import Team
import ujson as json
import datetime
import competition.models
from django.utils import timezone


def get_team_rank(competition, start, end, addition, reverse):
    add1, add2 = '<', 'desc'
    if reverse:
        add1, add2 = '>', ''

    result = Team.objects.raw('''
        WITH submissions AS (SELECT * from competition_submission sub WHERE sub.competition_id=%s and sub.submit_datetime>%s and sub.submit_datetime<%s 
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
    ''', [competition.pk, start, end])
    return result

def get_course_team(course):
    result = Team.objects.raw('''
        SELECT DISTINCT ct.id from competition_participation as cp, course_course_students as ccs,competition_team as ct
        WHERE ccs.course_id =%s and ccs.user_id=cp.user_id and cp.team_id=ct.id
    ''', [course.pk])
    return result

def get_stu_team(competition, student):
    result = Team.objects.raw('''
        SELECT * from competition_participation WHERE competition_id=%s and user_id=%s
    ''', [competition.pk, student.pk])
    return result


def course_leaderboard_data(competition, course):
    course_team = get_course_team(course)
    team_id = []

    for i, t in enumerate(course_team):
        team_id.append(t.id)

    start = course.start_datetime
    end = course.end_datetime

    addition = ""
    if competition.uid == 'luckydata':
        addition = 'and sub.private_score>-1'

    rank_now = get_team_rank(competition, start, end, addition, competition.evaluate_reverse)
    leaderboard_data = []

    count = 0
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
        }
        if t.id in team_id:
            count = count + 1
            row["rank"] = count
            leaderboard_data.append(row)
    return leaderboard_data

def stu_leaderboard_data(competition, course, stu):
    stu_team = get_stu_team(competition, stu)
    team_id = []

    addition = ""
    reverse = False
    if competition.uid == 'luckydata':
        addition = 'and sub.private_score>-1'
    if competition.uid == 'Tsinghua_course3':
        reverse = True

    for i, t in enumerate(stu_team):
        team_id.append(t.team_id)

    leaderboard_data = []
    if team_id:
        course_team = get_course_team(course)
        course_team_id = []

        for i, t in enumerate(course_team):
            course_team_id.append(t.id)

        start = course.start_datetime
        end = course.end_datetime
        rank_now = get_team_rank(competition, start, end, addition, reverse)

        count = 0
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
            }
            if t.id in course_team_id:
                count = count + 1
            if t.id in team_id:
                row["rank"] = count
                leaderboard_data.append(row)
                break
    return leaderboard_data

    


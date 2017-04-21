from django.conf.urls import include, url
import competition.views

suburls = [
    url(r'^$', competition.views.detail, name='index'),
    url(r'^make-submission/$', competition.views.make_submission, name='make_submission'),
    url(r'^final-submission/$', competition.views.final_submission, name='final_submission'),
    url(r'^my-submission/$', competition.views.my_submission, name='my_submission'),
    url(r'^leaderboard/$', competition.views.leaderboard, name='leaderboard'),
    url(r'^final-leaderboard/$', competition.views.final_leaderboard, name='final_leaderboard'),
    url(r'^winners/$', competition.views.winners, name='winners'),
    url(r'^leaderboard/(?P<submission_pk>\d+)/$', competition.views.leaderboard, name='leaderboard_submission'),
    url(r'^leaderboard-raw/$', competition.views.leaderboard_raw_data, name='leaderboard_raw_data'),
    url(r'^rules/$', competition.views.rules, name='rules'),
    url(r'^rules/accept$', competition.views.accept_rules, name='accept_rules'),
    url(r'^team/submit_as/$', competition.views.submit_as, name='submit_as'),
    url(r'^team/create/(?P<option>\w+)/$', competition.views.create_team, name='create_team'),
    url(r'^team/my_team/$', competition.views.my_team, name='my_team'),
    url(r'^team/alter_name/(?P<name>.+)$', competition.views.ajax_alter_team_name, name='alter_team_name'),
    url(r'^team/invite_user/(?P<email>.+)$', competition.views.ajax_invite_user, name='invite_user'),
    url(r'^team/join_team/$', competition.views.join_team, name='join_team'),
    url(r'^data/$', competition.views.data, name='data'),
    url(r'^data/(?P<name>[-0-9a-zA-Z_.]+)/$', competition.views.data, name='data'),
    url(r'^(?P<slug>[a-zA-Z-_]+)/$', competition.views.detail, name='detail'),
]

urlpatterns = [
    url(r'^$', competition.views.index, name="main"),
    url(r'^(?P<competition_pk>[a-zA-z0-9_]+)/', include(suburls)),
    url(r'^submission/edit/(?P<submission_id>\d+)/$', competition.views.ajax_edit_submission_description,
        name='edit_submission'),
    url(r'^(?P<competition_pk>[a-zA-z0-9_]+)/submission/final/$', competition.views.ajax_final_submit,name='final_submit'),
    url(r'^submission/(?P<submission_pk>\d+)$', competition.views.ajax_query_submission, name='query_submission'),
]

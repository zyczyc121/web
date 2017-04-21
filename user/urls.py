from django.conf.urls import url
import user.views

urlpatterns = [
    url(r'^register/$', user.views.register, name='register'),
    url(r'^login/$', user.views.login, name='login'),
    url(r'^logout/$', user.views.logout, name='logout'),
    url(r'^activate/$', user.views.activate, name='activate'),
    url(r'^pending/$', user.views.pending, name='pending'),
    url(r'^confirm/$', user.views.confirm, name='confirm'),
    url(r'^profile/$', user.views.profile, name='profile'),
    url(r'^profile/edit/$', user.views.edit_profile, name='edit_profile'),
    url(r'^profile/(?P<id>\d+)$', user.views.view_user, name='user'),
    url(r'^forget-password/$', user.views.forget_password, name='forget_password'),
    url(r'^reset-password/$', user.views.reset_password, name='reset_password'),
    url(r'^auto-complete/interest$', user.views.auto_complete_interest, name='auto_complete_interest'),
    url(r'^auto-complete/tool$', user.views.auto_complete_tool, name='auto_complete_tool')
]

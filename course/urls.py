from django.conf.urls import include, url
from django.views.generic import TemplateView
import course.views


assignment_urls = [
    url(r'^$', course.views.ViewAssignment.as_view(), name="assignment"),
    url(r'^edit/', course.views.EditAssignment.as_view(), name="edit_assignment"),
    url(r'^detail/$', course.views.EditDetail.as_view(), name="edit_detail"),
    url(r'^detail/new/$', course.views.EditDetailPage.as_view(), name="edit_detail_page"),
    url(r'^detail/edit/(?P<slug>[a-zA-Z-_]+)/$', course.views.EditDetailPage.as_view(), name="edit_detail_page"),
    url(r'^detail/delete/(?P<slug>[a-zA-Z-_]+)/$', course.views.delete_detail_page, name="delete_detail_page"),
    url(r'^data/$', course.views.EditData.as_view(), name='edit_data'),
    url(r'^data/delete/(?P<data_pk>\d+)/$', course.views.delete_data, name='delete_data'),
    url(r'^data/add/$', course.views.add_data, name='add_data'),
    url(r'^evaluation/$', course.views.EditEvaluation.as_view(), name='edit_evaluation'),
]

urlpatterns = [
    url(r'^$', course.views.index, name="index"),
    url(r'^(?P<course_pk>\d+)/$', course.views.ViewCourse.as_view(), name="view"),
    url(r'^(?P<course_pk>\d+)/signup/$', course.views.signup, name="signup"),
    #url(r'^(?P<course_pk>\d+)/applycourse/$', course.views.applycourse, name="applycourse"),
    url(r'^(?P<course_pk>\d+)/students/(?P<page>[0-9]+)/$', course.views.ViewStudents.as_view(), name="students"),
    url(r'^(?P<course_pk>\d+)/leaderboard/$', course.views.ViewLeaderboard.as_view(), name='leaderboard'),
    url(r'^(?P<course_pk>\d+)/disapprove/(?P<student_pk>[0-9]+)/$', course.views.disapprove, name="disapprove"),
    url(r'^(?P<course_pk>\d+)/edit/$', course.views.EditCourse.as_view(), name="edit"),
    url(r'^(?P<course_pk>\d+)/delete_ta/(?P<ta_pk>\d+)/$', course.views.delete_ta, name="delete_ta"),
    url(r'^(?P<course_pk>\d+)/add_ta/$', course.views.add_ta, name="add_ta"),
    url(r'^(?P<course_pk>\d+)/add_stu/$', course.views.add_stu, name="add_stu"),
    url(r'^(?P<course_pk>\d+)/new_assignment/$', course.views.CreateAssignment.as_view(), name="create_assignment"),
    url(r'^(?P<course_pk>\d+)/(?P<assignment_pk>\d+)/', include(assignment_urls)),
    url(r'^(?P<course_pk>\d+)/(?P<assignment_pk>\d+)/detail/$', course.views.EditDetail.as_view(), name="edit_detail")
]

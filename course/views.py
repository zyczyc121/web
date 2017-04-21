from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django import http
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse, reverse_lazy
import django.views.generic.edit
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib import messages

from course.models import *
from course.forms import *
import competition.models
import os
import datetime
from django.utils.translation import ugettext as _
from competition.util import active_user_count
from .util import course_leaderboard_data,stu_leaderboard_data


def is_member_of(group_name):
    def test(user):
        return user.groups.filter(name=group_name).exists()

    return test


is_tutor = is_member_of("tutors")
# Views

def index(request):
    active_users = request.session.get('active_users', active_user_count())

    over_courses = Course.objects.filter(end_datetime__lt = timezone.now()).order_by("-start_datetime")
    go_courses = Course.objects.filter(start_datetime__gt = timezone.now()).order_by("-start_datetime")
    in_courses = Course.objects.filter(start_datetime__lte = timezone.now(), end_datetime__gte = timezone.now()).order_by("-start_datetime")

    render_context = {
        "over_courses": over_courses,
        "go_courses": go_courses,
        "in_courses": in_courses,
        "over_num": over_courses.count(),
        "go_num": go_courses.count(),
        "in_num": in_courses.count(),
        "active_users": active_users,
    }

    if(request.user.is_authenticated()):
        render_context["tutor_courses"] = request.user.tutor_courses.all().order_by("-start_datetime")
        render_context["assistant_courses"] = request.user.ta_courses.all().order_by("-start_datetime")
        render_context["attend_courses"] = request.user.attend_courses.all().order_by("-start_datetime")
        render_context["tutor_num"] = render_context["tutor_courses"].count()
        render_context["assistant_num"] = render_context["assistant_courses"].count()
        render_context["attend_num"] = render_context["assistant_courses"].count()

    return render(request, "course/index.html", render_context)


class CourseMixin:
    def __init__(self):
        self.course = None
        self.user = None

    def get_context_data(self, **kwargs):
        context = super(CourseMixin, self).get_context_data(**kwargs)
        if is_tutor(self.user):
            context['all_courses'] = self.user.tutor_courses.all()
        else:
            context['all_courses'] = [self.course]

        context['course'] = self.course
        context['manage'] = (self.user == self.course.tutor) or \
                            (self.course.teaching_assistants.filter(pk=self.user.pk).exists())

        context['signed_up'] = self.course.students.filter(pk=self.user.pk).exists()
        context['form_helper'] = form_helper
       
        return context


class AssignmentMixin(CourseMixin):
    def __init__(self):
        self.assignment = None
        self.competition = None

    def get_context_data(self, **kwargs):
        context = super(AssignmentMixin, self).get_context_data(**kwargs)
        context['assignment'] = self.assignment
        context['competition'] = self.competition
        return context



class ViewCourse(CourseMixin, generic.TemplateView):
    template_name = "course/course.html"

    def __init__(self):
        super(ViewCourse, self).__init__()

    def dispatch(self, request, course_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        if not self.course.open_navigate:
            messages.info(request,_("this course can't Register now"))
        return super(ViewCourse, self).dispatch(request, course_pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewCourse, self).get_context_data(**kwargs)
        if is_tutor(self.user):
            context['all_courses'] = self.user.tutor_courses.all()
        else:
            context['all_courses'] = [self.course]

        context['course'] = self.course
        context['manage'] = (self.user == self.course.tutor)
        context['assistant'] = (self.course.teaching_assistants.filter(pk=self.user.pk).exists())
        context['active_users'] = self.request.session.get('active_users', active_user_count())

        if context['signed_up']:
            context['stu_rank'] = stu_leaderboard_data(self.course.competition, self.course, self.user)
        #context['team']
        return context


class EditCourse(CourseMixin, generic.UpdateView):
    template_name = "course/edit_course.html"

    model = Course
    fields = ['name', 'school', 'start_datetime', 'end_datetime', 'description', 'register_code', 'open_navigate',
              'open_signup',
              ]

    def dispatch(self, request, course_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        if self.course.tutor != self.user:
            return http.HttpResponseForbidden()
        return super(EditCourse, self).dispatch(request, course_pk, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.course

    def get_context_data(self, **kwargs):
        context = super(EditCourse, self).get_context_data(**kwargs)
        context['active_users'] = self.request.session.get('active_users', active_user_count())
        return context

    def get_success_url(self):
        return reverse('course:view', args=(self.course.pk,))


@login_required
def delete_ta(request, course_pk, ta_pk):
    course = get_object_or_404(Course, pk=course_pk)
    ta = get_object_or_404(User, pk=ta_pk)
    if course.tutor != request.user:
        return http.HttpResponseForbidden()

    course.teaching_assistants.remove(ta)
    return http.HttpResponseRedirect(reverse('course:view', args=(course.pk,)))


@require_POST
@login_required
def add_ta(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if course.tutor != request.user:
        return http.HttpResponseForbidden()
    ta_email = request.POST.get('email', None)
    #messages.success(request, ta_email)
    try:
        ta = User.objects.get(email=ta_email)
        #messages.error(request, ta.username)
        course.teaching_assistants.add(ta)
    except User.DoesNotExist:
        messages.error(request, _("Email ") + ta_email + _(" not found"))
    return http.HttpResponseRedirect(reverse('course:view', args=(course.pk,)))

@require_POST
@login_required
def add_stu(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if course.tutor != request.user:
        return http.HttpResponseForbidden()
    stu_email = request.POST.get('email', None)
    
    try:
        stu = User.objects.get(email=stu_email)
        course.students.add(stu)
        messages.success(request, _("You has successfully added student ") + stu.username)
    except User.DoesNotExist:
        messages.error(request, _("Email ") + stu_email + _(" not found"))
    return http.HttpResponseRedirect(reverse('course:view', args=(course.pk,)))


class CreateAssignment(CourseMixin, generic.FormView):
    template_name = "course/edit_assignment.html"
    form_class = CreateProjectForm

    initial = {}

    def __init__(self):
        super(CreateAssignment, self).__init__()
        self.competition = None
        self.assignment = None

    def dispatch(self, request, course_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        if self.user != self.course.tutor:
            return http.HttpResponseForbidden()
        return super(CreateAssignment, self).dispatch(request, course_pk, *args, **kwargs)

    def form_valid(self, form):
        comp = form.save(commit=False)
        comp.host = self.user
        comp.category = competition.models.Competition.KNOWLEDGE
        comp.award = "Credit"
        comp.allow_overdue_submission = False
        comp.evaluation = "AUC"
        comp.num_line = 0
        comp.public_ratio = 0
        comp.public_truth = ""
        comp.private_truth = ""
        comp.save()
        self.competition = comp

        assignment = Assignment(
            title=comp.name,
            description=comp.description,
            course=self.course,
            open=True,
            create_datetime=timezone.now(),
            start_datetime=comp.start_datetime,
            end_datetime=comp.end_datetime,
            competition=comp
        )
        assignment.save()
        self.assignment = assignment
        return super(CreateAssignment, self).form_valid(form)

    def get_success_url(self):
        return reverse("course:edit_data", args=(self.course.pk, self.assignment.pk,))


class ViewAssignment(AssignmentMixin, generic.TemplateView):
    template_name = "course/assignment.html"

    def dispatch(self, request, course_pk, assignment_pk, **kwargs):
        self.course = get_object_or_404(Course, pk=course_pk)
        self.user = request.user
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.competition = self.assignment.competition
        return super(ViewAssignment, self).dispatch(request, course_pk, assignment_pk, **kwargs)


class EditAssignment(AssignmentMixin, generic.UpdateView):
    template_name = "course/edit_assignment.html"
    # model = competition.models.Competition
    # fields = ['name', 'description', 'max_team_size', 'start_datetime', 'end_datetime', 'logo']
    # labels = {
    #     'max_team_size': 'Maximum team size',
    #     'name': 'Assignment title',
    #     'logo': 'Logo (optional)'
    # }
    form_class = CreateProjectForm

    def dispatch(self, request, course_pk, assignment_pk, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=course_pk)
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.user = request.user
        self.competition = self.assignment.competition
        if self.user != self.course.tutor or self.course != self.assignment.course:
            return http.HttpResponseForbidden()
        return super(EditAssignment, self).dispatch(request, course_pk, assignment_pk, **kwargs)

    def form_valid(self, form):
        self.assignment.title = form.cleaned_data['name']
        self.assignment.description = form.cleaned_data['description']
        self.assignment.start_datetime = form.cleaned_data['start_datetime']
        self.assignment.end_datetime = form.cleaned_data['end_datetime']
        self.assignment.save()
        return super(EditAssignment, self).form_valid(form)

    def get_success_url(self):
        return reverse('course:edit_data', args=(self.course.pk, self.assignment.pk))

    def get_object(self, queryset=None):
        return self.competition


class EditDetail(CourseMixin, generic.TemplateView):
    template_name = "course/edit_detail.html"

    def __init__(self):
        super(EditDetail, self).__init__()
        self.competition = None
        self.assignment = None

    def dispatch(self, request, course_pk, assignment_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.competition = self.assignment.competition
        if self.user != self.course.tutor:
            return http.HttpResponseForbidden()
        return super(EditDetail, self).dispatch(request, course_pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditDetail, self).get_context_data()
        context['assignment'] = self.assignment
        context['competition'] = self.competition
        return context


@login_required
def delete_detail_page(request, course_pk, assignment_pk, slug):
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    if assignment.course.tutor != request.user:
        return http.HttpResponseForbidden()
    if assignment.competition.host != request.user:
        return http.HttpResponseForbidden()

    try:
        detail = assignment.competition.detail_set.get(slug=slug)
        detail.delete()
    except competition.models.Detail.DoesNotExist:
        raise http.Http404

    return http.HttpResponseRedirect(reverse('course:edit_detail', args=(assignment.course.pk, assignment.pk)))


class EditDetailPage(AssignmentMixin, generic.FormView):
    template_name = "course/edit_detail_page.html"
    form_class = EditDetailForm

    def __init__(self):
        super(EditDetailPage, self).__init__()
        self.slug = None

    def get_initial(self):
        if 'slug' in self.kwargs:
            slug = self.kwargs['slug']
            if slug == 'introduction':
                return {'title': 'Introduction', 'content': self.competition.introduction}
            elif slug == 'rules':
                return {'title': 'Rules', 'content': self.competition.rules}
            elif slug == 'data':
                return {'title': 'Data', 'content': self.competition.data_description}
            else:
                try:
                    detail = self.competition.detail_set.get(slug=slug)
                    return {'title': detail.title, 'content': detail.content}
                except competition.models.Detail.DoesNotExist:
                    raise http.Http404()
        else:
            return {'title': '', 'content': ''}

    def dispatch(self, request, course_pk, assignment_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.competition = self.assignment.competition
        if self.user != self.course.tutor:
            return http.HttpResponseForbidden()

        return super(EditDetailPage, self).dispatch(request, course_pk, *args, **kwargs)

    def form_valid(self, form):
        title = form.cleaned_data['title']
        content = form.cleaned_data['content']
        if 'slug' in self.kwargs:
            slug = self.kwargs['slug']
            if slug == 'introduction':
                self.competition.introduction = content
                self.competition.save()
            elif slug == 'rules':
                self.competition.rules = content
                self.competition.save()
            elif slug == 'data':
                self.competition.data_description = content
                self.competition.save()
            else:
                detail = self.competition.detail_set.get(slug=slug)
                detail.title = title
                detail.content = content
                detail.slug = slugify(title)
                detail.save()
        else:
            competition.models.Detail.objects.create(
                competition=self.competition,
                title=title,
                content=content,
                slug=slugify(title),
                order=self.competition.detail_set.count() + 3
            )

        return super(EditDetailPage, self).form_valid(form)

    def get_success_url(self):
        return reverse("course:edit_detail", args=(self.course.pk, self.assignment.pk))


class EditEvaluation(AssignmentMixin, generic.UpdateView):
    model = competition.models.Competition
    fields = [
        'evaluation', 'submit_per_day', 'final_submit_count', 'public_truth', 'private_truth',
    ]
    labels = {
        'submit_per_day': 'Submission per day',
        'final_submit_count': 'Final submission count',
        'public_truth': 'Public truth file',
        'private_truth': 'Private truth file',
    }

    template_name = "course/edit_evaluation.html"

    def dispatch(self, request, course_pk, assignment_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.competition = self.assignment.competition
        if self.user != self.course.tutor:
            return http.HttpResponseForbidden()

        return super(EditEvaluation, self).dispatch(request, course_pk, *args, **kwargs)

    def form_valid(self, form):
        public_truth_data = form.cleaned_data['public_truth'].read().decode('utf8')
        private_truth_data = form.cleaned_data['private_truth'].read().decode('utf8')
        public_lines = public_truth_data.count('\n')
        private_lines = private_truth_data.count('\n')
        self.competition.public_ratio = public_lines / private_lines * 100
        self.competition.num_line = private_lines

        return super(EditEvaluation, self).form_valid(form)

    def get_success_url(self):
        return reverse('course:assignment', args=(self.course.pk, self.assignment.pk))

    def get_object(self, queryset=None):
        return self.competition


class EditData(AssignmentMixin, generic.TemplateView):
    template_name = "course/edit_data.html"

    def dispatch(self, request, course_pk, assignment_pk, *args, **kwargs):
        self.user = request.user
        self.course = get_object_or_404(Course, pk=course_pk)
        self.assignment = get_object_or_404(Assignment, pk=assignment_pk)
        self.competition = self.assignment.competition
        if self.user != self.course.tutor:
            return http.HttpResponseForbidden()
        return super(EditData, self).dispatch(request, course_pk, assignment_pk)


@require_POST
def add_data(request, course_pk, assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    if assignment.course != course or request.user != course.tutor:
        return http.HttpResponseForbidden()

    file = request.FILES['file']

    _, filename = os.path.split(file.name)
    _, fileext = os.path.splitext(filename)
    competition.models.Data.objects.create(
        competition=assignment.competition,
        content=file,
        name=file.name,
        size=file.size,
        filetype=file.content_type,
    )

    response_data = {
        "name": file.name,
        "size": file.size,
        "type": file.content_type,
        "success": True
    }

    return http.JsonResponse(response_data)


def delete_data(request, course_pk, assignment_pk, data_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    data = get_object_or_404(competition.models.Data, pk=data_pk)
    if assignment.course != course or course.tutor != request.user or data.competition != assignment.competition:
        return http.HttpResponseForbidden()

    data.delete()
    return http.HttpResponseRedirect(reverse('course:edit_data', args=(course_pk, assignment_pk)))


@require_POST
@login_required
def signup(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if course.open_signup or course.register_code == request.POST.get('code', ''):
        course.students.add(request.user)
        messages.success(request, _("You has successfully signed up for ") + course.name)
    else:
        messages.error(request, _("Your code is not correct"))
    return http.HttpResponseRedirect(reverse('course:view', args=(course.pk,)))


@login_required
def disapprove(request, course_pk, student_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not course.is_managed_by(request.user):
        return http.HttpResponseForbidden()
    student = get_object_or_404(User, pk=student_pk)
    course.students.remove(student)
    print(request.GET.get('ref'))
    return http.HttpResponseRedirect(request.GET.get('ref'), reverse('course:students', args=(course.pk, 1)))


class ViewStudents(CourseMixin, generic.ListView):
    paginate_by = 30
    template_name = "course/students.html"

    def dispatch(self, request, course_pk, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=course_pk)
        self.user = request.user

#        flag = (self.user == self.course.tutor) or (self.course.teaching_assistants.filter(pk=self.user.pk).exists())
        
#        if not flag:
#            return http.HttpResponseForbidden()
        return super(ViewStudents, self).dispatch(request, course_pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewStudents, self).get_context_data(**kwargs)
        context['active_users'] = self.request.session.get('active_users', active_user_count())
        return context

    def get_queryset(self):
        return self.course.students.all()

class ViewLeaderboard(CourseMixin, generic.TemplateView):
    paginate_by = 30
    template_name = "course/leaderboard.html"

    def dispatch(self, request, course_pk, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=course_pk)
        self.user = request.user
        flag = (self.user == self.course.tutor) or \
                            (self.course.teaching_assistants.filter(pk=self.user.pk).exists())

        if not flag:
            return http.HttpResponseForbidden()
        return super(ViewLeaderboard, self).dispatch(request, course_pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewLeaderboard, self).get_context_data(**kwargs)
        context['active_users'] = self.request.session.get('active_users', active_user_count())
        #context['course_rank'] = course_leaderboard_data(self.course)
        #context['course_rank'] = final_leaderboard_data(competition, competition.final_showwinners_count),(self.course)        

        #messages.info(self.request, self.course.competition.name)
        context['course_rank'] = course_leaderboard_data(self.course.competition, self.course)
        #messages.info(self.request, self.course.name)
        return context


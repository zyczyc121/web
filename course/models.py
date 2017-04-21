from django.db import models
from django.contrib.auth.models import User
import user.models
import competition.models
from ckeditor.fields import RichTextField
import os.path
import uuid
from django.utils import timezone


def resource_file_name(instance, filename):
    return os.path.join(str(uuid.uuid4()) + "_" + filename)

class Course(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    tutor_name = models.CharField(max_length=50, blank=True)
    tutor = models.ForeignKey(User, related_name="tutor_courses")
    competition = models.ForeignKey(competition.models.Competition)
    teaching_assistants = models.ManyToManyField(User, related_name="ta_courses", blank=True)
    school = models.CharField(max_length=50)
    logo = models.ImageField(upload_to=resource_file_name, blank=True)

    name_en = models.CharField(max_length=100, null=True)
    description_en = models.TextField(null=True)
    school_en = models.CharField(max_length=100, null=True)
    invisible = models.BooleanField(default=False)

    create_datetime = models.DateTimeField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    students = models.ManyToManyField(User, related_name="attend_courses", blank=True)
    open_navigate = models.BooleanField(default=True)
    open_signup = models.BooleanField(default=False)
    register_code = models.CharField(unique=True,max_length=12)

    def __str__(self):
        return self.name + " By " + self.tutor.info.display_name

    def open_assignments(self):
        return self.assignments().filter(open=True)

    def is_active(self):
        return timezone.now() < self.end_datetime and timezone.now() >= self.start_datetime

    def is_over(self):
        return timezone.now() > self.end_datetime

    def is_managed_by(self, u):
        return self.tutor == u or self.teaching_assistants.filter(pk=u.pk).exists()


class Announcement(models.Model):
    title = models.CharField(max_length=50)
    content = RichTextField()
    publisher = models.ForeignKey(User)
    publish_datetime = models.DateTimeField()

    def __str__(self):
        return self.course.name + ": " + self.title


class Assignment(models.Model):
    title = models.CharField(max_length=50)
    description = RichTextField()

    course = models.ForeignKey(Course, related_name="assignments")
    open = models.BooleanField(default=True)
    create_datetime = models.DateTimeField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    competition = models.ForeignKey(competition.models.Competition)

    def __str__(self):
        return self.course.name + ": " + self.title


class PendingSignUp(models.Model):
    course = models.ForeignKey(Course)
    student = models.ForeignKey(User)

    student_number = models.CharField(max_length=20, null=True)
    real_name = models.CharField(max_length=50, null=True)
    description = models.TextField(max_length=50, null=True)

    signup_datetime = models.DateTimeField()
    remote_addr = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return self.student.info.name + ' : ' + self.course.name


class Team(models.Model):
    assignment = models.ForeignKey(Course)

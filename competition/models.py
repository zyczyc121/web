import os.path
import uuid
import datetime

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.files.storage import FileSystemStorage
from django.core import validators


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


# Storages
data_storage = FileSystemStorage(settings.DATA_ROOT)
submission_storage = FileSystemStorage(settings.SUBMISSION_ROOT)
truth_storage = FileSystemStorage(settings.TRUTH_ROOT)


def resource_file_name(instance, filename):
    return os.path.join(str(uuid.uuid4()) + "_" + filename)


def truth_file_name(instance, filename):
    return os.path.join(instance.name, filename)


class Competition(models.Model):
    CHAMPIONSHIP = 1
    KNOWLEDGE = 2
    category_choice = (
        (CHAMPIONSHIP, "Championship"),
        (KNOWLEDGE, "Knowledge")
    )

    evaluation_choice = (
        ('AUC', 'Area Under ROC Curve'),
        ('RMSE', 'Root of Mean Square Error'),
        ('PRECISION', 'Precision'),
        ('RECALL', 'Recall'),
        ('ACCURACY', 'Accuracy'),
        ('MAP', 'Mean Average Precision'),
        ('NDCG', 'Normalized Discounted Cumulative Gain'),
        ('SMP', 'SMP cup 2016'),
        ('SOHU', 'Sohu Luckydata')
    )

    uid = models.CharField(max_length=50,db_index = True, unique=True, null=True)

    name = models.CharField(max_length=50)
    name_en = models.CharField(max_length=100, null=True)
    description = models.TextField(blank=True)
    description_en = models.TextField(null=True, blank=True)
    host = models.ForeignKey(User, related_name='host_competitions')
    category = models.IntegerField(choices=category_choice)
    award = models.CharField(max_length=10, blank=True)
    sponsor = models.CharField(max_length=100, blank=True)
    sponsor_en = models.CharField(max_length=100, blank=True)

    start_datetime = models.DateTimeField()
    final_submit_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    finalCaculate_datetime = models.DateTimeField(null=True)
    ShowWinner_datetime = models.DateTimeField(null=True)
    valid_end_datetime = models.DateTimeField(null=True)
    winner_start_datetime = models.DateTimeField(null=True)
    winner_end_datetime = models.DateTimeField(null=True)

    max_team_size = models.IntegerField(default=10,
                                        validators=[validators.MinValueValidator(1),
                                                    validators.MaxValueValidator(100)])


    allow_overdue_submission = models.BooleanField()
    invisible = models.BooleanField(default=False)
    submit_per_day = models.IntegerField(default=5)
    final_submit_count = models.IntegerField(default=2)
    final_showwinners_count = models.IntegerField(default=50)
    week_winnernum = models.IntegerField(default=1)
    final_showscore_min = models.FloatField(default=0.5)
    evaluation = models.CharField(max_length=10, choices=evaluation_choice)
    evaluate_reverse = models.BooleanField(default=False)
    num_line = models.IntegerField()
    final_num_line = models.IntegerField(null=True)
    public_ratio = models.IntegerField()
    public_truth = models.FileField(upload_to=truth_file_name, storage=truth_storage)
    private_truth = models.FileField(upload_to=truth_file_name, storage=truth_storage)
    filetype = models.CharField(max_length=10, default='csv')

    introduction = RichTextUploadingField()
    introduction_en = RichTextUploadingField(null=True)
    rules = RichTextUploadingField()
    rules_en = RichTextUploadingField(null=True)
    data_description = RichTextUploadingField()
    data_description_en = RichTextUploadingField(null=True)
    winners = RichTextUploadingField(null=True,blank=True)
    winners_en = RichTextUploadingField(null=True,blank=True)

    logo = models.ImageField(upload_to=resource_file_name, blank=True)
    banner = models.ImageField(upload_to=resource_file_name, blank=True)

    participants = models.ManyToManyField(User, through='Participation', through_fields=('competition', 'user'),
                                          related_name='participate_competitions')

    def last_refresh_time(self):
        now = timezone.now()
        delta = datetime.timedelta(days=(now - self.start_datetime).days)
        return self.start_datetime + delta

    def next_refresh_time(self):
        now = timezone.now()
        delta = datetime.timedelta(days=(now - self.start_datetime).days + 1)
        return self.start_datetime + delta

    def ongoing_days(self):
        return (timezone.now() - self.start_datetime).days + 1

    def is_active(self):
        return timezone.now() < self.end_datetime and timezone.now() >= self.start_datetime

    def is_over(self):
        return timezone.now() > self.end_datetime

    def __str__(self):
        return self.name

    @staticmethod
    def active_competitions():
        now = timezone.now()
        Competition.objects.filter(start_datetime_lte=now, end_datetime_gt=now)

    def has_participant(self, user):
        return self.participants.filter(pk=user.pk).exists()

    def find_team_of_user(self, user):
        try:
            team = Participation.objects.filter(user=user, competition=self).get().team
            return team

        except ObjectDoesNotExist:
            return None


class Team(models.Model):
    members = models.ManyToManyField(User, through='Participation', through_fields=('team', 'user'),
                                     related_name="teams")
    leader = models.ForeignKey(User)
    competition = models.ForeignKey(Competition, related_name="teams")

    name = models.CharField(max_length=20)
    create_datetime = models.DateTimeField()

    final_score = models.FloatField(blank=True)
    final_submission_path = models.FilePathField(blank=True)
    final_submission_name = models.FilePathField(blank=True)

    def submission_count_today(self):
        return self.submissions.filter(submit_datetime__gte=self.competition.last_refresh_time(), status__lte=2, final_submit=False).count()

    def final_submission_count_today(self):
        return self.submissions.filter(submit_datetime__gte=self.competition.last_refresh_time(), status__lte=2, final_submit=True).count()

    def submissions(self):
        return Submission.objects.filter(competition=self.competition,
                                         user__in=self.members.all())

    def submission_left_today(self):
        return self.competition.submit_per_day - self.submission_count_today()

    def submission_count_total(self):
        return self.submissions.filter(status__lte=2).count()

    def size(self):
        return self.members.count()

    def is_single(self):
        return self.members.count() == 1

    def __str__(self):
        return self.name + " : " + self.competition.name


class Timeline(models.Model):
    competition = models.ForeignKey(Competition)
    name = models.CharField(max_length=50)
    mark_datetime = models.DateTimeField()


class Detail(models.Model):
    competition = models.ForeignKey(Competition)
    title = models.CharField(max_length=50)
    content = RichTextUploadingField()
    slug = models.SlugField()
    order = models.IntegerField()
    title_en = models.CharField(max_length=50, null=True)
    content_en = RichTextUploadingField(null=True)

    class Meta:
        unique_together = ('competition', 'slug')

    def __str__(self):
        return self.competition.name + ' - ' + self.title


class Data(models.Model):
    competition = models.ForeignKey(Competition, related_name="data")
    content = models.FileField(upload_to=resource_file_name, storage=data_storage, null=True, blank=True)
    baidu_url = models.URLField(blank=True)
    baidu_code = models.CharField(blank=True, max_length=5)
    dropbox_url = models.URLField(blank=True)

    name = models.CharField(max_length=50)
    size = models.BigIntegerField()

    filetype = models.CharField(max_length=10)

    class Meta:
        unique_together = (
            ('competition', 'name')
        )


class Participation(models.Model):
    competition = models.ForeignKey(Competition)
    user = models.ForeignKey(User)
    team = models.ForeignKey('Team', null=True, blank=True)
    join_datetime = models.DateTimeField()

    def __str__(self):
        return self.user.username + ' : ' + self.competition.name

    class Meta:
        unique_together = (
            ('competition', 'user'),
        )


class Submission(models.Model):
    PENDING = 1
    SUCCESS = 2
    ERROR = 3
    status_choices = (
        (PENDING, 'pending'),
        (SUCCESS, 'success'),
        (ERROR, 'error'),
    )
    content = models.FileField(upload_to=resource_file_name, storage=submission_storage)
    user = models.ForeignKey(User, related_name="submissions")
    competition = models.ForeignKey(Competition, related_name="submissions")
    team = models.ForeignKey(Team, related_name="submissions")

    description = models.CharField(max_length=100)
    display_name = models.CharField(max_length=255)
    submit_datetime = models.DateTimeField()
    message = models.CharField(max_length=50, blank=True)
    final_submit = models.BooleanField(default=False)
    public_score = models.FloatField()
    private_score = models.FloatField()
    remote_addr = models.GenericIPAddressField(blank=True, null=True)

    status = models.IntegerField(choices=status_choices)

    def get_team(self):
        return self.user.teams.get(competition=self.competition)

    def is_editable(self, u):
        return self.user == u or self.get_team().leader == u

    def __str__(self):
        return self.user.username + ", " + self.get_team().name + ', ' + str(self.public_score)


class Leaderboard(models.Model):
    managed = False
    db_table = 'leaderboard'

    team = models.ForeignKey(Team)
    num_submission = models.IntegerField()
    score = models.FloatField()
    submission_datetime = models.DateTimeField()

class Winner_week(models.Model):
    competition = models.ForeignKey(Competition)
    week_num = models.IntegerField()

    team = models.ForeignKey(Team)
    team_name = models.CharField(max_length=255)
    leader =  models.ForeignKey(User)
    leader_name = models.CharField(max_length=255)

    single = models.IntegerField()
    members = models.TextField(null=True)
    score = models.FloatField()

class Sub_limt(models.Model):
    competition = models.ForeignKey(Competition)
    user = models.ForeignKey(User)
    is_valid = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)


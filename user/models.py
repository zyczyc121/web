from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="info")
    display_name = models.CharField(max_length=30)
    real_name = models.CharField(max_length=50, null=True)
    organization = models.TextField(max_length=500, null=True)

    remote_addr = models.GenericIPAddressField(blank=True, null=True)
    last_visit = models.DateTimeField(null=True)    

    receive_update = models.BooleanField()
    avatar = models.ImageField(upload_to="image/avatar", blank=True)

    bio = models.TextField(max_length=500, blank=True)
    personal_tag = models.CharField(max_length=200, blank=True)
    occupation = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    province = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)

    website_url = models.CharField(max_length=255, blank=True)
    github_account = models.CharField(max_length=50, blank=True)
    twitter_account = models.CharField(max_length=50, blank=True)
    linkedin_url = models.CharField(max_length=255, blank=True)

    PENDING = 1
    ACTIVE = 2
    FORBIDDEN = 3
    status_choice = (
        (PENDING, "pending"),
        (ACTIVE, "active"),
        (FORBIDDEN, "forbidden")
    )

    status = models.IntegerField(choices=status_choice)

    def __str__(self):
        return self.user.username + " : " + self.display_name


class Skill(models.Model):
    label = models.CharField(max_length=20, db_index=True)
    category = models.IntegerField(db_index=True)
    users = models.ManyToManyField(User, related_name="skills")


class Tool(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    users = models.ManyToManyField(User, related_name="tools")

    def __str__(self):
        return self.name


class Interest(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    users = models.ManyToManyField(User, related_name="interests")

    def __str__(self):
        return self.name


class UserModification(models.Model):
    ACTIVATION = 1
    RESET_PASSWORD = 2
    JOIN_TEAM = 3

    action_choice = (
        (ACTIVATION, "activation"),
        (RESET_PASSWORD, "reset password"),
        (JOIN_TEAM, "join team")
    )

    user = models.ForeignKey(User)
    key = models.CharField(max_length=128)
    action = models.IntegerField(choices=action_choice)
    expire_datetime = models.DateTimeField()

    arg1 = models.IntegerField(blank=True, null=True)
    arg2 = models.IntegerField(blank=True, null=True)

    class Meta:
        index_together = [
            ["user", "action"],
        ]

class UserModifyProfile(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField(max_length=30)
    modify_datetime = models.DateTimeField()

    modify_before = models.TextField(max_length=500, blank=True)
    modify_after = models.TextField(max_length=500, blank=True)
    remote_addr = models.GenericIPAddressField(blank=True, null=True)

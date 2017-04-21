from django.contrib import admin

from .models import *


# Register your models here.

class UserInfoInline(admin.StackedInline):
    model = UserInfo

class UserAdmin(admin.ModelAdmin):
    inlines = [UserInfoInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
#admin.site.register(UserInfo)
admin.site.register(UserModification)
admin.site.register(Interest)
admin.site.register(Skill)
admin.site.register(Tool)
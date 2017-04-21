from django.contrib import admin

# Register your models here.
from competition.models import *


# @admin.register(Detail)
# class DetailAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ("title",)}


class DetailInline(admin.StackedInline):
    model = Detail
    fields = ('order',  'title', 'slug', 'content', 'title_en', 'content_en')

class DataInline(admin.StackedInline):
    model = Data


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    inlines = [DataInline, DetailInline]


admin.site.register(Category)
admin.site.register(Timeline)
admin.site.register(Team)
admin.site.register(Participation)
admin.site.register(Submission)

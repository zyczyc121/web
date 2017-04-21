"""gaggle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import gaggle.views

urlpatterns = [
                  url(r'^$|^index/$', gaggle.views.index, name='index'),
                  url(r'^privacy/', gaggle.views.privacy, name='privacy'),
                  url(r'^terms/', gaggle.views.terms, name='terms'),
                  url(r'^contact/', gaggle.views.contact, name='contact'),
                  url(r'^about/', gaggle.views.about, name='about'),
                  url(r'^admin/', include(admin.site.urls)),
                  url(r'^competition/', include('competition.urls', namespace='competition')),
                  url(r'^user/', include('user.urls', namespace='user')),
                  url(r'^course/', include('course.urls', namespace='course')),
                  url(r'^forum/', include('pybb.urls', namespace='pybb')),
                  url(r'^i18n/', include('django.conf.urls.i18n')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# CKEditor
urlpatterns += [
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
]

# Captcha
urlpatterns += [
    url(r'^ captcha/', include('captcha.urls')),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

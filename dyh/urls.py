# -*- coding:utf-8 -*-
from django.views import static
from django.contrib import admin
from django.conf.urls import url

from dyh import settings
from dyh import views

admin.autodiscover()

urlpatterns = [
    url(r'^$', views.home),
    url(r'^admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT}),
]

urlpatterns += [
    url(r'^(?P<url_factor>.*)/$', views.default), # 微信后台配置的回掉请求的处理
]

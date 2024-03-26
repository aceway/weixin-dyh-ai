#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: ./admin.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月24日 星期六 14时56分48秒
#  Description: ...
# 
########################################################################

from django.contrib import admin
from dyh.settings import ITEM_CNT_PER_ADMIN_PAGE

from dyh.ai.models import AIVender
from dyh.ai.models import AIModelType
from dyh.ai.models import AIModel
from dyh.ai.models import WXAIConfig
from dyh.ai.models import DyhAIConfig
from dyh.ai.models import ActiveAIConfig

class AIVenderAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'add_time', )
    list_display    = ('id', 'name', 'tag', 'is_active', 'office_site', 'product_site', 'add_time',)
    search_fields   = ('name', 'tag', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    list_filter = ['is_active', ]
    date_hierarchy = 'add_time'
admin.site.register(AIVender, AIVenderAdmin)

class AIModelTypeAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'add_time', 'used_times')
    list_display    = ('id', 'name', 'tag', 'used_times', 'add_time',)
    search_fields   = ('name', 'tag', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
admin.site.register(AIModelType, AIModelTypeAdmin)

class AIModelAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'used_times', 'add_time', )
    list_display    = ('id', 'vender', 'the_type', 'tag', 'name', 'is_active', 'used_times', 'add_time', 'URL', 'doc_url')
    search_fields   = ('name', 'tag', 'URL', 'doc_url', 'config_json', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
    list_filter = ['vender', 'is_active', 'the_type']
admin.site.register(AIModel, AIModelAdmin)

class WXAIConifgAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'used_times', 'ok_times', 'failed_times', 'add_time', 'last_used_time' , )
    list_display    = ('id', 'used_times', 'ok_times', 'failed_times', 'vender', 'owner', 'is_active', 'start_time', 'end_time', 'last_used_time', 'add_time',)
    search_fields   = ('KEY', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
    list_filter = ['vender', 'owner', 'is_active', ]
admin.site.register(WXAIConfig, WXAIConifgAdmin)

class DyhAIConifgAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'used_times', 'ok_times', 'failed_times', 'add_time', 'last_used_time' , )
    list_display    = ('id', 'used_times', 'ok_times', 'failed_times', 'vender', 'owner', 'is_active', 'start_time', 'end_time', 'last_used_time', 'add_time',)
    search_fields   = ('KEY', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
    list_filter = ['vender', 'owner', 'is_active', ]
admin.site.register(DyhAIConfig, DyhAIConifgAdmin)

class ActiveAIConfigAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'used_times', 'ok_times', 'failed_times', 'add_time', 'last_used_time', )
    list_display    = ('id', 'active_name', 'used_times', 'ok_times', 'failed_times', 'vender', 'is_active', 'closed_times', 'user_limit_times', 'start_time', 'end_time', 'last_used_time', 'add_time',)
    search_fields   = ('KEY', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
    list_filter = ['vender', 'is_active', ]
admin.site.register(ActiveAIConfig, ActiveAIConfigAdmin)

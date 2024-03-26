# -*- coding=utf-8 -*-
from django.contrib import admin
from dyh.dyh_mgr.models import WXUser
from dyh.dyh_mgr.models import SysCfg
from dyh.dyh_mgr.models import WXDyhMgr
from dyh.dyh_mgr.models import WXDingYueHao
from dyh.settings import ITEM_CNT_PER_ADMIN_PAGE

# Register your models here.

# class SysCfgAdmin(admin.ModelAdmin):
#     readonly_fields =('id', 'add_time')
#     list_display    = ('id',  'name', 'stat', 'key', 'value', 'add_time')
#     search_fields   = ('name', 'key', 'value', 'remark')
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'add_time'
#     list_filter = ['stat']
# admin.site.register(SysCfg, SysCfgAdmin)

class WXUserAdmin(admin.ModelAdmin):
    readonly_fields =('id', 'wx_dyh', 'wx_openid', 'join_time' )
    list_display    = ('id', 'wx_dyh', 'wx_openid', 'wx_nicname', 'disable','enable_ai', 'always_ai', 'vav', 'voice_idx', 'use_ai_times', 'join_time')
    search_fields   = ('wx_dyh', 'wx_openid', 'wx_nicname', )
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    list_filter = ['wx_dyh', 'disable', 'enable_ai', 'always_ai', 'vav']
    date_hierarchy = 'join_time'
admin.site.register(WXUser, WXUserAdmin)

class WXDYHAdmin(admin.ModelAdmin):
    readonly_fields =('id', 'access_token', 'at_time','last_verify_time', 'at_seconds', 'verify_times', 'first_verify_time')
    list_display    = ('id', 'dyh_account', 'dyh_nicname', 'rawid', 'url_factor', 'dyh_appid', 'verify_times', 'first_verify_time', 'last_verify_time', 'at_time', 'at_seconds')
    search_fields   = ('dyh_account', 'dyh_nicname', 'url_factor', 'token', 'aeskey')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'last_verify_time'
    list_filter = ['first_verify_time']
admin.site.register(WXDingYueHao, WXDYHAdmin)

class WXDyhMgrAdmin(admin.ModelAdmin):
    readonly_fields =('id', )
    list_display    = ('id',  'wx_user', 'is_active', 'add_time')
    search_fields   = ('remark', )
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'add_time'
    list_filter = ['is_active', 'wx_user',]
admin.site.register(WXDyhMgr, WXDyhMgrAdmin)

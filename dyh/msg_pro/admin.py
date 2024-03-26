# -*- coding:utf-8 -*-
from django.contrib import admin
from dyh.msg_pro.models import WXUserMsgText
from dyh.msg_pro.models import WXUserMsgImage
from dyh.msg_pro.models import WXUserMsgVoice
from dyh.msg_pro.models import WXUserMsgVideo
from dyh.msg_pro.models import WXUserMsgShortVideo
from dyh.msg_pro.models import WXUserMsgLocation
from dyh.msg_pro.models import WXUserMsgLink

from dyh.msg_pro.models import WXUserEventSubscribe
from dyh.msg_pro.models import WXUserEventMenu

from dyh.msg_pro.models import WXUserEventScan
from dyh.msg_pro.models import WXUserEventLocation
from dyh.msg_pro.models import WXUserEventClick

from dyh.settings import ITEM_CNT_PER_ADMIN_PAGE

# Register your models here.

class WXUserEventSubscribeAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'wx_user', 'response', 'nonce', 'event_type', 'msg_time', 'rsp_time')
    list_display    = ('id', 'wx_user', 'event_type', 'msg_time', 'rsp_time', 'response')
    search_fields   = ('wx_user', 'response', 'remark',)
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'msg_time'
    list_filter = ['wx_user', 'event_type']
admin.site.register(WXUserEventSubscribe, WXUserEventSubscribeAdmin)

class WXUserEventMenuAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'wx_user', 'response', 'rsp_fmt', 'msg_md5', 'msg_type', 'content', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'remark', 'event_type', 'event_key')
    list_display    = ('id', 'wx_user', 'event_type', 'msg_time')
    search_fields   = ('wx_user',)
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'msg_time'
    list_filter = ['wx_user', 'event_type', ]
admin.site.register(WXUserEventMenu, WXUserEventMenuAdmin)

class WXUserMsgTextAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'wx_user','msg_md5', 'msg_type', 'content', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'remark')
    list_display    = ('id', 'wx_user',  'msg_type', 'rsp_fmt', 'model_id','wx_notify_times','rsp_len', 'rsp_offset', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'msg_md5','msg_id', 'nonce', )
    search_fields   = ('content', 'response', 'model_id', 'msg_id', 'msg_md5', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'msg_time'
    list_filter = ['wx_user', 'with_ai', 'model_id']
admin.site.register(WXUserMsgText, WXUserMsgTextAdmin)

class WXUserMsgVoiceAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'wx_user','msg_md5', 'msg_type', 'content', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'format', 'url','media_id', 'idx', 'msg_dataid', 'save_path',  'nonce', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'remark')
    list_display    = ('id', 'wx_user',  'msg_type', 'rsp_fmt', 'model_id','wx_notify_times','rsp_len', 'rsp_offset', 'content', 'response', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'msg_md5','msg_id', 'nonce', 'remark')
    search_fields   = ('msg_md5', 'content', 'response', 'remark', )
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'msg_time'
    list_filter = ['wx_user', 'with_ai', 'model_id']
admin.site.register(WXUserMsgVoice, WXUserMsgVoiceAdmin)

class WXUserMsgImageAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'wx_user','msg_md5', 'content', 'pic_url', 'media_id', 'idx', 'msg_dataid', 'save_path', 'rsp_time', 'notify_time', 'response', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'bk_done_time', 'remark')
    list_display    = ('id', 'wx_user',  'msg_type', 'rsp_fmt', 'model_id','wx_notify_times','rsp_len', 'rsp_offset', 'content', 'response', 'msg_time', 'notify_time', 'bk_done_time', 'rsp_time', 'msg_md5','msg_id', 'nonce', 'remark')
    search_fields   = ('save_path', 'pic_url', 'msg_md5', 'response', 'remark')
    list_per_page = ITEM_CNT_PER_ADMIN_PAGE
    date_hierarchy = 'msg_time'
    list_filter = ['wx_user', 'with_ai', 'model_id']
admin.site.register(WXUserMsgImage, WXUserMsgImageAdmin)

# class WXUserEventScanAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user', 'nonce', 'event_type', 'msg_time', 'event_key', 'ticket')
#     list_display    = ('id', 'wx_user', 'event_type', 'msg_time') 
#     search_fields   = ('wx_user',)
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'event_type']
# admin.site.register(WXUserEventScan, WXUserEventScanAdmin)
# 
# class WXUserEventLocationAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user', 'nonce', 'event_type', 'msg_time', 'latitude', 'longitude', 'precision')
#     list_display    = ('id', 'wx_user', 'event_type', 'msg_time')
#     search_fields   = ('wx_user',)
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'event_type']
# admin.site.register(WXUserEventLocation, WXUserEventLocationAdmin)
# 
# class WXUserEventClickAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user', 'nonce', 'event_type', 'msg_time', 'event_key')
#     list_display    = ('id', 'wx_user', 'event_type', 'msg_time')
#     search_fields   = ('wx_user',)
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'event_type', 'event_key']
# admin.site.register(WXUserEventClick, WXUserEventClickAdmin)
# 
# class WXUserMsgVideoAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user','msg_md5', 'content', 'response', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'bk_done_time', 'remark')
#     list_display    = ('id', 'wx_user', 'with_ai', 'content', 'response', 'remark', 'msg_time', 'bk_done_time', 'wx_notify_times',)
#     search_fields   = ('msg_md5', 'content', 'response', 'remark', )
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'with_ai', 'model_id']
# admin.site.register(WXUserMsgVideo, WXUserMsgVideoAdmin)
# 
# class WXUserMsgShortVideoAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user','msg_md5', 'content', 'response', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'bk_done_time', 'remark')
#     list_display    = ('id', 'wx_user', 'with_ai', 'content', 'response', 'remark', 'msg_time', 'bk_done_time', 'wx_notify_times',)
#     search_fields   = ('url', 'msg_md5', 'content', 'response', 'remark', )
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'with_ai', 'model_id']
# admin.site.register(WXUserMsgShortVideo, WXUserMsgShortVideoAdmin)
# 
# class WXUserMsgLocationAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user','msg_md5', 'content', 'response', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'bk_done_time', 'remark')
#     list_display    = ('id', 'wx_user', 'with_ai', 'content', 'response', 'remark', 'msg_time', 'bk_done_time', 'wx_notify_times',)
#     search_fields   = ('msg_md5', 'content', 'response', 'remark', )
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'with_ai', 'model_id']
# admin.site.register(WXUserMsgLocation, WXUserMsgLocationAdmin)
# 
# class WXUserMsgLinkAdmin(admin.ModelAdmin):
#     readonly_fields = ('id', 'wx_user','msg_md5', 'content', 'url', 'response', 'msg_id','wx_notify_times', 'with_ai', 'model_id', 'nonce', 'msg_time', 'bk_done_time', 'remark')
#     list_display    = ('id', 'wx_user', 'with_ai', 'content', 'response', 'remark', 'msg_time', 'bk_done_time', 'wx_notify_times',)
#     search_fields   = ('url', 'msg_md5', 'content', 'response', 'remark', )
#     list_per_page = ITEM_CNT_PER_ADMIN_PAGE
#     date_hierarchy = 'msg_time'
#     list_filter = ['wx_user', 'with_ai', 'model_id']
# admin.site.register(WXUserMsgLink, WXUserMsgLinkAdmin)

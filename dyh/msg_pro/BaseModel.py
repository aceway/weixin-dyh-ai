# -*- coding:utf-8 -*-
import sys
import time
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

from datetime import datetime

from django.db import models
from django.db import IntegrityError
from django.utils import timezone

from dyh.settings import RSP_MAX_LEN
from dyh.settings import SAVE_MAX_LEN

from dyh.settings import WX_RETURN_TXT
from dyh.settings import WX_RETURN_IMG
from dyh.settings import WX_RETURN_IMG_TXT
from dyh.settings import WX_RETURN_VOICE

from dyh.settings import WX_FIXED_FIELD_TAGS

from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import MSG_TYPE_TAG_IMAGE
from dyh.settings import MSG_TYPE_TAG_VOICE
from dyh.settings import MSG_TYPE_TAG_VIDEO
from dyh.settings import MSG_TYPE_TAG_SHORTVIDEO
from dyh.settings import MSG_TYPE_TAG_LOCATION
from dyh.settings import MSG_TYPE_TAG_LINK

from dyh.settings import EVENT_TYPE_TAG_SUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_UNSUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_SCAN
from dyh.settings import EVENT_TYPE_TAG_LOCATION
from dyh.settings import EVENT_TYPE_TAG_CLICK

from dyh.ai.models import AIModel
from dyh.dyh_mgr.models import WXUser

RSP_TXT_NO_ERROR = 0
RSP_TXT_EMPTY = 1
RSP_TXT_OVER = 2
RSP_TXT_NONE = 3

class WXUserMsgBaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    wx_user  = models.ForeignKey(WXUser, to_field="wx_openid", verbose_name='用户',help_text='微信订阅号用户', on_delete=models.CASCADE)
    nonce    = models.CharField(max_length=128, verbose_name='Nonce',help_text='消息的nonce')
    msg_id   = models.CharField(unique=True, max_length=64, verbose_name='消息ID',help_text='普通消息ID，事件没有则构造: msgType-eventType-tamstamp')
    msg_type = models.CharField(max_length=32, verbose_name='消息类型',help_text='微信消息类型')
    msg_time = models.DateTimeField(auto_now_add=True, verbose_name='首创时间', help_text='首次收消息的时间, 微信可能重复发送，最多三次')
    wx_notify_times = models.PositiveIntegerField(default=0, verbose_name='微信通知次数', help_text='同样问题微信通知消息次数 - 用户发同样的问题也算，或不ACK微信会重试')
    notify_time = models.DateTimeField(blank=None, null=True, verbose_name='最近通知时间', help_text='微信通知通知时间, 重复通知时更新')
    content  = models.TextField(max_length=4096, default="", verbose_name='发送的消息', help_text='发送的消息')
    msg_md5  = models.CharField(max_length=32, verbose_name='请求MD5', help_text='用户发送请求内容的MD5，用于避免重复像AI请求')
    with_ai  = models.BooleanField(default=False, verbose_name='和AI对话', help_text='消息是否发给AI的')
    model_id = models.CharField(max_length=64, default='-', verbose_name='应答的模型',help_text='模型ID, 用于和AI交流的，不唯一，允许配置不同参数的记录存在，方便切换')
    response = models.TextField(default="", verbose_name='回复的消息', help_text='针对comment的回复-应答消息')
    bk_done  = models.BooleanField(default=False, verbose_name='后台处理消息完毕', help_text='后台处理消息完毕，则前台可用于返回给用户')
    bk_done_time = models.DateTimeField(blank=None, null=True, verbose_name='AI答复时间', help_text='答复消息时间-AI response')
    rsp_fmt  = models.CharField(max_length=32, default="TEXT", verbose_name='回复消息的格式', help_text='回复消息的格式')
    rsp_done = models.BooleanField(default=False, verbose_name='返回消息完毕', help_text='前台已经讲消息完毕发送给用户完毕')
    rsp_time = models.DateTimeField(blank=None, null=True, verbose_name='回用户时间', help_text='答复事件时间-this sys TO User')
    rsp_len  = models.PositiveIntegerField(default=0, verbose_name='要回复内容的总长度', help_text='回复给发送者消息的长度')
    rsp_offset = models.PositiveIntegerField(default=0, verbose_name='已回复内容的长度', help_text='回复给发送者的消息的进度-response中发完的字节量，用于长消息续传')
    remark  = models.TextField(max_length=1024, verbose_name='备注', help_text='备注')

    class Meta:
        abstract = True

    # def msg_time_formatted(self, obj):
    #     return obj.msg_time.strftime("%Y-%m-%d %H:%M:%S")

    # def notify_time_formatted(self, obj):
    #     return obj.notify_time.strftime("%Y-%m-%d %H:%M:%S")

    # def bk_done_time_formatted(self, obj):
    #     return obj.bk_done_time.strftime("%Y-%m-%d %H:%M:%S")

    # def rsp_time_formatted(self, obj):
    #     return obj.rsp_time.strftime("%Y-%m-%d %H:%M:%S")

    def get_msg_type(self):
        return self.msg_type.strip().upper()

    def get_event_type(self):
        if hasattr(self, 'event_type'):
            return self.event_type.strip().upper()
        else:
            return ""

    def get_msg_id(self):
        if hasattr(self, 'msg_id'):
            return self.msg_id
        else:
            if hasattr(self, 'event_type'):
                return "{m}-{e}-{i}".format(m=self.msg_type, e=self.event_type, i=self.msg_time.timestamp())
            else:
                return "{m}-{i}".format(m=self.msg_type, i=self.msg_time.timestamp())
        return self.msg_type.strip().upper()

    def __str__(self):
        return "[dbid:{i}][{t}-{rt}][{m}][{u}]{c}."\
            .format(i=self.id, t=self.msg_type, rt=self.rsp_fmt, m=self.msg_id, u=self.wx_user, c=self.content[:6])

    def get_text_msg(self):
        if self.get_msg_type() == MSG_TYPE_TAG_TEXT:
            return self
        else:
            from dyh.msg_pro.models import  WXUserMsgText
            the_txt_msg = WXUserMsgText.objects.filter(msg_id = self.msg_id).order_by("-id")[:1]
            if the_txt_msg.count() == 1:
                return the_txt_msg[0]
            else:
                return None

    def total_lost_seconds(self):
        if self.msg_time:
            return round( timezone.now().timestamp() - self.msg_time.timestamp(), 1)
        else:
            return -1

    def this_lost_seconds(self):
        if self.notify_time:
            return round( timezone.now().timestamp() - self.notify_time.timestamp(), 1)
        else:
            return -1

    def bk_done_cost_seconds(self):
        if self.bk_done_time:
            return round( timezone.now().timestamp() - self.bk_done_time.timestamp(), 1)
        else:
            return -1

    def rsp_done_cost_seconds(self):
        if self.rsp_time:
            return round( timezone.now().timestamp() - self.rsp_time.timestamp(), 1)
        else:
            return "-1"

    def get_timeout_tip(self, toal_max_seconds=14, round_max_seconds=5):
        if self.total_lost_seconds() - toal_max_seconds > 0:
            return "系统处理中，请稍后来发送 '继续' 查看本次的处理结果"
        elif self.wx_notify_times == 3 and (timezone.now().timestamp() - self.notify_time.timestamp()) > round_max_seconds:
            return "处理中，请耐心等候"
        else:
            return None

    def parse_as_help_cmd(self):
        """
        return help text or None
        """
        from dyh.msg_pro import utils
        text = self.get_content()
        return utils.get_help_cmd_text(text)

    def parse_as_sys_cmd(self):
        """
        return sys cmd text or None
        """
        from dyh.msg_pro import utils
        text = self.get_content()
        return utils.get_sys_cmd_text(text)

    def is_media_msg(self):
        return hasattr(self, 'media_id')

    def is_event_msg(self):
        return hasattr(self, 'event_type')

    def get_manager_tip(self):
        if not self.wx_user.is_manager():
            return ""

        tip = "[did:{i}, {n} times, this {t}s, toal {tt}s,bk:{b}s,rsp:{f}s, AI:{a}]\n"\
            .format(i=self.id,n=self.wx_notify_times, t=self.this_lost_seconds(), \
                    tt=self.total_lost_seconds(), b=self.bk_done_cost_seconds(),
                    f=self.rsp_done_cost_seconds(), a=self.with_ai)
        return tip

    def get_media_id(self):
        if self.is_event_msg():
            return self.media_id
        else:
            return None

    def get_event_msg(self):
        return hasattr(self, 'event_type')

    def get_content(self):
        return self.content

    def get_full_response(self):
        return self.response

    def get_response_fragment(self, fragment_max_len = RSP_MAX_LEN,  rollback=False):
        result = {'error': None, 'desc': None, 'response': None}
        update_fields = []
        while True:
            if self.rsp_len == 0:
                result['error'] = RSP_TXT_EMPTY
                result['desc'] = "没有未回答完的信息了"
                result['response'] = ""
                break

            if self.rsp_len > 0 and self.rsp_offset >= self.rsp_len:
                result['error'] = RSP_TXT_OVER
                result['desc'] = "已经全部回复完，没有更多了!"
                result['response'] = "."
                break

            start = self.rsp_offset
            end = start  + fragment_max_len
            rsp_txt = self.response[ self.rsp_offset :  end ]
            idx = rsp_txt.rfind(' ')
            if idx > 0 and fragment_max_len - idx < 10:
                rsp_txt = rsp_txt[ : idx]
                end = start + idx
            self.incr_rsp_offset(len(rsp_txt))

            if self.rsp_len > fragment_max_len:
                # 一次回复不完的，给予提示
                if end < self.rsp_len:
                    end_tip = '\n(未完 .. 继续)'
                else:
                    end_tip = '\n(完)'
                rsp_txt += end_tip
                result['desc'] = end_tip.strip()
            else:
                result['desc'] = "OK"

            result['error'] = RSP_TXT_NO_ERROR
            result['response'] = rsp_txt
            break
            # end of while True

        if self.rsp_offset >= self.rsp_len:
            self.finish_response_process()

        if rollback and self.rsp_offset >= self.rsp_len:
            self.reset_rsp_offset()
            if 'rsp_offset' not in update_fields:
                update_fields.append('rsp_offset')

        if len(update_fields) > 0:
            self.save(update_fields=update_fields)

        if VERBOSE_LOG:
            logger.info("get_response_fragment: {m}: {r}".format(m=self, r=result))
        return result

    def incr_wx_notify_times(self, delta=1):
        update_fields = []
        update_fields.append('notify_time')
        self.notify_time = timezone.now()

        if self.wx_notify_times == 0:
            update_fields.append('msg_time')
            self.msg_time = self.notify_time

        update_fields.append('wx_notify_times')
        self.wx_notify_times += delta
        self.save(update_fields=update_fields)

    def incr_rsp_offset(self, ln):
        self.rsp_time = timezone.now()
        self.rsp_offset += ln
        self.save()

    def reset_rsp_offset(self):
        self.rsp_offset = 0
        self.rsp_done = False
        self.save()

    def finish_background_process_with_response(self, response):
        """
        结束后台处理任务的， 但不干预前台取数据(rsp_offset)的任务
        """
        rsp_len = len(response)
        update_fields = ['response']
        self.response = response

        update_fields.append('bk_done')
        self.bk_done = True

        update_fields.append('bk_done_time')
        self.bk_done_time = timezone.now()

        self.rsp_len = rsp_len
        update_fields.append('rsp_len')

        if self.rsp_offset > rsp_len:
            self.rsp_offset = rsp_len
            update_fields.append('rsp_offset')

        self.save(update_fields=update_fields)
        return True

    def finish_response_process(self):
        """
        结束，不代表取完数据，需要进一步根据 rsp_offset 判断
        """
        update_fields = ['rsp_done']
        self.rsp_done = True

        update_fields.append('rsp_time')
        self.rsp_time = timezone.now()

        update_fields.append('rsp_len')
        self.rsp_len = len(self.response)

        update_fields.append('rsp_offset')
        self.rsp_offset = len(self.response)

        self.save(update_fields=update_fields)
        #self.refresh_from_db()

    def format4rsp2wx_user(self, force=False, rollback=False):
        response = None
        result = self.get_response_fragment(rollback=rollback)
        if result and int(result.get('error', -1)) == RSP_TXT_NO_ERROR:
            response = result['response']
        elif force and result and result.get('response', None):
            response = result['response']
        elif force and result and result.get('desc', None):
            response = result['desc']
        else:
            response = None

        if VERBOSE_LOG:
            logger.info("{m} format4rsp2wx_user: {r}".format(m=self, r=response))
        return response

class WXUserEventBase(WXUserMsgBaseModel):
    """
    事件基础类
    """
    event_type    = models.CharField(max_length=64, verbose_name='事件',help_text='事件消息的子类型')
    class Meta:
        abstract = True

    def __str__(self):
        return "[dbid:{i}][{t}][{e}][{m}][{u}]Event, ntimes:{ts}, bk done:{b}, rsp done:{r}."\
            .format(i=self.id, t=self.msg_type, e=self.event_type, m=self.msg_id, u=self.wx_user, ts=self.wx_notify_times, b=self.bk_done, r=self.rsp_done)

    def get_event_type(self):
        return self.event_type.strip().upper()

class WXUserMsgBase(WXUserMsgBaseModel):
    """
    普通消息的基础类
    """
    class Meta:
        abstract = True


    def __str__(self):
        return "[dbid:{i}][{t}][{m}][{u}]Msg, ntimes:{ts}, bk done:{b}, rsp done:{r}."\
            .format(i=self.id, t=self.msg_type, m=self.msg_id, u=self.wx_user, ts=self.wx_notify_times, b=self.bk_done, r=self.rsp_done)

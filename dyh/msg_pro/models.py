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
from dyh.settings import WX_MAX_BYTES

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
from dyh.settings import EVENT_TYPE_TAG_MENU

from dyh.settings import EVENT_TYPE_TAG_SCAN
from dyh.settings import EVENT_TYPE_TAG_LOCATION
from dyh.settings import EVENT_TYPE_TAG_CLICK
from dyh.settings import DEFAULT_ENABLE_ALL_VOICE_ANSWER_VOICDE

from dyh.ai.models import AIModel
from dyh.dyh_mgr.models import WXUser

from dyh.msg_pro import BaseModel

RSP_TXT_NO_ERROR = 0
RSP_TXT_EMPTY = 1
RSP_TXT_OVER = 2
RSP_TXT_NONE = 3

class WXUserEventSubscribe(BaseModel.WXUserEventBase):
    """
    关注事件
    """
    class Meta:
        db_table = 't_wx_event_subscribe'
        verbose_name='微信关注事件'
        verbose_name_plural = verbose_name
        ordering = ['id', ]

class WXUserMsgText(BaseModel.WXUserMsgBase):
    """
    文本信息
    """
    class Meta:
        db_table = 't_wx_msg_text'
        verbose_name='微信文本消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]
    def __str__(self):
        return "[dbid:{i}][{t}-{rt}][{m}][{u}] bk done:{b}, rsp done:{r}, times:{ts}, len:{ln}, offset:{of}."\
            .format(i=self.id, t=self.get_msg_type(), rt=self.rsp_fmt, m=self.msg_id, u=self.wx_user, b=self.bk_done, r=self.rsp_done, ts=self.wx_notify_times, ln=self.rsp_len, of=self.rsp_offset)

class WXUserMsgVoice(BaseModel.WXUserMsgBase):
    """
    语音信息
    """
    media_id = models.CharField(max_length=128, default="", verbose_name='媒体ID', help_text='用户发送请求内容上传到微信服务器获得的媒体ID')
    format = models.CharField(max_length=32, default="", verbose_name='语音格式', help_text='语音格式，如amr，speex等')
    msg_dataid = models.CharField(max_length=64, default="", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="", verbose_name='第几篇', help_text='多文时第几篇文章，从1开始（消息如果来自文章时才有）')
    url      = models.CharField(max_length=1024, default="", verbose_name='语音网址', help_text='语音的网址')
    save_path = models.CharField(max_length=2048, default="", verbose_name='文件保存路径', help_text='TODO: 语音文件在本地的保存路径')
    class Meta:
        db_table = 't_wx_msg_voice'
        verbose_name='微信语音消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]

class WXUserMsgImage(BaseModel.WXUserMsgBase):
    """
    图片信息
    """
    media_id = models.CharField(max_length=128, default="", verbose_name='媒体ID', help_text='用户发送请求内容上传到微信服务器获得的媒体ID')
    msg_dataid = models.CharField(max_length=64, default="-", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="0", verbose_name='第几篇', help_text='多图文时第几篇文章，从1开始（消息如果来自文章时才有）')
    pic_url      = models.TextField(max_length=1024, default="", verbose_name='图片的网址', help_text='图片的网址')
    save_path = models.TextField(max_length=4096, default="", verbose_name='图片保存路径', help_text='TODO: 图片在本地的保存路径')
    class Meta:
        db_table = 't_wx_msg_image'
        verbose_name='微信图片消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]

class WXUserEventMenu(BaseModel.WXUserEventBase):
    """
    菜单事件
    """
    event_key  = models.CharField(max_length=1024, verbose_name='事件',help_text='事件KEY值，与自定义菜单接口中KEY值对应')
    class Meta:
        db_table = 't_wx_event_menu'
        verbose_name='微信菜单操作'
        verbose_name_plural = verbose_name
        ordering = ['id', ]

class WXUserEventScan(BaseModel.WXUserEventBase):
    """
    扫码事件
    """
    event_key = models.CharField(max_length=256, verbose_name='事件KEY值',help_text='事件KEY值，qrscene_为前缀，后面为二维码的参数值')
    ticket    = models.CharField(max_length=256, verbose_name='二维码ticket',help_text='二维码的ticket，可用来换取二维码图片')
    class Meta:
        db_table = 't_wx_event_scan'
        verbose_name='微信扫码事件'
        verbose_name_plural = verbose_name
        ordering = ['id', ]

class WXUserEventLocation(BaseModel.WXUserEventBase):
    """
    位置事件
    """
    latitude  = models.CharField(max_length=32, verbose_name='地理位置纬度',help_text='地理位置纬度')
    longitude = models.CharField(max_length=32, verbose_name='地理位置经度',help_text='地理位置经度')
    precision = models.CharField(max_length=32, verbose_name='地理位置精度',help_text='地理位置精度')
    class Meta:
        db_table = 't_wx_event_location'
        verbose_name='微信位置事件'
        verbose_name_plural = verbose_name
        ordering = ['id', ]

class WXUserEventClick(BaseModel.WXUserEventBase):
    """
    点击事件
    """
    event_key  = models.CharField(max_length=64, verbose_name='事件',help_text='事件KEY值，与自定义菜单接口中KEY值对应')
    class Meta:
        db_table = 't_wx_event_click'
        verbose_name='微信点击事件'
        verbose_name_plural = verbose_name
        ordering = ['id', ]

class WXUserMsgVideo(BaseModel.WXUserMsgBase):
    """
    语音信息
    """
    media_id = models.CharField(max_length=128, default="", verbose_name='媒体ID', help_text='用户发送请求内容上传到微信服务器获得的媒体ID')
    thumb_media_id      = models.CharField(max_length=64, default="", verbose_name='缩略图的媒体id', help_text='视频消息缩略图的媒体id，可以调用多媒体文件下载接口拉取数据')
    msg_dataid = models.CharField(max_length=64, default="", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="", verbose_name='多图文时第几篇文章', help_text='多图文时第几篇文章，从1开始（消息如果来自文章时才有）')
    class Meta:
        db_table = 't_wx_msg_video'
        verbose_name='微信视频消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]

class WXUserMsgShortVideo(BaseModel.WXUserMsgBase):
    """
    短视频信息
    """
    media_id = models.CharField(max_length=128, default="", verbose_name='媒体ID', help_text='用户发送请求内容上传到微信服务器获得的媒体ID')
    thumb_media_id      = models.CharField(max_length=64, default="", verbose_name='缩略图的媒体id', help_text='视频消息缩略图的媒体id，可以调用多媒体文件下载接口拉取数据')
    msg_dataid = models.CharField(max_length=64, default="", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="", verbose_name='多图文时第几篇文章', help_text='多图文时第几篇文章，从1开始（消息如果来自文章时才有）')
    class Meta:
        db_table = 't_wx_msg_short_video'
        verbose_name='微信短视频消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]


class WXUserMsgLocation(BaseModel.WXUserMsgBase):
    """
    微信地理位置消息
    """
    location_x = models.CharField(max_length=32, default="", verbose_name='地理位置纬度', help_text=' 地理位置纬度')
    location_y = models.CharField(max_length=32, default="", verbose_name='地理位置经度', help_text=' 地理位置经度')
    scale = models.CharField(max_length=32, default="", verbose_name='地图缩放大小', help_text=' 地图缩放大小')
    label = models.CharField(max_length=128, default="", verbose_name='地理位置信息', help_text=' 地理位置信息')
    msg_dataid  = models.CharField(max_length=32, default="", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="", verbose_name='多图文时第几篇文章', help_text='多图文时第几篇文章，从1开始（消息如果来自文章时才有）')
    class Meta:
        db_table = 't_wx_msg_location'
        verbose_name='微信位置消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]


class WXUserMsgLink(BaseModel.WXUserMsgBase):
    """
    链接消息
    """
    title = models.CharField(max_length=256, default="", verbose_name='消息标题', help_text='消息标题')
    description = models.CharField(max_length=4096, default="", verbose_name='消息描述', help_text='消息描述')
    url = models.CharField(max_length=1024, default="", verbose_name='消息链接', help_text='消息链接')
    msg_dataid  = models.CharField(max_length=32, default="", verbose_name='消息的数据ID', help_text='消息的数据ID（消息如果来自文章时才有）')
    idx = models.CharField(max_length=32, default="", verbose_name='多图文时第几篇文章', help_text='多图文时第几篇文章，从1开始（消息如果来自文章时才有）')
    class Meta:
        db_table = 't_wx_msg_link'
        verbose_name='微信链接消息'
        verbose_name_plural = verbose_name
        ordering = ['-id', ]


# 注意：次处顺序决定 help cmd中处理的顺序
MSG_TYPE_MAP_MSG_CLASS = {
    MSG_TYPE_TAG_TEXT: WXUserMsgText,
    MSG_TYPE_TAG_IMAGE: WXUserMsgImage,
    MSG_TYPE_TAG_VOICE: WXUserMsgVoice,

    MSG_TYPE_TAG_VIDEO: WXUserMsgVideo,
    MSG_TYPE_TAG_SHORTVIDEO : WXUserMsgShortVideo,
    MSG_TYPE_TAG_LOCATION: WXUserMsgLocation,
    MSG_TYPE_TAG_LINK: WXUserMsgLink,
}
EVENT_TYPE_MAP_EVENT_CLASS = {
    EVENT_TYPE_TAG_SUBSCRIBE: WXUserEventSubscribe,
    EVENT_TYPE_TAG_UNSUBSCRIBE: WXUserEventSubscribe,
    EVENT_TYPE_TAG_MENU: WXUserEventMenu,
    EVENT_TYPE_TAG_SCAN: WXUserEventScan,
    EVENT_TYPE_TAG_LOCATION: WXUserEventLocation,
    EVENT_TYPE_TAG_CLICK: WXUserEventClick,
}

def _try_fill_dbobj_with_dictobj(theclass, dbobj, dictobj):
    dcKeys = dictobj.keys()
    map_key = {}
    for k in dcKeys:
        map_key[k.replace("_", "").lower()] = k

    attrs = vars(theclass)
    for dbattr in attrs:
        try:
            dbkey = dbattr.replace("_", "").lower()
            if dbkey in map_key:
                k = map_key[dbkey]
                setattr(dbobj, dbattr, dictobj[k])
        except Exception as e:
            logger.warn("Set class {c} obj {o} with value of {d} assoc key {k} failed {e}"\
                .format(c=theclass, o=dbobj, d=dictobj, k=dbattr, e=e))

def _get_msg_type_class(msg_type, event_type):
    if event_type:
        return EVENT_TYPE_MAP_EVENT_CLASS.get(event_type, None)
    else:
        return MSG_TYPE_MAP_MSG_CLASS.get(msg_type, None)

def get_text_msg_by_msg_id(msg_id):
    msg = WXUserMsgText.objects.filter(msg_id = msg_id).order_by("-id")[:1]
    if msg.count() > 0:
        return msg[0]
    else:
        None

def get_msg_from_db(user_id, with_ai, msg_id, msg_type, event_type, msg_md5):
    msgClass = MSG_TYPE_MAP_MSG_CLASS.get(msg_type, EVENT_TYPE_MAP_EVENT_CLASS.get(event_type, None))
    if msgClass and issubclass(msgClass, BaseModel.WXUserMsgBaseModel):
        pass
    else:
        logger.error('get_msg_from_db failed: the common_info not support, msg type: [{t}] event type: [{e}], class: [{c}].'\
            .format(t=msg_type, e=event_type, c=msgClass))
        return None

    wxMsg = msgClass.objects.filter(msg_id=msg_id).order_by("-id")[:1]
    if wxMsg.count() > 0:
        wxMsg = wxMsg[0]
        return wxMsg

    wx_user = None
    try:
        wx_user = WXUser.objects.get(id=user_id)
    except WXUser.DoesNotExist:
        return None

    wxMsg = msgClass.objects.filter(wx_user=wx_user, with_ai=with_ai, msg_md5=msg_md5).order_by("-id")[:1]
    if wxMsg.count() > 0:
        wxMsg = wxMsg[0]
        return wxMsg

def confirm_msg_in_db(common_info):
    wx_user = common_info['UserObj']
    msg_type = common_info['MsgType']
    timestamp = int(common_info['CreateTime'])
    msg_time = timezone.make_aware(datetime.fromtimestamp(timestamp))
    nonce = common_info.get('nonce', '{t} no nonce'.format(t=msg_type))

    with_ai = wx_user.always_ai or wx_user.enable_ai
    vav = False
    if msg_type == MSG_TYPE_TAG_VOICE and (DEFAULT_ENABLE_ALL_VOICE_ANSWER_VOICDE or wx_user.vav):
        vav = True

    msg_id = common_info.get("MsgId", None)
    event_type = common_info.get("Event", "NotEvent")
    content = common_info.get("Content", "").strip()
    msg_md5 = common_info.get("MsgMd5", "")
    if msg_id is None:
        msg_id = "{m}-{e}-{i}".format(m=msg_type, e=event_type, i=timestamp)

    while True:
        wxMsg = get_msg_from_db(wx_user.id, with_ai, msg_id, msg_type, event_type, msg_md5)
        if isinstance(wxMsg, BaseModel.WXUserMsgBaseModel):
            break

        msgClass = MSG_TYPE_MAP_MSG_CLASS.get(msg_type, EVENT_TYPE_MAP_EVENT_CLASS.get(event_type, None))
        if msgClass and issubclass(msgClass, BaseModel.WXUserMsgBaseModel):
            pass
        else:
            logger.error('get_msg_from_db failed: the common_info not support, msg type: [{t}] event type: [{e}], class: [{c}] of info:{i}.'\
                .format(t=msg_type, e=event_type, c=msgClass, i=common_info))
            break

        wxMsg = msgClass(wx_user=wx_user, nonce=nonce, msg_id=msg_id, msg_type=msg_type,\
                       msg_time=msg_time, notify_time=timezone.now(),\
                       content=content, msg_md5=msg_md5, with_ai = with_ai)
        try:
            if hasattr(wxMsg, 'event_type'): wxMsg.event_type = event_type
            if vav and msg_type == MSG_TYPE_TAG_VOICE:
                wxMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
            else:
                wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT

            _try_fill_dbobj_with_dictobj(msgClass, wxMsg, common_info)
            wxMsg.save()
        except IntegrityError as e:
            error = '{e}'.format(e=e)
            if "Duplicate" in error and "entry" in error:
                wxMsg = msgClass.objects.filter(msg_id=msg_id).order_by("-id")[:1]
                if wxMsg.count() > 0:
                    wxMsg = wxMsg[0]
                else:
                    wxMsg = msgClass.objects.filter(wx_user=wx_user, with_ai=with_ai, msg_md5=msg_md5).order_by("-id")[:1]
                    if wxMsg.count() > 0:
                        wxMsg = wxMsg[0]
                    else:
                        tip = "Confirm msg in db error with create new msg: {i}, the msg: {m}, {e}!".format(i=common_info, m=wxMsg, e=e)
                        logger.error(tip)
                        raise ValueError(tip)
            else:
                logger.error("Confirm msg in db except: {e}".format(e=e))
                raise e

    if isinstance(wxMsg, BaseModel.WXUserMsgBaseModel):
        if VERBOSE_LOG:
            logger.info("Confirm msg in db msg OK:{m}.".format(m=wxMsg))
        return wxMsg
    else:
        logger.error("Confirm msg in db failed with info: {i}.".format(i=common_info))
        return None

def copy_msg2txt_msg(wxMsg):
    if isinstance(wxMsg, WXUserMsgText):
        return wxMsg

    wx_user = wxMsg.wx_user
    msg_type = wxMsg.get_msg_type()
    event_type = wxMsg.get_event_type()

    msg_time = wxMsg.msg_time
    nonce = wxMsg.nonce
    msg_id = wxMsg.msg_id
    content = wxMsg.content
    msg_md5 = wxMsg.msg_md5
    with_ai = wx_user.always_ai or wx_user.enable_ai
    rsp_fmt = wxMsg.rsp_fmt

    if not msg_id:
        msg_id = "{m}-{e}-{i}".format(m=msg_type, e=event_type, i=msg_time.timestamp())

    txtMsg = WXUserMsgText.objects.filter(msg_id=msg_id).order_by("-id")[:1]
    if txtMsg.count() > 0:
        txtMsg = txtMsg[0]
        if VERBOSE_LOG:
            logger.info("Copy msg to text msg OK, fetch text msg directly:{m}.".format(m=txtMsg))
        return txtMsg

    txtMsg = WXUserMsgText.objects.filter(wx_user=wx_user, with_ai=with_ai, msg_md5=msg_md5).order_by("-id")[:1]
    if txtMsg.count() > 0:
        txtMsg = txtMsg[0]
        if VERBOSE_LOG:
            logger.info("Confirm msg to text msg OK, fetch text msg with same content:{m}.".format(m=txtMsg))
        return txtMsg

    txtMsg = WXUserMsgText(wx_user=wx_user, nonce=nonce, msg_id=msg_id, msg_type=msg_type,\
                            msg_time=msg_time, notify_time=timezone.now(),\
                            content=content, msg_md5=msg_md5, with_ai = with_ai)
    try:
        txtMsg.rsp_fmt = rsp_fmt
        txtMsg.save()
    except IntegrityError as e:
        error = '{e}'.format(e=e)
        if "Duplicate" in error and "entry" in error:
            another_msg = WXUserMsgText.objects.filter(msg_id=msg_id).order_by("-id")[:1]
            if another_msg.count() > 0:
                txtMsg = another_msg[0]
            else:
                another_msg = WXUserMsgText.objects.filter(wx_user=wx_user, with_ai=with_ai, msg_md5=msg_md5).order_by("-id")[:1]
                if another_msg.count() > 0:
                    txtMsg = another_msg[0]
                else:
                    tip = "Copy msg to text msg except, origin msg: {m}, error: {e}!".format(m=wxMsg, e=e)
                    logger.error(tip)
                    raise ValueError(tip)
        else:
            tip = "Copy msg to text msg except, origin msg: {m}, error: {e}!".format(m=wxMsg, e=e)
            logger.error(tip)
            raise e


    if txtMsg and isinstance(txtMsg, BaseModel.WXUserMsgBaseModel):
        if VERBOSE_LOG:
            tip = "Copy msg to text msg OK: {m}!".format(m=txtMsg)
            logger.info(tip)
        return txtMsg
    else:
        tip = "Copy msg to text msg failed, origin msg: {m}!".format(m=wxMsg, e=e)
        logger.error(tip)
        return None

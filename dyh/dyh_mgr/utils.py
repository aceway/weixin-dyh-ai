#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: utils.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: Sat 22 Nov 2014 09:07:09 PM CST
#  Description: ...
# 
########################################################################
import json
import time
#import hashlib
import logging
logger = logging.getLogger('django')

import requests
import datetime
import threading
from datetime import timedelta
from dyh.settings import SAVE_MAX_LEN
from django.utils import timezone

from dyh.utils import download_media_file
from dyh.utils import extract_img_link_from

from dyh.dyh_mgr.models import WXUser
from dyh.dyh_mgr.models import WXDyhMgr
from dyh.dyh_mgr.models import WXDingYueHao

from dyh.msg_pro.models import WXUserMsgText
from dyh.msg_pro.models import WXUserEventSubscribe

from dyh.weixin_api_mgr.WeixinApiMgr import WeixinApiMgr

from dyh.settings import EVENT_TYPE_TAG_SUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_UNSUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_SCAN
from dyh.settings import EVENT_TYPE_TAG_LOCATION
from dyh.settings import EVENT_TYPE_TAG_CLICK
from dyh.settings import DEFAULT_ENABLE_AI
from dyh.settings import DEFAULT_ALWAYS_AI
from dyh.settings import WX_API_DOMAIN

dyh_mgr_proccessor = {} # holder
def process_dyh_mgr_msg(wxMsg, cmd):
    func_desc = dyh_mgr_proccessor.get(cmd, None)
    if isinstance(func_desc, tuple) and len(func_desc) >= 2:
        proccessor = func_desc[IDEX_DESC['fun']]
        return proccessor(wxMsg)
    else:
        return "Not found the cmd: [{c}] for manager!".format(c=cmd)

def mgr_query_today_total_msg_count(wxMsg):
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    # wx_user_openid = wx_user.wx_openid
    # wx_dyh_rawid = wx_dyh.rawid
    # msg_content = wxMsg.content
    content = """今日用户给订阅号发送信息总数"""
    msg = WXUserMsgText.objects.filter(wx_user__wx_dyh=wx_dyh, msg_time__gte=datetime.date.today())
    if msg is not None and msg.count() > 0:
        content += ": {c} 条.".format(c=msg.count())
    else:
        content += ": 0 条."
    return content

def _mgr_query_today_new_user_count(wxMsg):
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    content = """今日发生订阅次数: {sub}, 退订次数: {un}"""
    rec = WXUserEventSubscribe.objects.filter(wx_user=wx_user, event_type=EVENT_TYPE_TAG_SUBSCRIBE, msg_time__gte=datetime.date.today())
    sub = 0
    if rec is not None and rec.count() > 0:
        sub = rec.count()

    rec = WXUserEventSubscribe.objects.filter(wx_user__wx_dyh=wx_dyh, event_type=EVENT_TYPE_TAG_UNSUBSCRIBE, msg_time__gte=datetime.date.today())
    unsun = 0
    if rec is not None and rec.count() > 0:
        unsun = rec.count()

    return content.format(sub=sub, un=unsun)

def mgr_query_today_new_msg_list(wxMsg):
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    wx_user_openid = wx_user.wx_openid

    td = datetime.date.today()
    content = "[{t}]用户消息:\n".format(t= str(td)[:10])
    all_msg = WXUserMsgText.objects.filter(wx_user__wx_dyh=wx_dyh, msg_time__gte=td).order_by('-msg_time',)
    if all_msg is not None and all_msg.count() > 0:
        msg = all_msg[:9]
        user_map_name = {}
        for m in msg:
            cur_tz = timezone.get_current_timezone()
            t = cur_tz.normalize(m.msg_time).strftime("%Y-%m-%d %H:%M:%S")
            if m.wx_openid not in user_map_name:
                user_info = get_wx_user_info(wx_dyh, m.wx_openid)
                if user_info is not None and isinstance(user_info.wx_nicname, str) and len(user_info.wx_nicname.strip()) > 0:
                    user_map_name[m.wx_openid] = user_info.wx_nicname
                else:
                    user_map_name[m.wx_openid] = ""
            if  len(user_map_name[m.wx_openid].strip()) > 0:
                content += "[{t}] {u}: {m}\n".format(t=t[-8:], u=user_map_name[m.wx_openid], m = m.content)
            else:
                content += "[{t}] {u}: {m}\n".format(t=t[-8:], u=wx_user_openid, m = m.content)
        if all_msg.count() > 9:
            content += "更多消息请登录微信公众平台查看..."
    else:
        content += "今日仍无用户消息."
    return content

def _mgr_query_today_new_user_list(wxMsg):
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    td = datetime.date.today()
    content = "[{t}]新增订阅用户\n".format(t= str(td)[:10])
    rec = WXUserEventSubscribe.objects.filter(wx_user__wx_dyh=wx_dyh, event_type=EVENT_TYPE_TAG_SUBSCRIBE, msg_time__gte=datetime.date.today())
    if rec is not None and rec.count() > 0:
        rec = rec[:9]
        user_map_name = {}
        for r in rec:
            cur_tz = timezone.get_current_timezone()
            t = cur_tz.normalize(r.msg_time).strftime("%Y-%m-%d %H:%M:%S")
            name = '{n}'.format(n=r.wx_user)
            if name not in user_map_name:
                user_map_name[name] = name

            if  len(user_map_name[name].strip()) > 0:
                content += "[{t}] {u}.\n".format(t=t[-8:], u = user_map_name[name])
            else:
                content += "[{t}] {u}.\n".format(t=t[-8:], u = name)
    else:
        content += "今日仍无新订阅用户."
    return content

def mgr_query_today_the_user_msg(wxMsg):
    """
        ('#@',   mgr_query_today_the_user_msg, u"查询今日某用户发给订阅号的信息, #@后需空一格再写UserID"),
    """
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    wx_dyh_rawid = wx_dyh.rawid

    msg_content = wxMsg.content

    if len(msg_content.strip().split(' ')) < 2:
        content ="请指明查询谁发送的信息: #@ UserID"
        return content

    td = datetime.date.today()
    who = msg_content.strip().split(' ')[1].strip()
    nickname = ""
    if who.isdigit():
        user = WXUser.objects.filter(pk=who)
        if user is not None and len(user) > 0:
            user = user[0]
            nickname = user.wx_nicname.strip()
            who_msg = WXUserMsgText.objects.filter(wx_openid=user.wx_openid, dyh_openid=wx_dyh_rawid, msg_time__gte=td).order_by('-msg_time',)
        else:
            who_msg = WXUserMsgText.objects.filter(wx_openid=who, dyh_openid=wx_dyh_rawid, msg_time__gte=td).order_by('-msg_time',)
    else:
        who_msg = WXUserMsgText.objects.filter(wx_openid=who, dyh_openid=wx_dyh_rawid, msg_time__gte=td).order_by('-msg_time',)

    if isinstance(nickname, str) and len(nickname) > 0:
        content = "今日[{w}]发的信息:\n".format(w=nickname)
    else:
        content = "今日[{w}]发的信息:\n".format(w=who)
    if who_msg is not None and who_msg.count() > 0:
        msg = who_msg[:9]
        for m in msg:
            cur_tz = timezone.get_current_timezone()
            t = cur_tz.normalize(m.msg_time).strftime("%Y-%m-%d %H:%M:%S")
            content += "[{t}]: {m}\n".format(t=t[:18][-7:], m = m.content)
        if who_msg.count() > 9:
            content += "更多消息请登录微信公众平台查看..."
    else:
        content += "\n仍无消息."
    return content

def _mgr_query_today_activie_user_openid(wxMsg):
    """
        ('#@@',  _mgr_query_today_activie_user_openid, u"查询今日活跃用户OpenID列表."),
    """
    wx_user = wxMsg.wx_user
    td = datetime.date.today()
    content = "[{t}]活跃用户\n".format(t= str(td)[:10])
    msg = WXUserMsgText.objects.filter(wx_user=wx_user, msg_time__gte=td).order_by('-msg_time',)
    if msg is not None and msg.count() > 0:
        msg = msg[:100]
        active_user   = {}
        content +="UserID - Nickname\n"
        for m in msg:
            if m.wx_user.wx_openid not in active_user:
                active_user[m.wx_user.wx_openid] = True
                content += "{uid} - {nn}\n".format(uid=m.wx_user.id, nn=m.wx_user.wx_nicname)
    else:
        content += "今日仍无活跃用户."
    return content

def mgr_send_today_broadcast_msg(wxMsg):
    content = "TODO: 发送今日广播信息"
    return content

def mgr_send_msg_to_user_msg(wxMsg):
    wx_user = wxMsg.wx_user
    wx_dyh = wx_user.wx_dyh
    wx_user_openid = wx_user.wx_openid
    wx_dyh_rawid = wx_dyh.rawid

    msg_content = wxMsg.content

    msg_info = msg_content.strip().split(' ') 
    if len(msg_info) < 3:
        content = "请指明给谁发送什么消息: #@u UserID 消息"
        return content

    max_sleep_houre = 48
    who = msg_info[1].strip()
    msg = msg_info[2].strip()
    if who.isdigit():
        user = WXUser.objects.filter(pk=who)
        if user is not None and user.count() > 0:
            user = user[0]
            if user.wx_openid == wx_user_openid.strip():
                content = "请不要用管理员命令给自己发送消息."
                return content
            elif user is not None:
                #who = user.wx_openid
                pass
            else:
                pass
    if user is None:
        tips = "The user [{u}] does not exist.".format(u=who)
        logger.error(tips)
        return tips
    if len(user.wx_nicname.strip()) <=0: user.wx_nicname = who
    his_msg = WXUserMsgText.objects.filter(wx_openid=user.wx_openid, dyh_openid=wx_dyh_rawid).order_by('-msg_time', )[:1]
    if his_msg.count() == 0 :
        content = "由于 [{u}] {mh}小时未与你互动，你不能再主动发消息给他。直到用户下次主动发消息给你才可以对其进行回复。".format(u=user.wx_nicname, mh=max_sleep_houre)
        return content
    his_msg = his_msg[0]
    msg_time = his_msg.msg_time
    if timezone.now() > msg_time + timedelta(hours=8):
        content = "由于 [{u}] {mh}小时未与你互动，你不能再主动发消息给他。直到用户下次主动发消息给你才可以对其进行回复。".format(u=user.wx_nicname, mh=max_sleep_houre)
        return content
    else:
        dyh_info = get_wx_dyh_info(str(wx_dyh_rawid))
        if dyh_info is None:
            tips = "Don't find the dyh [{d}].".format(d=wx_dyh_rawid)
            logger.error(tips)
            return tips
        if len(dyh_info.appsecret.strip()) < 8 :
            tips = "还未在管理后台为你的公众号设置AppSecret:[{a}].".format(dyh_info.appsecret.strip())
            logger.error(tips)
            return tips
        wam = WeixinApiMgr(appid=dyh_info.dyh_appid, appsecret=dyh_info.appsecret)
        ac = wam.get_access_token()
        if isinstance(ac,dict) and len(ac.get('access_token', "")) > 0 and len(dyh_info.access_token.strip()) == 0:
            logger.debug("get access token from weixin server first time:{at}".format(at=ac))
            dyh_info.access_token = ac['access_token']
            dyh_info.at_seconds   = ac['expires_in']
            dyh_info.at_time      = timezone.now()
            dyh_info.save()
        elif isinstance(ac,dict) and len(ac.get('access_token', "")) > 0:
            if timezone.now() > dyh_info.at_time + timedelta(seconds=dyh_info.at_seconds):
                ac = wam.get_access_token()
                logger.debug("Locale db access token is out get new from weixin server: {at}".format(at=dyh_info.access_token))
                dyh_info.access_token = ac['access_token']
                dyh_info.at_seconds   = ac['expires_in']
                dyh_info.at_time      = timezone.now()
                dyh_info.save()
            else:
                logger.debug("Locale db access token still active ,use it: {at}".format(at=dyh_info.access_token))
                wam.set_access_token(dyh_info.access_token)
        else:
            tips = "Get access_token for img failed: {e}".format(e=ac)
            logger.error(tips)
            return tips

        pret = wam.post_user_text_msg(user.wx_openid, msg)
        tips = ""
        if isinstance(pret, dict):
            if 'code' in pret and pret['code'] == 0:
                if isinstance(pret['data'], dict) and 'errcode' in pret['data'] :
                    if int(pret['data']['errcode']) == 0:
                        tips = "消息已经发给用户."
                    else:
                        tips = pret['data']['errmsg'] + "(" + str(pret['data']['errcode']) + ")"
                else:
                    tips = "系统内部错误."
            else:
                tips = pret['desc']
        else:
            tips = "系统内部错误."
        return tips


IDEX_DESC={ "fun":0, "des":1, }

def mgr_query_help_cmd(wxMsg):
    content = "管理员命令:\n"
    for cmd, func_desc in list(dyh_mgr_proccessor.items()):
        content += "{c}: {desc}.\n".format(c=cmd, desc=func_desc[IDEX_DESC['des']])
    return content

dyh_mgr_proccessor = {
    '#':   (mgr_query_help_cmd, "显示管理员命令列表"),
    '#u':  (_mgr_query_today_new_user_count, "今日新增订阅数"),
    '#uu': (_mgr_query_today_new_user_list, "今日新增用户"),
    '#@@': (_mgr_query_today_activie_user_openid, "今日活跃用户"),
}

##############################################################################
def get_wx_user_info(wx_dyh, wx_user_opnid):
    wu = WXUser.objects.filter(wx_dyh=wx_dyh, wx_openid=wx_user_opnid)
    if wu is not None and wu.count() > 0:
        return wu[0]
    else:
        the_user = WXUser(wx_dyh=wx_dyh, wx_openid=wx_user_opnid, enable_ai=DEFAULT_ENABLE_AI, always_ai=DEFAULT_ALWAYS_AI, wx_nicname="{i}".format(i=wx_user_opnid) )
        the_user.save()
        return the_user

def get_wx_dyh_info(wx_rawid):
    dyh = WXDingYueHao.objects.filter(rawid=wx_rawid)
    if dyh.count() == 1:
        return dyh[0]
    elif dyh.count() > 1:
        logger.error("wx_rawid {r} error, count not one:  {c}".format(r=wx_rawid, c=dyh.count()))
        return dyh[0]
    else:
        return None

def try_get_dyh_mgr(wx_user):
    mgr = WXDyhMgr.objects.filter(wx_user=wx_user, is_active=True)
    if mgr is not None and mgr.count() > 0:
        logger.info("Found dyh mgr [{u}]".format(u=wx_user))
        return mgr[0]
    else:
        return None

def get_dyh_by_url_factor(url_factor):
    """
    admin在后台配置url_factor, 控制此查询结果, 给每个订阅号分配不同的路径入口
    """
    if isinstance(url_factor, str) and len(url_factor.strip()) > 0:
        wx_dyh = WXDingYueHao.objects.filter(url_factor=url_factor)
        if wx_dyh and wx_dyh.count() > 0:
            dyh = wx_dyh[0]
            dyh.last_verify_time = timezone.now()
            dyh.verify_times += 1
            dyh.save()
            return dyh
        else:
            logger.error("get_dyh_by_url_factor but paramter url_factor:{p} not config in db.".format(p=url_factor))
    else:
        logger.error("get_dyh_by_url_factor but paramter url_factor:{p} error.".format(p=url_factor))
    return None

def try_upload_img_from_url(wx_user, dyh, from_url):
    media_id = None
    img_url, img_ext = extract_img_link_from(from_url)
    if img_url and img_ext:
        while True:
            media_type = "image"
            local_file = download_media_file(img_url, media_type, img_ext)
            if local_file is None:
                logger.error("download_media_file failed: {m} {i} from {u}".format(m=media_type, i=img_ext, u=img_url))
                break

            wxApiMgr = WeixinApiMgr(dyh.dyh_appid.strip(), dyh.appsecret.strip(), WX_API_DOMAIN)
            result = wxApiMgr.upload_media(local_file, media_type)
            if isinstance(result, dict) and 'media_id' in result and  len(result['media_id'].strip()) == 64:
                media_id =  result['media_id']
            else:
                logger.error("Update image to WX server faild: {r}".format(r=result))
                media_id = None
            break # endo fwhile True:
    return media_id, img_url

def try_upload_img_from_local_file(wx_user, wx_dyh, from_url):
    media_id = None
    return media_id, from_url

# -*- coding:utf-8 -*-
import os
import sys
import json
import time
import requests
import threading
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

from datetime import timedelta
from django.utils import timezone
from django.db.models import F
from django.db.models import Q
from django.db.models.functions import Length

from dyh import settings as st

from dyh.utils import got_str_md5
from dyh.utils import download_media_file
from dyh.utils import extract_img_link_from

from dyh.msg_pro.BaseModel import WXUserMsgBaseModel
from dyh.msg_pro.models import WXUserMsgImage
from dyh.msg_pro.models import WXUserMsgVoice
from dyh.msg_pro.models import MSG_TYPE_MAP_MSG_CLASS
from dyh.msg_pro.models import EVENT_TYPE_MAP_EVENT_CLASS
from dyh.msg_pro.models import confirm_msg_in_db

from dyh.dyh_mgr.models import WXUser
from dyh.dyh_mgr.models import WXDingYueHao
from dyh.dyh_mgr.utils import dyh_mgr_proccessor as SYS_CMD_MAP_PROCESS
from dyh.dyh_mgr.utils import try_upload_img_from_url
from dyh.dyh_mgr.utils import mgr_query_help_cmd

from dyh.ai.models import AIModel
from dyh.ai.models import WXAIConfig
from dyh.ai.models import get_all_available_models

from dyh.weixin_api_mgr.WeixinApiMgr import WeixinApiMgr
from dyh.weixin_sdk.WXBizMsgCrypt import WXBizMsgCrypt

def parse_user_question_by_AI(wxMsg):
    """
    TODO: 用json格式回答
        你是否知道答案用单独一个字段以0或1标识；
        从用户的发送的内容中分析用户是否有以下意图:
        是否要画画，1标识是，0标示否;
        是否要写代码，1标识是，0标示否;
        是否要语音回答，1标识是，0标示否;
        期望语音选择男还是女，1标志着男，0标识女;
        是否要将语音换另外一位，1标识是，0标示否，
        回复内容的文本本身都在单独一个字段，其中不再嵌套子字段，如:
        问：歌德是谁？
        回复：{
            "know": 1,
            "draw": 0,
            "code": 0,
            "voice": 1,
            "gender": 0,
            "answer": "约翰·沃尔夫冈·冯·歌德（Johann Wolfgang von Goethe），是一位德国著名的思想家、
        作家、科学家，被认为是德国文学的最杰出代表之一，他的作品包括《少年维特的烦恼》和《浮士德》等。"
        }
    """

    # TODO: define in config - db item.
    if wxMsg.get_msg_type() == st.EVENT_TYPE_TAG_SUBSCRIBE :
        return "新用户加入，请致欢迎辞."
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_TEXT:
        msg_type_prompt = "请回答用户问题, 以json格式返回数据，所有内容均在json对象内: " + \
            "其中known字段表示你是否知道答案，1表示是, 0表示否；tone字段标识用户是否希望得到语音回答，" + \
            "gender字段标识用户是否选择希望女音回答；问题的答复内容都在answer字段里，不再嵌套子json字段，" + \
            "如: {know:0，tone:0,gender:1,answer:'没明白你的问题，请说详细点。'}"
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_CODE:
        return "这是用户期望写段代码"
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_VOICE:
        return "这是用户用语音发起的问题"
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_IMAGE:
        return "这是用户用发的一张图片"
    elif wxMsg.get_msg_type() == st.EVENT_TYPE_TAG_LOCATION:
        return "这是位置信息"
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_VIDEO:
        return "这是用户用发的一段视频"
    elif wxMsg.get_msg_type() == st.MSG_TYPE_TAG_LINK:
        return "这是一个网络链接"
    else:
        return "parase user question 代支持消息"

def make_encryp_rsp_with_msg_obj(wxMsg, common_info, cur_rsp, rsp_fmt=None):
    encryp_msg = None
    while True:
        if wxMsg is None or common_info is None:
            logger.error("内部错误!!!!")
            break

        wx_user = None
        dyh = None
        msg_type = None
        if isinstance(wxMsg, WXUserMsgBaseModel):
            msg_type = wxMsg.get_msg_type()
            nonce = wxMsg.nonce
            wx_user = wxMsg.wx_user
            dyh = wx_user.wx_dyh
        else:
            msg_type = common_info.get("MsgType", None)
            nonce = common_info.get("nonce", None)
            wx_user = common_info.get("UserObj", None)
            dyh = common_info.get("DyhObj", None)

        tuser = wx_user.wx_openid
        fuser = dyh.rawid

        token = dyh.token.strip()
        aeskey = dyh.aeskey.strip()
        dyh_appid = dyh.dyh_appid.strip()
        wxcpt=WXBizMsgCrypt(token, aeskey, dyh_appid)

        if VERBOSE_LOG :
            logger.info("Pack response message [{tp}] rsp_fmt [{fmt}] from {f} to {t} cur_rsp:{c}"\
                .format(tp=msg_type, fmt=rsp_fmt, f=fuser, t=tuser, c=cur_rsp))

        if cur_rsp is None:
            # no rsp to ...
            break

        if isinstance(cur_rsp, dict):
            cur_rsp = cur_rsp.get('text', None) or cur_rsp.get('desc', None) or '{c}'.format(c=cur_rsp)
        elif not isinstance(cur_rsp, str):
            logger.error("内部错误!!!!")
            break

        cnt = cur_rsp.strip().lower()
        sz = sys.getsizeof(cnt)
        ln = len(cnt)
        if VERBOSE_LOG:
            logger.info("make_encryp_rsp_with_msg_obj cur_rsp len: {l}, size:{s}, rsp_fmt:{f}".format(l=ln, s=sz, f=rsp_fmt))

        if rsp_fmt == st.MSG_TYPE_TAG_TEXT and ln == 64 and wxMsg.wx_user.always_voice:
            ret_text = st.WX_RETURN_VOICE.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=cur_rsp)
        elif rsp_fmt in (st.MSG_TYPE_TAG_VOICE, ) and ln == 64:
            ret_text = st.WX_RETURN_VOICE.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=cur_rsp)
        elif rsp_fmt in (st.MSG_TYPE_TAG_IMAGE, ) and ln == 64:
            ret_text = st.WX_RETURN_IMG.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=cur_rsp)
        elif rsp_fmt in (st.MSG_TYPE_TAG_CODE, ):
            ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)
        elif rsp_fmt == st.MSG_TYPE_TAG_TEXT and wx_user.always_voice:
            mock_info = {"UserObj": wx_user, "DyhObj": dyh}
            mock_info['MsgId'] = common_info['MsgId']
            mock_info['nonce'] =  common_info.get("nonce", "")
            mock_info['CreateTime'] = int(time.time())
            mock_info['MsgType'] = st.MSG_TYPE_TAG_VOICE
            mock_info['Content'] = cur_rsp
            mock_info['MsgMd5'] =  got_str_md5(mock_info['Content'])
            mockVoiceMsg = confirm_msg_in_db(mock_info)
            if not isinstance(mockVoiceMsg, WXUserMsgVoice):
                ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)
                return ret_text

            from dyh.weixin_msg import wx_voice
            pre_result = {'ok': True, 'answer': cur_rsp, 'desc': "text to voice"}
            result = wx_voice.try_trans_answer2voice(mockVoiceMsg, pre_result)
            if isinstance(result, dict) and result.get('ok', False) and len(result['answer']) == 64:
                ret_text = st.WX_RETURN_VOICE.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=result['answer'])
            else:
                ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)
        else:
            media_id, img_url = _try_rsp_as_image(wxMsg.response, common_info)
            if media_id:
                wxMsg.response = media_id
                wxMsg.rsp_fmt = st.MSG_TYPE_TAG_IMAGE
                ret_text = st.WX_RETURN_IMG.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=media_id)
            elif img_url :
                wxMsg.response = img_url
                wxMsg.rsp_fmt = st.MSG_TYPE_TAG_IMAGE
                tip = "服务器上图片为临时文件，需要的请尽快下载保存到本地.\n"
                ret_text = st.WX_RETURN_IMG_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), t="AI-图片", d=tip, p=img_url, u=img_url)
            elif sz > st.WX_MAX_BYTES:
                logger.error('Pack ret cur_rsp too long {s} > {m} will be cutted: {c}:'\
                    .format(s=sys.getsizeof(cur_rsp), m=st.WX_MAX_BYTES, c=cur_rsp[:10] + "..." + cur_rsp[-10:]))
                ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp[:st.RSP_MAX_LEN])
            else:
                ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)

        ret, encryp_msg = wxcpt.EncryptMsg(ret_text, nonce)
        if ret != 0 :
            logger.error("Pack encrypt data failed:{r}, response format {fmt}, msg [{f}] --> [{t}]: {c}"\
                .format(r=ret, fmt=rsp_fmt, f=fuser, t=tuser, c=cur_rsp))
            break
        else:
            tips = cur_rsp if len(cur_rsp) <= 64 else (cur_rsp[:64] + " ....")
            logger.info("Pack encrypt data ok, response format {fmt}, msg [{f}] --> [{t}], size:{s},len:{l}, {c}"\
                .format(fmt=rsp_fmt, f=fuser, t=tuser, s=sz, l=ln, c=tips))
        break

    if encryp_msg and cur_rsp and len(cur_rsp) >= wxMsg.rsp_len and wxMsg.rsp_len > 0:
        wxMsg.finish_response_process()
    elif encryp_msg and wxMsg.rsp_offset >= wxMsg.rsp_len and wxMsg.rsp_len > 0:
        wxMsg.finish_response_process()
    return encryp_msg

def make_encryp_rsp_for_cmd_rsp(common_info, cur_rsp, rsp_fmt):
    """
    给命令定制的返回，不支持探测消息格式，根据参数直接加密返回
    """
    encryp_msg = None
    while True:
        if not isinstance(common_info, dict):
            logger.error("内部错误!!!! common info: {i}".format(i=common_info))
            break

        if not cur_rsp or not rsp_fmt:
            logger.error("内部错误!!!! cur_rsp:{r}, rsp_fmt:{f}".format(r=cur_rsp, f=rsp_fmt))
            break

        msg_type = common_info.get("MsgType", st.MSG_TYPE_TAG_TEXT)

        wx_user = common_info.get("UserObj", None)
        if not isinstance(wx_user, WXUser):
            logger.error("内部错误!!!! UserObj:{u}".format(u=wx_user))
            break
        tuser = wx_user.wx_openid

        dyh = common_info.get("DyhObj", None)
        if not isinstance(dyh, WXDingYueHao):
            logger.error("内部错误!!!! DyhObj:{d}".format(d=dyh))
            break
        fuser = dyh.rawid
        token = dyh.token.strip()
        aeskey = dyh.aeskey.strip()
        dyh_appid = dyh.dyh_appid.strip()
        wxcpt=WXBizMsgCrypt(token, aeskey, dyh_appid)

        if VERBOSE_LOG :
            logger.info("Pack cmd response message rsp_fmt [{fmt}] from [{f}] to [{t}] cur_rsp: [{c}]."\
                .format(fmt=rsp_fmt, f=fuser, t=tuser, c=cur_rsp))

        max_len = st.RSP_MAX_LEN + len("(未完 .. 继续)")
        if len(cur_rsp) > max_len:
            cur_rsp = cur_rsp[: max_len+1]

        cnt = cur_rsp.strip().lower()
        sz = sys.getsizeof(cnt)
        ln = len(cnt)
        if rsp_fmt == st.MSG_TYPE_TAG_VOICE and ln == 64:
            ret_text = st.WX_RETURN_VOICE.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=cur_rsp)
        elif rsp_fmt == st.MSG_TYPE_TAG_IMAGE and ln == 64:
            ret_text = st.WX_RETURN_IMG.format(tuser=tuser, fuser=fuser, tm=int(time.time()), mid=cur_rsp)
        elif rsp_fmt == st.MSG_TYPE_TAG_CODE:
            ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)
        else:
            #media_id, img_url = try_upload_img_from_url(wx_user, dyh, cur_rsp)
            img_url, ext = extract_img_link_from(cur_rsp)
            if img_url and ext:
                tip = "服务器上图片为临时文件，需要的请尽快下载保存到本地.\n"
                ret_text = st.WX_RETURN_IMG_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), t="AI-图片", d=tip, p=img_url, u=img_url)
            else:
                ret_text = st.WX_RETURN_TXT.format(tuser=tuser, fuser=fuser, tm=int(time.time()), cnt=cur_rsp)

        nonce = '{n}'.format(n=int(time.time() * 1000))
        ret, encryp_msg = wxcpt.EncryptMsg(ret_text, nonce)
        if ret != 0 :
            logger.error("Pack encrypt data failed [{r}], response format [{fmt}], msg [{f}] --> [{t}]: [{c}]."\
                .format(r=ret, fmt=rsp_fmt, f=fuser, t=tuser, c=cur_rsp))
            break
        else:
            tips = cur_rsp if len(cur_rsp) <= 64 else (cur_rsp[:64] + " ....")
            logger.info("Pack encrypt data ok, response format [{fmt}], msg [{f}] --> [{t}], size:{s},len:{l}, [{c}]."\
                .format(fmt=rsp_fmt, f=fuser, t=tuser, s=sz, l=ln, c=tips))
            break
        break
    return encryp_msg

def get_help_cmd_text(text):
    if not text: return None
    text = text.split(" ")[0]
    if len(text) > 16: return False

    # TODO: 优化写正则
    text = text.strip().lower()
    for s in st.REMOVE_CHARS4HELP_CMD_DETECT:
        text = text.replace(s, "")

    ln = len(text)
    if ln == 0: return None

    if ln > 16: return None

    ln = ln * 1.0
    for k, v in st.HELP_CMD_MAP_CFG.items():
        lk = len(k)
        rt = lk / ln
        # logger.info("-----: K:[{k}], text:[{t}], lk:[{lk}],ln:[{ln}], rt:[{rt}], in:[{i}]".\
        #     format(k=k, t=text, lk=lk, ln=ln, rt=rt, i= k in text))
        if k in text and rt >= 0.5:
            return v
    return None

def get_sys_cmd_text(text):
    # TODO: 优化写正则
    if not text: return None
    if len(text) > 16: return False

    text = text.strip().lower()
    for s in st.REMOVE_CHARS4SYS_CMD_DETECT:
        text = text.replace(s, "")

    ln = len(text)
    if ln == 0: return None
    if ln > 16: return None

    ln = ln * 1.0

    txt = False
    for k, v in st.SYS_CMD_MAP_CFG.items():
        lk = len(k)
        if k in text and lk / ln >= 0.5:
            return v
    return None

_cfged_help_cmd = []
def get_support_help_cmd_list():
    if len(_cfged_help_cmd) > 0:
        return _cfged_help_cmd

    for _, cmd in st.HELP_CMD_MAP_CFG.items():
        if cmd not in _cfged_help_cmd:
            _cfged_help_cmd.append(cmd)
    return _cfged_help_cmd

_cfged_sys_cmd = []
def get_support_sys_cmd_list():
    if len(_cfged_sys_cmd) > 0:
        return _cfged_sys_cmd

    for _, cmd in st.SYS_CMD_MAP_CFG.items():
        if cmd not in _cfged_sys_cmd:
            _cfged_sys_cmd.append(cmd)
    return _cfged_sys_cmd

def get_support_cmd_list():
    return get_support_help_cmd_list() + get_support_sys_cmd_list()

def _try_rsp_as_image(response, common_info):
    if not response or not common_info:
        return None, None

    img_url, img_ext = extract_img_link_from(response)
    media_id = None
    if img_url and img_ext:
        dyh = common_info["DyhObj"] # wxMsg.wx_user.wx_dyh
        img_info = dict(common_info)
        img_info['MsgType'] = st.MSG_TYPE_TAG_IMAGE
        img_info['Content'] = "{t}toImg".format(t=time.time())
        img_info['MsgMd5'] = got_str_md5(img_info['Content'])
        imgMsg = confirm_msg_in_db(img_info)
        if not isinstance(imgMsg, WXUserMsgImage):
            return None, img_url

        if len(imgMsg.media_id.strip()) < 64 or len(imgMsg.pic_url) == 0:
            if len(imgMsg.pic_url) == 0:
                imgMsg.pic_url = img_url
                imgMsg.save()

            while True:
                media_type = "image"
                if len(imgMsg.media_id) == 0:
                    if len(imgMsg.save_path.strip()) == 0:
                        local_file = download_media_file(img_url, media_type, img_ext)
                        if local_file is None:
                            break
                        imgMsg.save_path = local_file
                        imgMsg.save()

                    wxApiMgr = WeixinApiMgr(dyh.dyh_appid.strip(), dyh.appsecret.strip(), st.WX_API_DOMAIN)
                    result = wxApiMgr.upload_media(local_file, media_type)
                    if isinstance(result, dict) and 'media_id' in result and  len(result['media_id'].strip()) > 0:
                        media_id =  result['media_id']
                        imgMsg.media_id = media_id
                        imgMsg.rsp_fmt = st.MSG_TYPE_TAG_IMAGE
                        imgMsg.save()
                        break
                    else:
                        media_id = None
                        logger.error("Upload image file {f} to weixin server failed: {r}"\
                            .format(f=local_file, r=result))
                        break
                elif len(imgMsg.media_id) == 64 and imgMsg.rsp_fmt == st.MSG_TYPE_TAG_IMAGE:
                    media_id = imgMsg.media_id
                break # endo fwhile True:

            if media_id:
                imgMsg.response = imgMsg.media_id
                imgMsg.rsp_fmt = st.MSG_TYPE_TAG_IMAGE
                imgMsg.save()

        elif len(imgMsg.media_id) == 64 and len(imgMsg.save_path) > 9 and len(imgMsg.pic_url) > 0:
            imgMsg.response = imgMsg.media_id
            imgMsg.rsp_fmt = st.MSG_TYPE_TAG_IMAGE
            imgMsg.save()
    return media_id, img_url

def _input_check_error(cmd, common_info):
    rsp = common_info.get("response", "输入错误")
    return rsp, st.MSG_TYPE_TAG_TEXT

def _help_info(cmd, common_info):
    wx_user = common_info.get("UserObj", None)

    rsp = ""
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_INFO, d="本帮助信息")
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_REPEAT, d="重复上一个回答完了的问题({n}分钟内的).".format(n=st.MSG_RECENT_MINUTES_FOR_HELP))
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_CONTINUE, d="继续之前就绪但未答完的问题({n}分钟内的).".format(n=st.MSG_RECENT_MINUTES_FOR_HELP))
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_MODELS, d="当前账号可用模型列表")
    rsp += "\n"

    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_PROMPT, d="查询当前账号特殊提示设定")
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_PROMPT_IMG, d="当前账号对图片的提示设定")
    rsp += "{c}  {d}\n".format(c=st.HELP_CMD_PROMPT_PDF, d="当前账号对PDF的提示设定")
    rsp += "\n"

    if wx_user and wx_user.vav or wx_user.always_voice:
        rsp += "{c}{d}\n".format(c="", d="支持语音问答,可通过以下指令调整语音:")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_INFO, d="查询语音AI相关设定")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_SWITCH, d="切换语音AI的男女声")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_NEXT, d="换到下一AI声音.")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_PREV, d="换回上一AI声音.")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_CN, d="切换成中文模型声音.")
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_EN, d="切换成英文模型声音.")
        rsp += "\n"
        rsp += "{c}  {d}\n".format(c=st.HELP_CMD_VOICE_ALWAYS, d="尽量都语音回答的开关.")
        rsp += "\n"

    # rsp += "{c}{d}\n".format(c="\n", d="AI为你写诗\n    为你作画\n    为你写代码\n    为你讲故事...")
    # rsp += "{c}  {d}\n".format(c="\n", d="有事问AI，AI is AI;")
    rsp += "{c}{d}\n".format(c="", d="随时随地随便问，AI欢迎你!")
    rsp += "\n"

    if wx_user.is_manager():
        rsp += "{c}  {d}\n".format(c="#", d=mgr_query_help_cmd(common_info))
        rsp += "\n"

    rsp += "\n"
    return rsp, st.MSG_TYPE_TAG_TEXT

def _try_get_last_msg(common_info, rsp_done):
    """
    """
    wx_user = common_info['UserObj']
    with_ai = wx_user.always_ai or wx_user.enable_ai

    assocTxtMsg = None
    lastMsg = None

    src_msg_type = None
    # src_event_type = None
    while True:
        for msg_type, msgClass in MSG_TYPE_MAP_MSG_CLASS.items():
            lastMsg = msgClass.objects.filter(with_ai=with_ai, wx_user=wx_user, rsp_done=rsp_done, rsp_len__gte=F('rsp_offset'))\
                                        .filter(msg_time__gt=timezone.now() - timedelta(seconds=st.MSG_RECENT_SECONDS_FOR_HELP))\
                                        .order_by('-id')[ : 1]
            if lastMsg and lastMsg.count() > 0:
                src_msg_type = msg_type
                lastMsg = lastMsg[0]
                if VERBOSE_LOG: logger.info("Find last msg: {l}".format(l=lastMsg))
                break

        if isinstance(lastMsg, WXUserMsgBaseModel): break

        for _, msgClass in EVENT_TYPE_MAP_EVENT_CLASS.items():
            lastMsg = msgClass.objects.filter(with_ai=with_ai, wx_user=wx_user, rsp_done=rsp_done, rsp_len__gte=F('rsp_offset'))\
                                        .filter(msg_time__gt=timezone.now() - timedelta(seconds=st.MSG_RECENT_SECONDS_FOR_HELP))\
                                        .order_by('-id')[ : 1]
            if lastMsg and lastMsg.count() > 0:
                src_msg_type = st.MSG_TYPE_TAG_EVENT
                # src_event_type = event_type
                lastMsg = lastMsg[0]
                if VERBOSE_LOG: logger.info("Find last event msg: {l}".format(l=lastMsg))
                break
        break

    if isinstance(lastMsg, WXUserMsgBaseModel) and src_msg_type == st.MSG_TYPE_TAG_TEXT:
        assocTxtMsg = lastMsg
        assocMsg = None
        while True:
            for msg_type, msgClass in MSG_TYPE_MAP_MSG_CLASS.items():
                if st.MSG_TYPE_TAG_TEXT == msg_type: continue

                assocMsg = msgClass.objects.filter(msg_id=assocTxtMsg.msg_id, rsp_done=rsp_done, rsp_len__gte=F('rsp_offset')).order_by('-id')[:1]
                #assocMsg = msgClass.objects.filter(msg_id=assocTxtMsg.msg_id).order_by('-id')[:1]
                if assocMsg and assocMsg.count() > 0:
                    assocMsg = assocMsg[0]
                    src_msg_type = msg_type
                    if VERBOSE_LOG: logger.info("Find last msg: {l} assoc text smg:{t}".format(l=assocMsg, t=assocTxtMsg))
                    break

            if isinstance(assocMsg, WXUserMsgBaseModel):
                lastMsg = assocMsg
                break

            for _, msgClass in EVENT_TYPE_MAP_EVENT_CLASS.items():
                assocMsg = msgClass.objects.filter(msg_id=assocTxtMsg.msg_id, rsp_done=rsp_done, rsp_len__gte=F('rsp_offset')).order_by('-id')[:1]
                #assocMsg = msgClass.objects.filter(msg_id=assocTxtMsg.msg_id).order_by('-id')[:1]
                if assocMsg and assocMsg.count() > 0:
                    src_msg_type = st.MSG_TYPE_TAG_EVENT
                    #src_event_type = event_type
                    assocMsg = assocMsg[0]
                    if VERBOSE_LOG: logger.info("Find last event msg: {l} assoc text smg:{t}".format(l=assocMsg, t=assocTxtMsg))
                    break

            if isinstance(assocMsg, WXUserMsgBaseModel):
                lastMsg = assocMsg
                break

            break
    if assocTxtMsg and lastMsg and assocTxtMsg.rsp_fmt == st.MSG_TYPE_TAG_VOICE and len(assocTxtMsg.response) == 64  \
      and (lastMsg.rsp_fmt != st.MSG_TYPE_TAG_VOICE or lastMsg.response != assocTxtMsg.response):
        lastMsg.rsp_fmt = assocTxtMsg.rsp_fmt
        lastMsg.response = assocTxtMsg.response
        lastMsg.rsp_len = len(lastMsg.response)
        lastMsg.save()
    elif assocTxtMsg and lastMsg and assocTxtMsg.rsp_fmt == st.MSG_TYPE_TAG_IMAGE and len(assocTxtMsg.response) == 64  \
      and (lastMsg.rsp_fmt != st.MSG_TYPE_TAG_IMAGE or lastMsg.response != assocTxtMsg.response):
        lastMsg.rsp_fmt = assocTxtMsg.rsp_fmt
        lastMsg.response = assocTxtMsg.response
        lastMsg.rsp_len = len(lastMsg.response)
        lastMsg.save()
    elif assocTxtMsg and lastMsg and lastMsg.rsp_fmt == st.MSG_TYPE_TAG_IMAGE and len(lastMsg.response) != 64:
        media_id, img_url = try_upload_img_from_url(lastMsg.wx_user, lastMsg.wx_user.wx_dyh, lastMsg.response)
        if media_id:
            lastMsg.remark = lastMsg.response[:1024]
            lastMsg.response = media_id
            lastMsg.rsp_len = len(lastMsg.response)
            lastMsg.save()
        elif img_url:
            pass
        else:
            lastMsg.rsp_fmt = st.MSG_TYPE_TAG_TEXT
            lastMsg.save()

    logger.info("lastMsg: {l}, assocTxtMsg: {a}".format(l=lastMsg, a=assocTxtMsg))
    return lastMsg, assocTxtMsg

def _continue(cmd, common_info):
    """
    对还没有回答完的问题继续, 已经回答完的忽略
    """
    wx_user = common_info['UserObj']
    rsp = None
    rsp_fmt = st.MSG_TYPE_TAG_TEXT

    rsp_done = False
    lastMsg, assocTxtMsg = _try_get_last_msg(common_info, rsp_done)
    if isinstance(lastMsg, WXUserMsgBaseModel):
        user_id = wx_user.id
        with_ai = wx_user.enable_ai or wx_user.always_ai
        lastMsg.incr_wx_notify_times()
        if not lastMsg.bk_done and lastMsg.wx_notify_times % (st.WX_MAX_REPPOST_TIMES*2)  == (st.WX_MAX_REPPOST_TIMES-1):
            # 重试一定次数后还没处理完的 发后台 AI 重新处理
            from dyh.msg_pro.views import BackgroundWorker
            prms = (user_id, with_ai, lastMsg.get_msg_id(), lastMsg.get_msg_type(), lastMsg.get_event_type(), lastMsg.msg_md5)
            threading.Thread(target=BackgroundWorker, args=prms).start()

        rsp = lastMsg.format4rsp2wx_user()
        rsp_fmt = lastMsg.rsp_fmt
        if assocTxtMsg and assocTxtMsg != lastMsg:
            assocTxtMsg.incr_wx_notify_times()
            if lastMsg.bk_done:
                assocTxtMsg.finish_response_process()

        mtip = lastMsg.get_manager_tip()
        if mtip and lastMsg.get_msg_type() == st.MSG_TYPE_TAG_TEXT and len(rsp) != 64 and 0 <= lastMsg.rsp_offset and  lastMsg.rsp_offset <= st.RSP_MAX_LEN :
            rsp = "{mt}问(id:{i}-{t}): {q}\n\n答: {a}"\
                .format(mt=mtip, i=lastMsg.id, t=lastMsg.get_msg_type(), q=lastMsg.content, a=rsp)
        return rsp, rsp_fmt
    else:
        return None, None


def _repeat(cmd, common_info):
    """
    对已经回答完的重复, 没回答完的忽略
    """
    # return "TODO cmd", st.MSG_TYPE_TAG_TEXT
    wx_user = common_info['UserObj']
    rsp = None
    rsp_fmt = st.MSG_TYPE_TAG_TEXT

    rsp_done = True
    lastMsg, assocTxtMsg = _try_get_last_msg(common_info, rsp_done)
    if lastMsg:
        user_id = wx_user.id
        with_ai = wx_user.enable_ai or wx_user.always_ai

        lastMsg.incr_wx_notify_times()
        if not lastMsg.bk_done and lastMsg.wx_notify_times % (st.WX_MAX_REPPOST_TIMES*2)  == (st.WX_MAX_REPPOST_TIMES-1):
            # 重试一定次数后还没处理完的 发后台 AI 重新处理
            from dyh.msg_pro.views import BackgroundWorker
            prms = (user_id, with_ai, lastMsg.get_msg_id(), lastMsg.get_msg_type(), lastMsg.get_event_type(), lastMsg.msg_md5)
            threading.Thread(target=BackgroundWorker, args=prms).start()
        elif lastMsg.bk_done and lastMsg.rsp_done:
            lastMsg.reset_rsp_offset()

        rsp = lastMsg.format4rsp2wx_user()
        rsp_fmt = lastMsg.rsp_fmt
        if assocTxtMsg and assocTxtMsg != lastMsg:
            assocTxtMsg.incr_wx_notify_times()
            if lastMsg.bk_done:
                assocTxtMsg.finish_response_process()

        mtip = lastMsg.get_manager_tip()
        if mtip and lastMsg.get_msg_type() == st.MSG_TYPE_TAG_TEXT and len(rsp) != 64 and 0 <= lastMsg.rsp_offset and  lastMsg.rsp_offset <= st.RSP_MAX_LEN :
            rsp = "{mt}问(id:{i}-{t}): {q}\n\n答: {a}"\
                .format(mt=mtip, i=lastMsg.id, t=lastMsg.get_msg_type(), q=lastMsg.content, a=rsp)
        return rsp, rsp_fmt
    else:
        return None, None

def _swtich_voice_lang_cn(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        common_info["UserObj"].voice_lang = "CN"
        common_info["UserObj"].save()
        return "语音模型切换到中文", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None
def _swtich_voice_lang_en(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        common_info["UserObj"].voice_lang = "EN"
        common_info["UserObj"].save()
        return "Voice model Changed to English", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _query_voice_setting(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        gender = wx_user.voice_gender  % 2
        info = "当前模型语音性别: {g}\n".format(g = "男" if gender == 1 else "女")
        info += "当前模型语音语言: {l}\n".format(l = wx_user.voice_lang)
        info += "当前尽量语音回复开关状态: {s}\n".format(s = "开启" if wx_user.always_voice == 1 else "关闭")
        return info, st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _swtich_voice_gender(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        gender = (common_info["UserObj"].voice_gender + 1) % 2
        common_info["UserObj"].voice_gender = gender
        common_info["UserObj"].save()
        switch = "男" if gender == 1 else "女"
        return "设定切换到{s}音".format(s=switch), st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _swtich_voice_on_always(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        wx_user.always_voice = not wx_user.always_voice 
        wx_user.save()
        return "设定尽量语音回复:{s}".format(s= "Y" if wx_user.always_voice else "N"), st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _voice_next_one(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        common_info["UserObj"].voice_idx += 1
        common_info["UserObj"].save()
        return "语音切换到下一位", st.MSG_TYPE_TAG_VOICE
    else:
        return None, None

def _voice_prev_one(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        common_info["UserObj"].voice_idx -= 1
        if common_info["UserObj"].voice_idx < 0:
            common_info["UserObj"].voice_idx = 0
            common_info["UserObj"].save()
            return "已经是首位了，不能再上一位", st.MSG_TYPE_TAG_VOICE
        else:
            common_info["UserObj"].save()
            return "语音切换到上一位", st.MSG_TYPE_TAG_VOICE
    else:
        return None, None

def _update_prompt4img_detect(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        content = common_info['Content']
        info = content.split(" ")
        if len(info) < 2:
            prompt= wx_user.img_prompt
            if not prompt:
                prompt = "无"
            elif len(prompt) > 450:
                prompt= "[{h} ... {t}]".format(h=prompt[:200], t=prompt[-200:])
            return "您当前的图片提示设定: [{p}]".format(p=prompt), st.MSG_TYPE_TAG_TEXT
        else:
            pass
            wx_user.img_prompt = " ".join(info[1:])[:4000]
            wx_user.save()
            return "您的图片提示已经更新，可以发图片让我识别了", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _update_prompt4pdf_detect(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        content = common_info['Content']
        info = content.split(" ")
        if len(info) < 2:
            prompt= wx_user.pdf_prompt
            if not prompt:
                prompt = "无"
            elif len(prompt) > 450:
                prompt= "[{h} ... {t}]".format(h=prompt[:200], t=prompt[-200:])
            return "您当前的PDF提示设定: [{p}]".format(p=prompt), st.MSG_TYPE_TAG_TEXT
        else:
            pass
            wx_user.pdf_prompt = " ".join(info[1:])[:4000]
            wx_user.save()
            return "您的PDF提示已经更新，可以发pdf文档在线链接让我分析了", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _query_prompt_setting(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        prompt = wx_user.img_prompt
        if not prompt:
            prompt = "无"
        elif len(prompt) > 25:
            prompt= "[{h} ... {t}]".format(h=prompt[:10], t=prompt[-10:])
        info = "您当前的图片提示设定: [{p}]\n".format(p = prompt)

        prompt = wx_user.pdf_prompt
        if not prompt:
            prompt = "无"
        elif len(prompt) > 25:
            prompt= "[{h} ... {t}]".format(h=prompt[:10], t=prompt[-10:])
        info += "\n您当前的PDF提示设定: [{p}]\n".format(p = prompt)
        return info, st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _list_current_user_models(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        content = common_info['Content']
        info = content.strip().split(" ")

        cfgs = get_all_available_models(wx_user)
        mlist = []

        for model_type, cfg_list in cfgs.items():
            tip = "{t} : ".format(t=model_type)
            for c in cfg_list:
                for m in c.enable_models.all():
                    if m.the_type.tag == model_type:
                        tip = "{t}\n    {c} : {m}".format(t=tip, c=c, m=m.tag)
                        break
            mlist.append(tip)
        return "当前各种转换模型:\n    " + "\n    ".join(mlist) + "\n", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _list_the_type_models(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        content = common_info['Content']
        info = content.strip().split(" ")
        if len(info) == 2:
            type_tag = info[1]
            # models = AIModel.objects.filter(the_type__tag =  type_tag)
            # mlist = []
            # the_type = None
            # if models.count() == 0:
            #     mlist.append("未找到该类型 [{t}] 到模型.".format(t=type_tag))
            # else:
            #     for m in models:
            #         the_type = m.the_type
            #         mlist.append("Status:{s}, {v}({vt}), {m}({tg}).".\
            #             format(v=m.vender, vt=m.vender.tag, m=m.name, tg=m.tag, s=m.is_active))
            # models = "\n    ".join(mlist) + "\n"
            # if the_type:
            #     tip = "{n} {t} 模型列表:\n    {m}".format(t=the_type.tag, n=the_type.name, m=models)
            # else:
            #     tip = "{t} 模型列表:\n    {m}".format(t=info[0], m=models)

            tip = ""
            user_models = WXAIConfig.objects.filter(owner = wx_user)
            if user_models.count() == 0:
                tip += "\n当前账号无可切换[{t}]模型".format( t= type_tag )
            else:
                tip += "\n当前账号可切换[{t}]模型:".format( t= type_tag )
                mtips = ""
                for um in user_models:
                    for m in um.enable_models.all():
                        if m.the_type.tag == type_tag:
                            fr = "{f}".format(f=um.start_time)
                            to = "{t}".format(t=um.end_time)
                            t = "ID:{i}, Status:{s}, {vt}, {tg}, times:{ut}/{ct}，date:{fr},{to}."\
                                .format(i=um.id, s=um.is_active, vt=um.vender.tag, tg=m.tag,\
                                        ut=um.used_times, ct=um.closed_times, fr=fr[:19], to=to[:19])
                            mtips += "\n    {t}".format(t=t)
                if len(mtips) > 0:
                    tip += mtips
                else:
                    tip += " [无]"
            return tip, st.MSG_TYPE_TAG_TEXT
        else:
            rsp = common_info.get("response", "输入参数错误")
            return rsp, st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _set_the_type_models(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        wx_user = common_info["UserObj"]
        content = common_info['Content']
        info = content.strip().split(" ")
        if len(info) == 3:
            tip = ""
            type_tag = info[1]
            the_target = info[2]

            user_cfg_models = WXAIConfig.objects.filter(owner = wx_user)
            if user_cfg_models.count() == 0:
                tip += "\n当前账号无可切换[{t}]模型.".format( t= type_tag )
            else:
                the_cfg = None
                the_model = None
                for um in user_cfg_models:
                    found_type = False
                    target_cfg = False
                    for m in um.enable_models.all():
                        if m.the_type.tag == type_tag:
                            found_type = True

                        the_id = "{i}".format(i = um.id)
                        if m.the_type.tag == type_tag and (the_target == m.vender.tag or the_target == the_id):
                            target_cfg = True
                            the_model = m
                            break

                    if target_cfg:
                        um.is_active = True
                        the_cfg = um
                        um.save()
                    elif found_type:
                        um.is_active = False
                        um.save()
                if the_cfg:
                    tip += "\n当前账号切换[{t}]模型实例配置为:{v}, {m}"\
                        .format(t= type_tag, v=the_target, m=the_model)
                else:
                    tip += "\n当前账号切换[{t}]模型实例配置失败!"\
                        .format(t= info[1], )
            return tip, st.MSG_TYPE_TAG_TEXT
        else:
            rsp = common_info.get("response", "输入参数错误")
            return rsp, st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

def _current_models_opt(cmd, common_info):
    if isinstance(common_info, dict) and isinstance(common_info.get("UserObj", None), WXUser):
        content = common_info['Content']
        info = content.strip().split(" ")
        cnt = len(info)
        if cnt < 2:
            return _list_current_user_models(cmd, common_info)

        if cnt == 2:
            return _list_the_type_models(cmd, common_info)

        if cnt == 3:
            return _set_the_type_models(cmd, common_info)

        return "输入参数错误!", st.MSG_TYPE_TAG_TEXT
    else:
        return None, None

HELP_CMD_MAP_PROCESS = {
    st.HELP_CMD_INPUT_ERROR: _input_check_error,
    st.HELP_CMD_INFO: _help_info,
    st.HELP_CMD_CONTINUE: _continue,
    st.HELP_CMD_REPEAT: _repeat,
    st.HELP_CMD_VOICE_INFO: _query_voice_setting,
    st.HELP_CMD_VOICE_SWITCH: _swtich_voice_gender,
    st.HELP_CMD_VOICE_ALWAYS: _swtich_voice_on_always,
    st.HELP_CMD_VOICE_NEXT: _voice_next_one,
    st.HELP_CMD_VOICE_PREV: _voice_prev_one,

    st.HELP_CMD_VOICE_CN: _swtich_voice_lang_cn,
    st.HELP_CMD_VOICE_EN: _swtich_voice_lang_en,

    st.HELP_CMD_MODELS: _current_models_opt,

    st.HELP_CMD_PROMPT: _query_prompt_setting,
    st.HELP_CMD_PROMPT_IMG: _update_prompt4img_detect,
    st.HELP_CMD_PROMPT_PDF: _update_prompt4pdf_detect,
}

def process_as_cmd(cmd, common_info):
    cmd = cmd.strip()
    processor  = HELP_CMD_MAP_PROCESS.get(cmd.strip(), None)
    if processor:
        rsp, rsp_fmt = processor(cmd, common_info)
        if rsp:
            common_info['response'] = rsp
        return rsp, rsp_fmt
    elif cmd in SYS_CMD_MAP_PROCESS:
        processor = SYS_CMD_MAP_PROCESS.get(cmd, (None,None))[0]
        if processor:
            mockWxMsg = WXUser() # DONT save it!!!
            mockWxMsg.content = cmd
            mockWxMsg.wx_user = common_info['UserObj']
            mockWxMsg.wx_dyh = common_info['DyhObj']
            rsp = processor(mockWxMsg)
            return rsp, st.MSG_TYPE_TAG_TEXT

    return None, None

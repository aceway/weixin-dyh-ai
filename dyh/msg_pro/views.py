# -*- coding:utf-8 -*-
import time
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

from django.shortcuts import render
from django.utils import timezone


from dyh.settings import HELP_CMD_INPUT_ERROR
from dyh.settings import REQ_MIN_LEN
from dyh.settings import REQ_MAX_LEN

from dyh.settings import WX_API_DOMAIN
from dyh.settings import CATCH_EXCEPTION
from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import MSG_TYPE_TAG_IMAGE
from dyh.settings import MSG_TYPE_TAG_VOICE
from dyh.settings import MSG_TYPE_TAG_LOCATION
from dyh.settings import MSG_TYPE_TAG_VIDEO
from dyh.settings import MSG_TYPE_TAG_SHORTVIDEO
from dyh.settings import MSG_TYPE_TAG_LINK

from dyh.settings import EVENT_TYPE_TAG_SUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_UNSUBSCRIBE
from dyh.settings import EVENT_TYPE_TAG_MENU
from dyh.settings import EVENT_TYPE_TAG_SCAN
from dyh.settings import EVENT_TYPE_TAG_LOCATION
from dyh.settings import EVENT_TYPE_TAG_CLICK

from dyh.utils import got_str_md5

from dyh.ai import aiType
from dyh.ai import utils as ai_utils
from dyh.ai.models import try_get_ai_for_user

from dyh.msg_pro.utils import get_sys_cmd_text
from dyh.msg_pro.utils import get_help_cmd_text

from dyh.msg_pro.BaseModel import WXUserMsgBaseModel
from dyh.msg_pro.models import WXUserMsgVoice
from dyh.msg_pro.models import confirm_msg_in_db
from dyh.msg_pro.models import get_text_msg_by_msg_id
from dyh.msg_pro.models import get_msg_from_db
from dyh.msg_pro.utils import parse_user_question_by_AI


#from dyh.dyh_mgr.models import WXUser
from dyh.weixin_api_mgr.WeixinApiMgr import WeixinApiMgr


# 每种消息类型的处理函数
from dyh.weixin_msg import wx_text
from dyh.weixin_msg import wx_image
from dyh.weixin_msg import wx_voice
from dyh.weixin_msg import wx_video
from dyh.weixin_msg import wx_link
from dyh.weixin_msg import wx_location
WEIXIN_MESSAGE_PROCESSOR = {
    MSG_TYPE_TAG_TEXT: wx_text.process_message,
    MSG_TYPE_TAG_IMAGE: wx_image.process_message,
    MSG_TYPE_TAG_VOICE: wx_voice.process_message,
    MSG_TYPE_TAG_VIDEO: wx_video.process_message,
    MSG_TYPE_TAG_SHORTVIDEO: wx_video.process_message,  # TODO: WARN take as video
    MSG_TYPE_TAG_LOCATION: wx_location.process_message,
    MSG_TYPE_TAG_LINK: wx_link.process_message,
}

from dyh.weixin_msg import wx_event
WEIXIN_EVENT_PROCESSOR = {
    EVENT_TYPE_TAG_SUBSCRIBE: wx_event.process_event_subscribe,
    EVENT_TYPE_TAG_UNSUBSCRIBE: wx_event.process_event_unsubscribe,
    EVENT_TYPE_TAG_MENU: wx_event.process_event_menu,
    EVENT_TYPE_TAG_CLICK: wx_event.process_event_click,
    EVENT_TYPE_TAG_SCAN: wx_event.process_event_scan,
    EVENT_TYPE_TAG_LOCATION: wx_event.process_event_location,
}
def get_wx_msg_processor(msg_type, event_type = None):
    if event_type:
        return WEIXIN_EVENT_PROCESSOR.get(event_type, None)
    else:
        return WEIXIN_MESSAGE_PROCESSOR.get(msg_type, None)

def pre_process_message(common_info):
    """
    预处理
    """

    content = ""
    while True:
        wx_user = common_info.get("UserObj", None)
        dyh = common_info.get("DyhObj", None)
        msg_type = common_info.get('MsgType', "")
        if msg_type == MSG_TYPE_TAG_TEXT:
            content = common_info.get('Content', "").strip()
            break
        elif dyh and msg_type == MSG_TYPE_TAG_VOICE:
            media_id = common_info.get("MediaId", None)
            fmt = common_info.get("Format", None)
            if not media_id or not fmt:
                if wx_user and wx_user.is_manager():
                    rsp = "语音消息格式缺失MediaId或Format: {i}".format(i=common_info)
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')
                else:
                    rsp = "语音消息格式异常"
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, rsp

            wxApiMgr = WeixinApiMgr(dyh.dyh_appid.strip(), dyh.appsecret.strip(), WX_API_DOMAIN)
            mpath = wxApiMgr.tmp_get_media_path(media_id)
            if mpath is None:
                logger.error("Get the voice media_id's url failed: {i}.".format(i=common_info))
                if wx_user and wx_user.is_manager():
                    rsp = "查询语音medial_id的URL失败"
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')
                else:
                    rsp = "查询语音信息异常"
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')

            url = "https://{d}{s}".format(d=WX_API_DOMAIN, s=mpath)

            msg_id = common_info.get("MsgId", "")
            mockMsg = WXUserMsgVoice(msg_type=msg_type, msg_id=msg_id, content= url)
            mockMsg.msg_md5 = got_str_md5(url)
            mockMsg.wx_user = wx_user
            mockMsg.msg_time = timezone.now()
            mockMsg.media_id = media_id
            mockMsg.format = fmt
            mockMsg.url = url
            mockMsg.with_ai = True
            result = ai_utils.sync_send_req2ai(mockMsg, replace_content=url, ext_format=fmt, specail_model_type=aiType.VOICE2TXT, auto_update_rsp=False)
            ok = result['ok']
            txt = result['answer']
            desc = result['desc']
            if not ok:
                logger.error("Parse the voice to text failed: {t} {d}.".format(t=txt, d=desc))
                if wx_user and wx_user.is_manager():
                    rsp = "语音识别失败: {t} {d}.".format(t=txt, d=desc)
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')
                else:
                    rsp = "语音识别失败, 请发送文字交流."
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')

            if len(txt) < 2:
                if wx_user and wx_user.is_manager():
                    rsp = "没听清: [{t}], 请再说一遍".format(t=txt)
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')
                else:
                    rsp = "没听清, 请再说一遍."
                    common_info['response'] = rsp
                    return HELP_CMD_INPUT_ERROR, common_info.get('content', '')

            content = txt
            common_info['Content'] = content
            common_info['MsgMd5'] = got_str_md5(common_info['Content'])
            logger.info("Got voice's tex : {t}.".format(t=txt))
        break

    if content:
        help_cmd = get_help_cmd_text(content)
        if help_cmd:
            return help_cmd, content

        sys_cmd = get_sys_cmd_text(content)
        if sys_cmd:
            return sys_cmd, content

        if len(content) > REQ_MAX_LEN:
            rsp = "内容太长，请一次不要超过{m}字!".format(m=REQ_MAX_LEN)
            common_info['response'] = rsp
            return HELP_CMD_INPUT_ERROR, content

        if len(content) < REQ_MIN_LEN:
            rsp = "内容太短，请一次不要少于{m}字!".format(m=REQ_MIN_LEN)
            common_info['response'] = rsp
            return HELP_CMD_INPUT_ERROR, content


    wxMsg = confirm_msg_in_db(common_info)
    if wxMsg is None:
        logger.error('pre_process_message {i} error!'.format(i=common_info))
        return None, None

    if isinstance(wxMsg, WXUserMsgBaseModel):
        wxMsg.incr_wx_notify_times()
        if wxMsg.msg_type == "EVENT" and wxMsg.event_type == EVENT_TYPE_TAG_SUBSCRIBE:
            if wxMsg.wx_notify_times % 3 == 1:
                wxMsg.resonse = ""
            wxMsg.reset_rsp_offset()

        if VERBOSE_LOG:
            logger.info("pre_process_message wx notify msg times {t} for {u}"\
                .format(t=wxMsg.wx_notify_times, u=wxMsg.wx_user))
        return wxMsg, wxMsg.rsp_fmt
    else:
        tip = "未支持到信息消息类型: {m}".format(m=wxMsg)
        logger.error(tip)
        return tip, MSG_TYPE_TAG_TEXT

def post_process_message(wxMsg, common_info=None, force=False):
    """
    后处理
    """
    rsp = None
    try:
        wxMsg.refresh_from_db()
        rsp = wxMsg.format4rsp2wx_user(force = force)
        if VERBOSE_LOG:
            logger.info("post_process_message format4rsp2wx_user msg: {m}, rsp: {r}".format(r=rsp, m=wxMsg))
    except CATCH_EXCEPTION as e:
        tip = '_verify_msg_signature exception: {e}.'.format(e=e)
        logger.error(tip)
        print(e)

        if wxMsg.wx_user.is_manager():
            rsp = "仅manager可见:" + tip
        else:
            rsp = "内部错误..."

    if not rsp:
        return None, None
    else:
        return rsp, wxMsg.rsp_fmt

def BackgroundWorker(user_id, with_ai, msg_id, msg_type, event_type, msg_md5):
    """
    转后台工作线程
    """
    # first try change requet question into text - Use AI capabilities to enhance the intelligence
    # give the prompt same special tag, example:
    rsp = None
    wxMsg = None
    do_times = 0
    max_try_times = 10
    start_timestamp = time.time()
    while do_times < max_try_times:
        do_times += 1
        #wxMsg = get_text_msg_by_msg_id(msg_id)
        wxMsg = get_msg_from_db(user_id, with_ai, msg_id, msg_type, event_type, msg_md5)
        if not isinstance(wxMsg, WXUserMsgBaseModel) or len(wxMsg.content.strip()) == 0:
            logger.warn("[BackgroundWorker]Got wxMsg object from db invalid, msg_id: {i}, msg: {m}!".format(i=msg_id, m=wxMsg))
            do_times += 1
            time.sleep(1)
            continue
        elif VERBOSE_LOG:
            logger.info("[BackgroundWorker]Got wxMsg object from db ok, msg_id: {i}, msg: {m} content: {c}.".format(i=msg_id, m=wxMsg, c=wxMsg.content))

        aiCfg, reason = try_get_ai_for_user(wxMsg.wx_user)
        if not aiCfg:
            rsp = reason
            wxMsg.finish_background_process_with_response(rsp)
            break

        if VERBOSE_LOG:
            logger.info("[BackgroundWorker] AI for user: {i}, {r}".format(i=user_id, r=rsp))

        msg_type_prompt = parse_user_question_by_AI(wxMsg)

        msg_type = wxMsg.get_msg_type()
        event_type = wxMsg.get_event_type()
        processor = get_wx_msg_processor(msg_type, event_type)
        if processor:
            if VERBOSE_LOG:
                logger.info("[BackgroundWorker] process {p} for user: {i}, {r}".format(p=processor, i=user_id, r=rsp))
            rsp = processor(wxMsg, msg_type_prompt = msg_type_prompt)
            if rsp: break
        else:
            tips = "[BackgroundWorker]Got wxMsg but the [{t} {e}] has no processor, {m}!"\
                .format(m=wxMsg, t=msg_type, e=event_type)
            rsp = tips
            logger.error(tips)
            break

        break # end of while True

    end_timestamp = time.time()
    m = wxMsg or msg_id
    if rsp:
        if not wxMsg.bk_done:
            wxMsg.finish_background_process_with_response(rsp)

        if VERBOSE_LOG:
            logger.info("[BackgroundWorker]Finish done msg ok, tried times {t}, cost sec {s}, msg {m} rsp: {r}"\
                .format(t=do_times, s=end_timestamp-start_timestamp, m=m, r=rsp[:32]))
    else:
        if VERBOSE_LOG:
            logger.info("[BackgroundWorker]No rsp for msg now, tried times {t}, cost sec {s}: {m}"\
                .format(m=m, t=do_times, s=end_timestamp-start_timestamp))

# -*- coding:utf-8 -*-
'''
*对微信服务器传来的用户发送的语音信息进行解析,回复*

- Args:
    - xml_tree_data: xml格式的微信消息, 详细参见微信的协议结构
    - data_finder: 在xml格式的微信消息里查找本消息内容的tag名

- Return:
    - 成功 按照微信各种消息格式返回加密的信息, 失败返回None
'''
import os
import time
import logging
logger = logging.getLogger('django')
VERBOSE_LOG=False

from django.utils import timezone


from dyh import settings
from dyh.settings import WX_API_DOMAIN
from dyh.settings import MSG_TYPE_TAG_VOICE
from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import HELP_CMD_INPUT_ERROR

from dyh import utils
from dyh.ai import aiType

from dyh.dyh_mgr.models import WXUser

from dyh.msg_pro.utils import process_as_cmd
from dyh.msg_pro.utils import get_help_cmd_text
from dyh.msg_pro.utils import get_sys_cmd_text

from dyh.msg_pro.models import WXUserMsgText
from dyh.msg_pro.models import WXUserMsgVoice
from dyh.msg_pro.models import copy_msg2txt_msg
from dyh.weixin_msg import wx_text

from dyh.weixin_api_mgr.WeixinApiMgr import WeixinApiMgr

from dyh.ai import utils as ai_utils

def process_message(wxMsg, msg_type_prompt=None):
    """
    过程内部基于同步实现, 语音已经在预处理中转换成文字放在 Content, content里
    且命令类的消息，也已经在预处理中干掉类
    """

    #wxMsg.content = ""
    #wxMsg.reset_rsp_offset()
    if VERBOSE_LOG:
        logger.info("Got voice msg:{m} {c}".format(m=wxMsg, c=wxMsg.content))

    if isinstance(wxMsg, WXUserMsgVoice):
        if VERBOSE_LOG: logger.info('process_message start {m}: {c}'.format(m=wxMsg, c=wxMsg.content))
    else:
        logger.error('process_message error, it is not voice msg {m}: {c}'.format(m=wxMsg))
        return None

    assocTxtMsg = copy_msg2txt_msg(wxMsg)
    if isinstance(assocTxtMsg, WXUserMsgText):
        pass
    else:
        logger.error('process_message error, it is not voice msg {m}: {c}'.format(m=wxMsg))
        return None

    result = None
    r1 = {}
    r2 = {}
    while True:
        r1 =  {'ok': True, 'text': wxMsg.content, 'desc': wxMsg.media_id}
        r2 = _get_text_answer_of_request(wxMsg, assocTxtMsg, r1)
        result = try_trans_answer2voice(wxMsg, r2)
        break

    if isinstance(result, dict) and result.get('ok', False):
        wxMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
        if len(result.get('desc', "")) > 60:
            time.sleep(4)  # 等待语音审核时间
        else:
            time.sleep(1)
        wxMsg.finish_background_process_with_response(result['answer'])
    else:
        wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT
        wxMsg.finish_background_process_with_response(result['desc'])

def _get_text_answer_of_request(wxMsg, assocTxtMsg, pre_result):
    req_txt =  pre_result['text'] if pre_result['ok'] else pre_result['desc']
    assocTxtMsg.content = req_txt
    result = ai_utils.sync_send_req2ai(assocTxtMsg, replace_content = req_txt, specail_model_type=aiType.TXT2TXT, auto_update_rsp=False)
    ok = result['ok']
    answer = result['answer']
    desc = result['desc']
    #print("XXXXXX", ok, answer, desc)
    if ok:
        assocTxtMsg.finish_background_process_with_response(answer)
        return {'ok': True, 'desc': desc, 'answer': answer}
    else:
        assocTxtMsg.remark = desc[:1024]
        assocTxtMsg.finish_background_process_with_response(answer)
        return {'ok': False, 'desc': desc, 'answer': answer or desc}

def try_trans_answer2voice(wxMsg, pre_result):
    wx_user = wxMsg.wx_user
    pre_txt =  pre_result['answer'] if pre_result['ok'] else pre_result['desc']
    if len(pre_txt) == 64 and wxMsg.rsp_fmt == MSG_TYPE_TAG_VOICE:
        return {"ok": True, 'answer': pre_txt, 'desc': "Help cmd got rsp"}

    wx_user = wxMsg.wx_user
    dyh = wx_user.wx_dyh

    answer = None
    use_voice2answer = False
    while True:
        if not (settings.DEFAULT_ENABLE_ALL_VOICE_ANSWER_VOICDE or wx_user.vav):
            use_voice2answer = False
            answer = pre_txt
            break

        if not (wxMsg.save_path.startswith(settings.DOWNLOAD_FILE_PATH) and os.path.isfile(wxMsg.save_path)):
            result = ai_utils.sync_send_req2ai(wxMsg, replace_content=pre_txt, specail_model_type=aiType.TXT2VOICE, auto_update_rsp=False)
            ok = result['ok']
            vfile = result['answer']
            desc = result['desc']
            if not (ok and vfile.startswith(settings.DOWNLOAD_FILE_PATH) and os.path.isfile(vfile)):
                use_voice2answer = False
                answer = pre_txt
                break
            wxMsg.save_path = vfile

        wxApiMgr = WeixinApiMgr(dyh.dyh_appid.strip(), dyh.appsecret.strip(), WX_API_DOMAIN)
        result = wxApiMgr.upload_media(wxMsg.save_path, "voice")
        if isinstance(result, dict) and 'media_id' in result and  len(result['media_id'].strip()) > 0:
            use_voice2answer = True
            answer = result['media_id']
        else:
            use_voice2answer = False
            answer = pre_txt
        break

    return {"ok": use_voice2answer, 'answer': answer, 'desc': pre_txt}

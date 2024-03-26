# -*- coding:utf-8 -*-
''' 
*对微信服务器传来的用户发送的图片信息进行解析,回复*

- Args:
    - xml_tree_data: xml格式的微信消息, 详细参见微信的协议结构
    - data_finder: 在xml格式的微信消息里查找本消息内容的tag名

- Return:
    - 成功 按照微信各种消息格式返回加密的信息, 失败返回None
'''
import time
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import datetime
from django.utils import timezone
from dyh.utils import got_str_md5

from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import MSG_TYPE_TAG_IMAGE
from dyh.settings import MSG_TYPE_TAG_VOICE

from dyh.msg_pro.models import WXUserMsgImage
from dyh.msg_pro.models import WXUserMsgVoice
from dyh.msg_pro.models import WXUserMsgText
from dyh.msg_pro.models import confirm_msg_in_db

from dyh.weixin_msg.wx_voice import try_trans_answer2voice

from dyh.ai import aiType
from dyh.ai import utils as ai_utils

def process_message(wxMsg, msg_type_prompt=None):
    auto_update_txt_result = not wxMsg.wx_user.always_voice
    result = ai_utils.sync_send_req2ai(wxMsg, specail_model_type=aiType.IMG2TXT, auto_update_rsp=auto_update_txt_result)
    ok = result['ok']
    response = result['answer']
    desc = result['desc']
    if ok:
        if VERBOSE_LOG:
            logger.info("User confged always_voice: {v} of {u}"\
                .format(v=wxMsg.wx_user.always_voice, u=wxMsg.wx_user))

        if wxMsg.rsp_fmt != MSG_TYPE_TAG_TEXT:
            wxMsg.remark = desc[:1024]
            wxMsg.save()
            wxMsg.finish_background_process_with_response(response)
            return response

        if not wxMsg.wx_user.always_voice:
            wxMsg.remark = desc[:1024]
            wxMsg.save()
            wxMsg.finish_background_process_with_response(response)
            return response

        mock_info = {"UserObj": wxMsg.wx_user, "DyhObj": wxMsg.wx_user.wx_dyh}
        mock_info['MsgId'] = wxMsg.msg_id
        mock_info['nonce'] =  wxMsg.nonce
        mock_info['CreateTime'] = wxMsg.msg_time.timestamp()

        mock_info['MsgType'] = MSG_TYPE_TAG_VOICE
        mock_info['Content'] = response
        mock_info['MsgMd5'] =  got_str_md5(response)
        mockVoiceMsg = confirm_msg_in_db(mock_info)
        if not isinstance(mockVoiceMsg, WXUserMsgVoice):
            wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT
            wxMsg.save()
            wxMsg.finish_background_process_with_response(response)
            return response

        mock_info = {"UserObj": wxMsg.wx_user, "DyhObj": wxMsg.wx_user.wx_dyh}
        mock_info['MsgId'] = wxMsg.msg_id
        mock_info['nonce'] =  wxMsg.nonce
        mock_info['CreateTime'] = wxMsg.msg_time.timestamp()

        mock_info['MsgType'] = MSG_TYPE_TAG_TEXT
        mock_info['Content'] = response
        mock_info['MsgMd5'] =  got_str_md5(response)
        mockTxtMsg = confirm_msg_in_db(mock_info)
        if not isinstance(mockTxtMsg, WXUserMsgText):
            wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT
            wxMsg.save()
            wxMsg.finish_background_process_with_response(response)
            return response

        txt_rsp = {'ok': True, 'desc': "of img desc", 'answer': response}
        result = try_trans_answer2voice(mockVoiceMsg, txt_rsp)
        if isinstance(result, dict) and result.get('ok', False) and len(result['answer']) == 64:
            rsp = result['answer']
            mockVoiceMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
            mockVoiceMsg.remark = response[:1024]
            mockVoiceMsg.save()
            mockVoiceMsg.finish_background_process_with_response(rsp)

            mockTxtMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
            mockTxtMsg.remark = response[:1024]
            mockTxtMsg.save()
            mockTxtMsg.finish_background_process_with_response(rsp)

            wxMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
            wxMsg.remark = response[:1024]
            wxMsg.save()
            wxMsg.finish_background_process_with_response(rsp)
            if len(response) > 60:
                time.sleep(4)  # 等待语音审核时间
            else:
                time.sleep(2)
            return rsp
        else:
            wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT
            wxMsg.save()
            wxMsg.finish_background_process_with_response(response)
            return response
    else:
        logger.error("process image to text failedd: {r} {d}".format(r=response, d=desc))
        return desc


# -*- coding:utf-8 -*-
'''
*对微信服务器传来的用户发送的事件信息进行解析,回复*

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

from django.utils import timezone, dateformat

from dyh.ai import aiType
from dyh.ai import utils as ai_utils

from dyh.msg_pro.models import WXUserEventSubscribe


# Create your views here.
def process_event_subscribe(eMsg, msg_type_prompt = None):
    if eMsg.wx_user.wx_dyh.welcome and len(eMsg.wx_user.wx_dyh.welcome.strip()) > 0:
        tip = eMsg.wx_user.wx_dyh.welcome.strip()
    else:
        tip = '对AI感兴趣的新朋友加入，请简洁快速地致欢迎词! 询他进一步需求, 并告诉他发送 ? 查看帮助, 欢迎随时和AI交流!'
    tip = "random:{r} {t}".format(r=time.time(), t=tip)
    logger.info("Welcome prompt for {u}: {t}".format(u=eMsg.wx_user, t=tip))
    result = ai_utils.sync_send_req2ai(eMsg, replace_content=tip, specail_model_type=aiType.TXT2TXT)
    ok = result['ok']
    response = result['answer']
    desc = result['desc']
    if ok:
        eMsg.remark = desc[:1024]
        eMsg.finish_background_process_with_response(response)
        return response
    else:
        logger.error("process image to text failedd: {r} {d}".format(r=response, d=desc))
        eMsg.remark = desc[:1024]
        eMsg.finish_background_process_with_response("欢迎关注.")
        return desc

def process_event_unsubscribe(eMsg, msg_type_prompt = None):
    rsp = "谢谢, 再见, 欢迎今后再关注(订阅号)."
    eMsg.response = rsp
    eMsg.finish_background_process_with_response(rsp)
    return rsp

def process_event_scan(eMsg, msg_type_prompt = None):
    logger.info("Event scan: {e}".format(e=eMsg))

def process_event_location(eMsg, msg_type_prompt = None):
    logger.info("Event location: {e}".format(e=eMsg))

def process_event_click(eMsg, msg_type_prompt = None):
    logger.info("Event click: {e}".format(e=eMsg))

def process_event_message(eMsg, msg_type_prompt=None):
    logger.info("Event: {e}".format(e=eMsg))

def process_event_menu(eMsg, msg_type_prompt=None):
    logger.info("Event menu: {e}".format(e=eMsg))
    eMsg.finish_response_process()
    eMsg.finish_background_process_with_response("")

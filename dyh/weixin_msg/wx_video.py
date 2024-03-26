# -*- coding:utf-8 -*-
''' 
*对微信服务器传来的用户发送的视频信息进行解析,回复*

- Args:
    - xml_tree_data: xml格式的微信消息, 详细参见微信的协议结构
    - data_finder: 在xml格式的微信消息里查找本消息内容的tag名

- Return:
    - 成功 按照微信各种消息格式返回加密的信息, 失败返回None
'''
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

def process_message(wxMsg, msg_type_prompt=None):
    logger.info("Video message: {m}".format(m=wxMsg))


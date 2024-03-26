#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: ./TENCENT_HUNYUAN.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年03月17日 星期日 13时26分48秒
#  Description: ...
# 混元大模型： https://console.cloud.tencent.com/hunyuan/standard-stats
# 
########################################################################
import json
import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

from http import HTTPStatus

from dyh.ai.tencent import modelInstance

from tencentcloud.common import credential
#from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

SecretId = "***************"
SecretKey = None
Region = "ap-guangzhou"
# 华北地区（北京）	ap-beijing
# 华南地区（广州）	ap-guangzhou


from dyh.settings import AI_REM_HIS_LINES

def call_with_messages(model, prompt, from_uid, key, config_json):
    if key:
        SecretKey = key

    PRE_TIP = "你是位回答用户问题的专业人士，回答问题严格遵纪守法，文明礼貌! "
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
        SecretId = config_json.get('SecretId', SecretId)
    else:
        config_json = {}

    if cfg_tip:
        PRE_TIP = cfg_tip

    msgs = []
    if isinstance(config_json.get('messages', None), (list, tuple)):
        msgs += config_json['messages']
    else:
        msgs.append({'role': 'assistant', 'content': PRE_TIP})

    content = "{p}".format(p=prompt)
    msgs.append({'role': "user", 'content': content})
    keep_len = AI_REM_HIS_LINES
    if keep_len > len(msgs):
        keep_len = len(msgs)

    if keep_len % 2 == 0:
        keep_len -= 1

    sys_prompt = config_json.get('sys_prompt', ["You are a helpful assistant, try to be like humanbeen, DON’T reveal your AI’s identity and DO NOT reveal the identity of the language model"])

    messages = [{'role': "system", 'content': ";".join(sys_prompt) }] +  msgs[ -keep_len: ]
    if VERBOSE_LOG:
        logger.info("Request messages to ali model {m}: {r}".format(m=model, r=messages))

    ok = False
    answer = '...'
    desc = ''
    ############################################
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户secretId，secretKey
        cred = credential.Credential( SecretId, SecretKey)
        cpf = ClientProfile()
        # 预先建立连接可以降低访问延迟
        cpf.httpProfile.pre_conn_pool_size = 2
        client = hunyuan_client.HunyuanClient(cred, Region, cpf)

        if model == modelInstance.TENCENT_HUNYUAN_CHASTD:
            req = models.ChatStdRequest()
        elif model == modelInstance.TENCENT_HUNYUAN_CHATPRO:
            req = models.ChatProRequest()
        else:
            return {'ok': False, 'answer': "Not found the model: {m}".format(m=model), 'desc': "model config error."}

        req.Messages = []
        for m in messages:
            msg = models.Message()
            msg.Role = m['role']
            msg.Content = m['content']
            req.Messages.append(msg)
        resp = client.ChatStd(req)

        full_content = ""
        total_token = 0
        for event in resp:
            data = json.loads(event['data'])
            total_token += data['Usage']['TotalTokens']
            for choice in data['Choices']:
                full_content += choice['Delta']['Content']

        answer = full_content
        desc = "OK, token:{t}".format(t=total_token)
        ok = True
    except TencentCloudSDKException as err:
    #except IndexError as err:
        #print(err)
        logger.error("Tencent hunyuan except: {e}".format(e=err))
        answer = "error: {e}".format(e=err)
        desc = "exception"
        ok = False

    if VERBOSE_LOG:
        logger.info("Tencent hunyuan ok: {o}, answer: {a}, desc:{d}"\
            .format(o=ok, a=answer, d=desc))
    return {'ok': ok, 'answer': answer, 'desc': desc}
    ############################################

if __name__ == '__main__':
	pass

#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: ./TENCENT_HUNYUAN.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年03月17日 星期日 13时26分48秒
#  Description: ...
# docs： https://platform.moonshot.cn/docs/api-reference
########################################################################
import json
import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

from openai import OpenAI
from http import HTTPStatus


from dyh.settings import AI_REM_HIS_LINES

def call_with_messages(model, prompt, from_uid, key, config_json):
    SecretKey = key
    PRE_TIP = "你是位回答用户问题的专业人士，不说AI模型，回答问题严格遵纪守法，文明礼貌! "
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
    else:
        config_json = {}

    if cfg_tip:
        PRE_TIP = cfg_tip

    msgs = []
    if isinstance(config_json.get('messages', None), (list, tuple)):
        msgs += config_json['messages']
    else:
        msgs.append({'role': 'assistant', 'content': PRE_TIP})

    content = prompt
    msgs.append({'role': "user", 'content': content})
    keep_len = AI_REM_HIS_LINES
    if keep_len > len(msgs):
        keep_len = len(msgs)

    if keep_len % 2 == 0:
        keep_len -= 1

    sys_prompt = config_json.get('sys_prompt', ["You are a helpful assistant, try to be like humanbeen, DON’T reveal your AI’s identity and DO NOT reveal the identity of the language model"])

    messages = [{'role': "system", 'content': ";".join(sys_prompt) }] +  msgs[ -keep_len: ]
    if VERBOSE_LOG:
        logger.info("Request messages to kimi model {m}: {r}".format(m=model, r=messages))

    url = config_json.get('url', "https://api.moonshot.cn/v1")
    ok = False
    answer = '...'
    desc = ''
    ############################################
    try:
        client = OpenAI(
            api_key = key,
            base_url = url,
        )

        completion = client.chat.completions.create(
          model = model,
          messages = messages,
          temperature=0.3,
          max_tokens=1024,
          n = 1,
        )

        if len(completion.choices) > 0 and completion.choices[0].message and completion.choices[0].message.content:
            answer = completion.choices[0].message.content
            total_token = completion.usage.total_tokens
            desc = "OK, used token:{t}".format(t=total_token)
            ok = True
        else:
            total_token = completion.usage.total_tokens
            answer = "ERROR: {e}".format(e=completion.choices)
            desc = "Failed, used token:{t}".format(t=total_token)
            ok = False
    except IndexError as err:
        logger.error("Kimi moonshot except: {e}".format(e=err))
        answer = "error: {e}".format(e=err)
        desc = "exception"
        ok = False

    if VERBOSE_LOG:
        logger.info("Kimi moonshot ok: {o}, answer: {a}, desc:{d}"\
            .format(o=ok, a=answer, d=desc))
    return {'ok': ok, 'answer': answer, 'desc': desc}
    ############################################

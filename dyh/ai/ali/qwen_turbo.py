#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: testQW1.5.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月23日 星期五 23时52分08秒
#  Description: ...
# 
########################################################################
import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

import dashscope
from http import HTTPStatus
MODEL=dashscope.Generation.Models.qwen_turbo

def call_with_messages(model, prompt, from_uid, key, config_json):
    PRE_TIP = "You are a helpful assistant."
    if config_json.get("pdf_prompt", ""):
        pdf_prompt = config_json['pdf_prompt']
        PRE_TIP = "{t}. 用户提示：'{p}'!".format(t = PRE_TIP, p=pdf_prompt)
    elif config_json.get("pri_prompt", ""):
        pri_prompt = config_json['pri_prompt']
        PRE_TIP = "{t}. 用户提示：'{p}'!".format(t = PRE_TIP, p=pri_prompt)


    dashscope.api_key = key
    if 'plugins' in config_json and isinstance(config_json['plugins'], dict):
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': [
                {'text': PRE_TIP},
                {'file': prompt}]
             }]
        plugins = {'pdf_extracter': {}}
        logger.info("Model {m} process url pdf file: {msg}".format(m=model, msg=messages))
    else:
        plugins = None
        messages = [{'role': 'system', 'content': PRE_TIP},
                    {'role': 'user', 'content': prompt}]

    response = dashscope.Generation.call(
        model=model,
        messages=messages,
        result_format='message',
        plugins=plugins,
    )

    ok = False
    answer = '...'
    desc = ''

    if response.status_code != HTTPStatus.OK:
        print(response)
        ok = False
        answer = '...'
        desc = '{m} 服务返回错误, status:{s}'.format(m=model, s=response.status_code)
        return {'ok': ok, 'answer': answer, 'desc': desc}

    if isinstance(response.output, dict) and \
      isinstance(response.output.get('choices', None), list) and \
      len(response.output.get('choices')) > 0 and \
      isinstance(response.output['choices'][0].get('message', None), dict):
        answer = ""
        choices = response.output.get('choices')
        for ch in choices:
            if isinstance(ch, dict) and isinstance(ch.get('message', None), dict):
                answer = ch['message'].get('content', "").strip()

            if len(answer) > 0:
                break
        if len(answer) == 0:
            tip='not found content in response object:{r}'.format(m=response)
            answer = "no AI answer"
            ok = False
            desc = tip
        else:
            desc = "OK"
            ok = True
    else:
        tip = 'response object check failed: {r}'.format(r=response)
        desc = tip
        answer = "no AI answer"
    return {'ok': ok, 'answer': answer, 'desc': desc}

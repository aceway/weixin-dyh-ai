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
import dashscope
from dashscope import Generation
from http import HTTPStatus

import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

def call_with_messages(model, prompt, from_uid, key, config_json):
    PRE_TIP = "你是位高级程序员，编程专家, 精通各种算法，处理问题简明扼要，问答严格遵纪守法，文明礼貌! "
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
    if cfg_tip:
        PRE_TIP = cfg_tip

    dashscope.api_key = key
    response = Generation.call(
        model= model,
        prompt= prompt,
    )

    ok = False
    answer = '...'
    desc = ''

    if response.status_code != HTTPStatus.OK:
        print(response)
        ok = False
        answer = '...'
        desc = '{m} 服务返回错误, status:{s}, response:{r}'.format(m=model, s=response.status_code, r=response.output)
        logger.error(desc)
        return {'ok': ok, 'answer': answer, 'desc': desc}

    logger.info("xxxxxxx: {r}".format(r=response.output))

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

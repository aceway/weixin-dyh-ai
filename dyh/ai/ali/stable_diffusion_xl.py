#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: testDF.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月23日 星期五 23时15分41秒
#  Description: ...
# 
########################################################################

import requests
import dashscope

from http import HTTPStatus



def call_with_messages(model, prompt, from_uid, key, config_json):
    PRE_TIP = "你是位回答用户问题的专业人士，不说AI模型，回答问题严格遵纪守法，文明礼貌! "
    dashscope.api_key = key
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
        if cfg_tip is not None:
            PRE_TIP = cfg_tip

    #prompt = "{t}Message from user: {u}.用户要画的场景描述:{p}".format(t = PRE_TIP, u=from_uid, p=prompt)
    prompt = "{t}.用户要画的场景描述:{p}".format(t = PRE_TIP, u=from_uid, p=prompt)
    response = dashscope.ImageSynthesis.call(model=model,
                                        prompt=prompt,
                                        negative_prompt="garfield",
                                        n=4,
                                        size='512*512')
                                        #size='1024*1024')
    ok = False
    answer = '...'
    desc = ''

    if response.status_code != HTTPStatus.OK:
        print(response)
        ok = False
        answer = '...'
        desc = '{m} 服务返回错误, status:{s}'.format(m=model, s=response.status_code)
        return {'ok': ok, 'answer': answer, 'desc': desc}

    if response.output and isinstance(response.output.results, list) and len(response.output.results) > 0:
        answer = "图片:\n{r}".format( r= "\n".join(response.output.results) ) 
    else:
        tip = 'response object check failed: {r}'.format(r=response)
        desc = tip
        answer = "no AI answer"
    return {'ok': ok, 'answer': answer, 'desc': desc}

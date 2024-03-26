#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: test.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月23日 星期五 22时43分45秒
#  Description: ...
#  TODO: 候补的OCR替换成阿里的：https://help.aliyun.com/document_detail/270960.html?spm=5176.28306286.commonbuy2container.1.3506778by9DCPR
########################################################################
import logging
logger = logging.getLogger('default')

import dashscope
from http import HTTPStatus
from dyh.ai import aiType

MODEL = dashscope.MultiModalConversation.Models.qwen_vl_chat_v1

def call_with_messages(model, prompt, from_uid, key, config_json):
    logger.info('testVL got model {m}, prompt: [{p}], uid: {u}, cfg json: {j}'.format(m=model, p=prompt, u=from_uid, j=config_json))
    ok = False
    answer = '...'
    desc = ''

    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
        image_url = config_json.get("image_url", None)

    if image_url is None:
        lp = prompt.strip().lower()
        if lp.startswith("http://") or lp.startswith("https://"):
            for ext in aiType.SUPPORT_IMG_EXT:
                if ext in lp:
                    image_url = prompt
    if image_url is None:
        ok = False
        answer = "No AI answer"
        desc = "Not found image to desc"
        return {'ok': ok, 'answer': answer, 'desc': desc}

    PRE_TIP = "你是位图画鉴赏家，识别图片高手，回答问题严格遵纪守法，文明礼貌! "
    if cfg_tip:
        PRE_TIP = cfg_tip

    if config_json.get("img_prompt", ""):
        img_prompt = config_json['img_prompt']
        prompt = "{t}. 用户提示：'{p}'!".format(t = PRE_TIP, p=img_prompt)
    elif config_json.get("pri_prompt", ""):
        pri_prompt = config_json['pri_prompt']
        prompt = "{t}. 用户提示：'{p}'!".format(t = PRE_TIP, p=pri_prompt)
    else:
        prompt = "{t}. 用户提示内容：图片中有什么物品, 是什么样的场景? 请详细描述! 如果不能作为图画识别请在回复中明确说明'{v}', 不要说抱歉, 并尝试识别其中的文字!".format(t = PRE_TIP, v=VL_UNKNOW_TAG)


    dashscope.api_key = key
    messages = [
        {
            "role": "user",
            "content": [
                {"image": image_url},
                {"text": prompt}
            ]
        }
    ]
    response = dashscope.MultiModalConversation.call(model= MODEL, messages=messages)
    print("qwen_vl_chat_v1 result detail: ", response)

    if response.status_code != HTTPStatus.OK:
        print(response)
        ok = False
        answer = '...'
        desc = '{m} 服务返回错误, status:{s}'.format(m=model, s=response.status_code)
        return ok, answer, desc

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
            ok = True
            desc = "OK"
    else:
        tip = 'response object check failed: {r}'.format(r=response)
        desc = tip
        answer = "no AI answer"
    return {'ok': ok, 'answer': answer, 'desc': desc}

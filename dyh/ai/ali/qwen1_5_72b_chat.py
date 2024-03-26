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
import json
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import random
import dashscope
from http import HTTPStatus
from dashscope.api_entities.dashscope_response import Role

from dyh.settings import AI_REM_HIS_LINES

def call_with_messages(model, prompt, from_uid, key, config_json):
    PRE_TIP = "你是位回答用户问题的专业人士，不说AI模型，回答问题严格遵纪守法，文明礼貌! "
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
    else:
        config_json = {}

    if cfg_tip:
        PRE_TIP = cfg_tip

    dashscope.api_key = key
    msgs = []
    if isinstance(config_json.get('messages', None), (list, tuple)):
        msgs += config_json['messages']
    else:
        msgs.append({'role': 'assistant', 'content': PRE_TIP})

    if len(prompt) < 20 and 0 <= prompt.find('换') <  prompt.find('音'):
        json_need = """请以纯JSON 格式回复—勿包含注释—并确保所有回复内容都在JSON结构内。回复的JSON中使用'rsp_fmt'字段指示用户的提示是希望用语音还是文本问答的意图：0表示希望文本，1表示希望语音; 使用'switch_voice'字段指示用户切换语音的意图，1表示是要切换成其它语音，0表示保持原语音。问题本身的答案放在'answer'字段, 但其中不要嵌套子JSON字段, 'answer'里不要包含本提示信息。示例: {'rsp_fmt': 1, 'switch_voice': 1, 'answer': "收到消息，好的."}"""

        content = "用户本次的问题：{p}。这是关于问答形式的说明,不是问题本身：{t}".format(p=prompt, t=json_need)
    else:
        json_need = False
        content = "{p}".format(p=prompt)

    msgs.append({'role': Role.USER, 'content': content})
    keep_len = AI_REM_HIS_LINES
    if keep_len > len(msgs):
        keep_len = len(msgs)

    if keep_len % 2 == 0:
        keep_len -= 1

    sys_prompt = config_json.get('sys_prompt', ["You are a helpful assistant, try to be like humanbeen, DON’T reveal your AI’s identity and DO NOT reveal the identity of the language model"])

    messages = [{'role': "system", 'content': ";".join(sys_prompt) }] +  msgs[ -keep_len: ]
    if VERBOSE_LOG:
        logger.info("Request messages to ali model {m}: {r}".format(m=model, r=messages))

    response = dashscope.Generation.call(model,
        messages=messages,
        seed=random.randint(1, 1000),
        result_format='message',
    )

    ok = False
    answer = '...'
    desc = ''

    if response.status_code != HTTPStatus.OK:
        logger.error("Ali model server http rsp: {r}".format(r=response))
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
            if VERBOSE_LOG:
                logger.info("Ali model server http rsp: {r}".format(r=response))

            if isinstance(ch, dict) and isinstance(ch.get('message', None), dict):
                answer = ch['message'].get('content', "").strip()

            if json_need and len(answer) > 1:
                got_json = False
                fr = 0
                to = 0
                cutted = None
                try:
                    if answer[0] == "{" and answer[-1] == "}":
                        answer = json.loads(answer)
                        got_json = False
                    else:
                        fr = answer.find("{")
                        to = answer.rfind("}") + 1
                        if 0 <= fr and fr < to:
                            cutted = answer[fr:to]
                            answer = json.loads(cutted)
                            got_json = False
                    if got_json and VERBOSE_LOG:
                        logger.info("Parse respose as json ok: {r}".format(r=response.output))
                except Exception as e:
                    logger.error("Parse respose as json error {e}, {f}-{t}: {r}, {c}".format(e=e, f=fr, t=to, r=answer, c=cutted))
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

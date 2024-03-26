#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: queryAI.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月24日 星期六 10时48分52秒
#  Description: ...
# 混元大模型： https://console.cloud.tencent.com/hunyuan/standard-stats
########################################################################
import logging
logger = logging.getLogger('default')

from dyh.ai.tencent import tx_voice
from dyh.ai.tencent import hunyuan
from dyh.ai.tencent import modelInstance as mInstance

def chatWithAI(prompt, from_uid, model = None, key=None, config_json=None):
    model_tag = None
    if model:
        model_tag = model.tag
    else:
        return {'ok': False, 'answer': "Tencent model cfg invalid", 'desc': "The tencent model cfg is invalid in db"}

    if key is None:
        return {'ok': False, 'answer':"Tencent KEY cfg invalid", 'desc': "The tencent key cfg is invalid in db"}

    if model_tag in (mInstance.TENCENT_HUNYUAN_CHATPRO, mInstance.TENCENT_HUNYUAN_CHASTD, mInstance.TENCENT_HUNYUAN_GETEMBEDDING):
        return hunyuan.call_with_messages(model_tag, prompt, from_uid, key, config_json)
    elif model_tag in (mInstance.TENCENT_VOICE_ONE_SENTENCE, ):
        return tx_voice.call_with_messages(model_tag, prompt, from_uid, key, config_json)
    else:
        answer = 'no AI answer'
        desc = 'some thing wrong model tag: {m}'.format(m=model_tag)
        logger.info("response msg from ali AI model tag {m}: {md}"\
            .format(m=model_tag, md=model))
        return {'ok':False, 'answer': answer, 'desc': desc}

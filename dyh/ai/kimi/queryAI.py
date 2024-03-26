#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: queryAI.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月24日 星期六 10时48分52秒
#  Description: ...
# docs： https://platform.moonshot.cn/docs/api-reference
########################################################################
import logging
logger = logging.getLogger('default')

from dyh.ai.kimi import modelInstance as mInstance

from dyh.ai.kimi import moonshot

def chatWithAI(prompt, from_uid, model = None, key=None, config_json=None):
    model_tag = None
    if model:
        model_tag = model.tag
    else:
        answer = "No kimi model"
        desc = "Please check kimi config in db."
        return {'ok': False, 'answer': answer, 'desc': desc}

    if model_tag in (mInstance.KIMI_MOONSHOT_V1_8K, mInstance.KIMI_MOONSHOT_V1_32K, mInstance.KIMI_MOONSHOT_V1_128K):
        return moonshot.call_with_messages(model_tag, prompt, from_uid, key, config_json)
    else:
        answer = 'no AI answer'
        desc = 'some thing wrong model tag: {m}'.format(m=model_tag)
        logger.info("response msg from kimi AI model tag {m}: {md}"\
            .format(m=model_tag, md=model))
        return {'ok': False, 'answer': answer, 'desc': desc}

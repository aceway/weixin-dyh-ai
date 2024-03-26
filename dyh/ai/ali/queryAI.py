#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: queryAliAI.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月24日 星期六 10时48分52秒
#  Description: ...
# 
########################################################################
import logging
logger = logging.getLogger('default')

import dashscope
from http import HTTPStatus

from dyh.ai.ali import modelInstance as mInstance

from dyh.ai.ali import qwen1_5_72b_chat
from dyh.ai.ali import qwen_turbo
from dyh.ai.ali import qwen_vl_chat_v1
from dyh.ai.ali import qwen_vl_plus

from dyh.ai.ali import stable_diffusion_xl
from dyh.ai.ali import wanx_sketch_to_image_v1
from dyh.ai.ali import paraformer
from dyh.ai.ali import sambert
from dyh.ai.ali import sanle

from dyh.ai.ali import ali_voice

from dyh.ai.ali.sambert import get_ali_support_voice_list


def chatWithAI(prompt, from_uid, model, key, config_json):
    model_tag = model.tag

    if model_tag in (mInstance.ALI_QWEN_TURBO, mInstance.ALI_QWEN_PLUS, mInstance.ALI_QWEN_MAX, mInstance.ALI_QWEN_MAX_1201, mInstance.ALI_QWEN_MAX_LONGCONTEXT):
        return qwen_turbo.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_QWEN1_5_72B_CHAT, mInstance.ALI_QWEN1_5_14B_CHAT, mInstance.ALI_QWEN1_5_7B_CHAT, mInstance.ALI_QWEN_PLUS ):
        return qwen1_5_72b_chat.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_QWEN_VL_CHAT_V1, mInstance.ALI_QWEN_VL_V1):
        return qwen_vl_chat_v1.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_QWEN_VL_PLUS, mInstance.ALI_QWEN_VL_MAX):
        return qwen_vl_plus.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_WANX_V1, mInstance.ALI_WANX_SKETCH_TO_IMAGE_V1):
        return wanx_sketch_to_image_v1.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_PARAFORMER_V1, mInstance.ALI_PARAFORMER_8K_V1, mInstance.ALI_PARAFORMER_MTL_V1,):
        return paraformer.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag == mInstance.ALI_SAMBERT  or  model_tag in get_ali_support_voice_list():
        return sambert.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag in (mInstance.ALI_VOICE_ONE_SENTENCE, ) :
        return ali_voice.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag == mInstance.ALI_STABLE_DIFFUSION_XL:
        return stable_diffusion_xl.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    elif model_tag == mInstance.ALI_SANLE_V1:
        return sanle.call_with_messages(model_tag, prompt, from_uid, key, config_json)

    else:
        answer = 'no AI answer'
        desc = 'some thing wrong model tag: {m}'.format(m=model_tag)
        logger.info("response msg from ali AI model tag {m}: {md}"\
            .format(m=model_tag, md=model))
        return {'ok': False, 'answer': answer, 'desc': desc}

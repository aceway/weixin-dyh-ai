#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: aiAgent.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月24日 星期六 11时58分00秒
#  Description: ...
# 
########################################################################
import os
import sys
import argparse

import importlib

import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False


from dyh.ai import openai
from dyh.ai import ali
from dyh.ai import tencent
from dyh.ai import kimi

def get_ai_vender_names():
    names = []
    names.append( 'ali' )
    names.append( 'openai')
    names.append( 'tencent')
    names.append( 'kimi')
    return names

AI_PLUGIN_DIR = os.path.dirname(__file__)
_ai_venders_model_processor = {}
def _load_ai_venders_model_processor():
    logger.info("AI vender plugins is here: {p}".format(p=AI_PLUGIN_DIR))
    for vender in os.listdir(AI_PLUGIN_DIR):
        vp = os.path.join(AI_PLUGIN_DIR, vender)
        aiApi = os.path.join(vp, "queryAI.py")
        if os.path.isdir(vp) and  os.path.isfile(aiApi):
            mname = "dyh.ai.{v}".format(v = vender)
            module = importlib.import_module(mname)
            if hasattr(module, 'queryAI') and hasattr(module.queryAI, 'chatWithAI'):
                _ai_venders_model_processor[vender] = module
                logger.info("    Loaded AI vender [{v}] module OK!".format(v=vender))
            else:
                logger.warn("    AI vender [{v}] module API is not fully implemented.".format(v=vender))

def chatWithAI(prompt, fromUid, model, key=None, config_json=None):
    logger.info("Ask AI model [{m}] for prompt: {p}".format(m=model, p=prompt))
    result = {'ok': False, 'answer': "", 'desc': " wait " }
    prompt = prompt.strip()
    if len(prompt) <= 2 or len(prompt.strip(".!?,-。！？，-")) == 0:
        result['ok'] = False
        result['answer'] = "prompt content's word not enough to chat"
        result['desc'] = "inputi error"
        return result

    try:
        venderAIModule = _ai_venders_model_processor.get(model.vender.tag, None)
        if venderAIModule:
            return venderAIModule.queryAI.chatWithAI(prompt, fromUid, model, key=key, config_json=config_json)
        else:
            result['ok'] = False
            result['answer'] = "no AI."
            result['desc'] = "No processor for the Vender [{v}]'s model [{m}]! ".format(v=model.vender, m=model)
            logger.error(result['desc'])
            return result
    except Exception as e:
        result['ok'] = False
        result['answer'] = "Exception: {e}.".format(e=e)
        result['desc'] = "Maybe AI api error"
        logger.error("AI model [{m}] except [{e}] for prompt: {p}".format(m=model, e=e, p=prompt))
        return result

_load_ai_venders_model_processor()

if __name__ == '__main__':
    translator = argparse.ArgumentParser(description="AI Agent...")
    translator.add_argument('-v', '--vender', type=str, help="Chose the AI vender in {v}.".format(v=get_ai_vender_names()), required=True)
    # translator.add_argument('-m', '--model', type=str, help="Chose the model name in {m}.".format(m = ali.getModelNames() + openai.getModelNames()), required=True)
    translator.add_argument('-m', '--model', type=str, help="Chose the model name...")
    translator.add_argument('-p', '--prompt', type=str, help="the prompt to ask AI", required=True)
    translator.add_argument('-uid', '--user_id', default="human", type=str, help="message from user, its id ", required=False)

    translator.add_argument('-u', '--url', type=str, default=None, help="the url for openAI querying ", required=False)
    translator.add_argument('-k', '--key', type=str, default=None, help="the key for AI query API, multi superate by , ", required=False)
    args = translator.parse_args()

    ret = chatWithAI(args.prompt, args.user_id, model=args.model, key=args.key)
    print(ret)

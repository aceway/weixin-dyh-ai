#!/usr/bin/env python
# -*- coding=utf-8 -*-
#import ssl
import logging
logger = logging.getLogger('django')

import copy
import random
#ssl._create_default_https_context = ssl._create_unverified_context
import json as json_parser
import requests

KEY_CONFIG = {
    'OPENAI_URL': "https://api.openai.com/v1/completions",
    'OPENAI_API_KEY': "",
}

HEADERS = {
    'User-Agent': "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    'Content-Type': "application/json",
    'Authorization': "Bearer " + KEY_CONFIG.get('OPENAI_API_KEY')
}

M_DAVINCI_003 = "text-davinci-003"
M_DAVINCI_EDIT_001 = "text-davinci-edit-001"
M_CODE_001 = "code-cushman-001"
M_CODE_002 = "code-davinci-002"
M_GPT_3_5 = "gpt-3.5-turbo"
M_DALL_E  = "DALL-E"


DEFAULT_CFG_MODEL = {
    'stat': True,
    'name': M_DAVINCI_003,
    'model': M_DAVINCI_003,
    'temperature': 0,
    'max_tokens': 512,
    'prompt': "hello world, how are you?",
}

SUPPORT_MODELS = {
    M_DAVINCI_003 : {
        'stat': True,
        'name': M_DAVINCI_003,
        'model': M_DAVINCI_003,
        'temperature': 0,
        'max_tokens': 512,
        'prompt': "hello world, how are you?",
    },
    M_CODE_001 : {
        'stat': True,
        'name': M_CODE_001,
        'model': M_CODE_001,
        'temperature': 0,
        'max_tokens': 1024,
        'prompt': "generate some javascript code to get prime number less than 1000?",
    },
    M_CODE_002 : {
        'stat': True,
        'name': M_CODE_001,
        'model': M_CODE_002,
        'temperature': 0,
        'max_tokens': 512,
        'prompt': "generate some python code to get prime number less than 1000?",
    },
    M_GPT_3_5:{
        'stat': True,
        "name": M_GPT_3_5,
        "model": M_GPT_3_5,
        "temperature": 0,
        'max_tokens': 512,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role":"assistant", "content": "Please truely and sincerly, not lie!"},
            {"role": "user", "content": "Please help me!"}
        ]
    },
    M_DALL_E: {
        'stat': True,
        "name": M_DALL_E,
        "model": M_DALL_E,
        "prompt": "A beatiful little putty rolling on the green grass ground.",
        "n": 1,
        "size": "512x512"
    }
}

def getModelNames():
    names = []
    for _, cfg in SUPPORT_MODELS.items():
        names.append( cfg['name'] )
    return names

def query_openai(url, headers, data):
    logger.debug("query_openai(url:{u}, data:{d}, headers:{h})".format(u=url, d=data, h=headers))
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code in [200, '200']:
        json_ret = json_parser.loads(response.content)
        if isinstance(json_ret, dict):
            return json_ret
        else:
            return "Got response error: {r}".format(r=json_ret)
    else:
        return "Something wrong, HTTP: {r}.".format(r=response)

def create_default_param_with_model(model):
    if model is None: model = M_DAVINCI_003

    model_prms = SUPPORT_MODELS.get(model)
    if isinstance(model_prms, dict):
        return copy.deepcopy(model_prms)
    else:
        return copy.deepcopy(DEFAULT_CFG_MODEL)

def add_prompt_for_model_params(params, query):
    model = params.get('model', None)
    if model in (M_DAVINCI_003, M_CODE_001, M_CODE_002):
        params['prompt'] = query
    elif model in (M_DALL_E,):
        params.pop('model', None)
        params['prompt'] = query
    elif model in (M_GPT_3_5, ):
        if params.get("has_history", False) is True:
            params.pop('has_history', None)
        else:
            params["messages"] = [{'role': "system", 'content': "You are a helpful assistant. Please answer truthfully and sincerely, without any lies!"}]
            params['messages'].append({'role': "assistant", 'content': "OK, I will be honest and not lie."})
            params['messages'].append({'role': "user", 'content': query})
    else:
        return False, model

    return True, model

def extract_answer_from_ai_rsp(model, response):
    logger.debug("Got model {m} response data: {r}".format(m=model, r=response))
    desc = '{m}'.format(m=model)
    ok = False
    if not isinstance(response, dict):
        answer = 'Invalid response: {r} of model {m}.'.format(r=response, m=model)
        ok = False
    elif model in (M_DAVINCI_003, M_CODE_001, M_CODE_002):
        choices = response.get("choices", "no AI answer")
        if isinstance(choices, (list,tuple)) and len(choices) > 0 and isinstance(choices[0], dict):
            answer = choices[0].get('text', "No answer words").strip()
            ok = True
            desc = 'ok'
        else:
            answer = "{a}".format(c=answer)
            ok = False
            desc = 'Failed'
    elif model in (M_GPT_3_5,):
        desc = "{m}, {u}".format(m=model, u=response.get('usage', ""))
        choices = response.get("choices", "no AI answer")
        if isinstance(choices, (list,tuple)) and len(choices) > 0 and isinstance(choices[0], dict):
            ok = True
            desc = 'ok'
            message = choices[0].get('message', "No choices words")
            if isinstance(message, dict):
                answer = message.get('content', "{m}".format(m=message))
            else:
                answer = "{m}".format(m=message)
        else:
            desc = 'Faile'
            message = choices[0].get('message', "No choices words")
            ok = False
            answer = "{a}".format(c=answer)
    elif model in (M_DALL_E,):
        data = response.get("data", "no AI image")
        if isinstance(data, (list,tuple)) and len(data) > 0 and isinstance(data[0], dict):
            answer = data[0].get('url', "No image url in data").strip()
            ok = True
            desc = 'OK'
        else:
            ok = False
            desc = 'Faile'
            answer = "{a}".format(c=answer)
    else:
        answer = "Not support model to extract response {r}".format(m=model, r=response)
        ok = False
        desc = 'Faile'
    return {'ok': ok, 'answer': answer, 'desc': desc}

def chatWithAI(query, fromUid, model = None, key=None, config_json=None):
    if model and model.URL:
        url = model.URL
    else:
        url = KEY_CONFIG.get("OPENAI_URL")

    if isinstance(config_json, dict):
        params = create_default_param_with_model(config_json.get("model", M_DAVINCI_003))
        for k, v in list(config_json.items()):
            params[k] = v
    else:
        params = copy.deepcopy(DEFAULT_CFG_MODEL)

    headers = copy.deepcopy(HEADERS)
    if key and len(key.strip()) > 0:
        headers['Authorization'] = "Bearer " + key

    ok, model_name = add_prompt_for_model_params(params, query)
    if ok is False:
        logger.error("add_prompt_for_model_params(params:{p}, query:{q}) {r}, {m}".format(p=params, q=query, r=ok, m=model_name))
        return {'ok': ok, 'answer': "no AI anser",  'desc': "Not support model: {m}".format(m=model_name)}

    response = query_openai(url, headers, params)
    return extract_answer_from_ai_rsp(model_name, response)

if __name__ == '__main__':
    import sys
    query = "Who are you?"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    qa = chatWithAI(query, 'human-test')
    print(qa)

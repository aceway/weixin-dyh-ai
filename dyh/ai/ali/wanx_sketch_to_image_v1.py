#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: testWX.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月23日 星期五 23时20分08秒
#  Description: ...
# 
########################################################################
import dashscope
from http import HTTPStatus


def call_with_messages(model, prompt, from_uid, key, config_json):
    PRE_TIP = "你是位画家, 文明礼貌，但不画暴力，色情内容! "
    if isinstance(config_json, dict):
        cfg_tip = config_json.get('pre_tip', None)
    if cfg_tip:
        PRE_TIP = cfg_tip

    dashscope.api_key = key
    #prompt = "{t}Message from user: {u}.用户要画但内容:{p}".format(t = PRE_TIP, u=from_uid, p=prompt)
    prompt = "{t}.用户要画但内容:{p}".format(t = PRE_TIP, u=from_uid, p=prompt)
    if model == 'wanx_sketch_to_image_v1':
        model = dashscope.ImageSynthesis.Models.wanx_sketch_to_image_v1
    elif model == 'wanx_v1':
        model = dashscope.ImageSynthesis.Models.wanx_v1
    else:
        model = dashscope.ImageSynthesis.Models.wanx_v1

    #  The size does not match the allowed size ['1024*1024', '720*1280', '1280*720']
    response = dashscope.ImageSynthesis.call(model=model,
                              prompt=prompt,
                              n= int(config_json.get('n', 1)),
                              size= config_json.get('size', '1024*1024')
    )
    ok = False
    answer = '...'
    desc = ''

    if response.status_code != HTTPStatus.OK:
        ok = False
        answer = '...'
        desc = '{m} 服务返回错误, status:{s}'.format(m=model, s=response.status_code)
        return {'ok': ok, 'answer': answer, 'desc': desc}

    if response.output and isinstance(response.output.results, list) and len(response.output.results) > 0:
        ok = True
        urls = []
        for result in response.output.results:
            url = result.get('url', "No image url")
            urls.append( '{u}'.format(u=url))
        if len(urls) == 1:
            answer = "{u}".format( u=urls[0])
        elif len(urls) > 0:
            answer = "图片:\n\n{r}".format( u=response.usage, r= "\n\n".join(urls))
        else:
            answer = "图片 {u}:\n{r}".format( u=response.usage, r= "\n".join(urls))
    else:
        ok = False
        tip = 'response object check failed: {r}'.format(r=response)
        desc = tip
        answer = "no AI answer"
    return {'ok': ok, 'answer': answer, 'desc': desc}


if __name__ == '__main__':
    simple_call()

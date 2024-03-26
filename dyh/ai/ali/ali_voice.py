#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 支持的输入格式：单声道（mono）16bit采样位数音频，包括无压缩的PCM、WAV、OPUS、AMR、SPEEX、MP3、AAC格式。
# 音频采样率：8000 Hz、16000 Hz。
# 时长限制：语音数据时长不能超过60s。
# 平台应用：https://nls-portal.console.aliyun.com/applist
# 文档: https://help.aliyun.com/document_detail/374321.html?spm=a2c4g.84442.0.0.7d88648e7I3ypm
# 
import os
import sys
import json
import argparse
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import requests
from http import HTTPStatus

AppId = None
AppKey = None

"""
外网访问（默认上海地域）
上海：https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr
北京：https://nls-gateway-cn-beijing.aliyuncs.com/stream/v1/asr
深圳：https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/asr

内网访问
上海：ws://nls-gateway-cn-shanghai-internal.aliyuncs.com:80/ws/v1
北京：ws://nls-gateway-cn-beijing-internal.aliyuncs.com:80/ws/v1
深圳：ws://nls-gateway-cn-shenzhen-internal.aliyuncs.com:80/ws/v1
"""
EndPoint="https://nls-gateway-cn-beijing.aliyuncs.com/stream/v1/asr"
EndPoint="https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/asr"
EndPoint="https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"

#def voice2text(url, fmt):
def call_with_messages(model, prompt, from_uid, key, config_json):
    result = {'ok': False, 'answer': "", 'desc': "no"}
    try:
        service_url = config_json.get("EndPoint", EndPoint)
        appId = config_json.get("AppId", AppId)
        appKey = config_json.get("AppKey", AppKey)

        url = prompt
        fmt = config_json.get('format', 'mp3')
        rate = config_json.get("SampleRate", 8000)

        headers = {"X-NLS-Token": appKey}
        params = {
            'audio_address': url,
            'appkey': appId,
            'format': fmt,
            'sample_rate': rate,  # 16000 or 8000
            'vocabulary_id': False,
            'customization_id': False,
            'enable_punctuation_prediction': False, # 	是否在后处理中添加标点，默认值：False（关闭。
            'enable_inverse_text_normalization': True, #ITN（逆文本inverse text normalization）中文数字转换阿拉伯数字。设置为True时，中文数字将转为阿拉伯数字输出，默认值：False。
            'enable_voice_detection': True, #是否启动语音检测。开启后能够识别出一段音频中有效语音的开始和结束，剔除噪音数据。默认值：False（不开启）。
            'disfluency': True, #过滤语气词，即声音顺滑，默认值：False（关闭）
        }
        response = requests.post(service_url, headers=headers, params=params)
        if response.status_code != HTTPStatus.OK:
            logger.error("ali server response ERROR: {r} {t}".format(r=response, t=response.text))
            result['ok'] = False
            result['answer'] = response.text or "ali server rsp http not 200", "server http rsp:{s}".format(s=response.status_code)
            result['desc'] = "HTTP status not OK"
            return result

        if VERBOSE_LOG:
            logger.info("Ali server response: {r} {t}".format(r=response, t=response.text))
        resp = json.loads(response.text)
        result['ok'] = True
        result['answer'] = resp.get('result', "").strip()
        result['desc'] = "OK"
        return result
    except Exception as e:
        logger.error("Ali voice format [{f}] to text failed: {e}, with url: {u}".format(e=e, f=fmt, u=url))
        result['ok'] = False
        result['answer'] = "trans voice to text failed: {e}".format(e=e)
        result['desc'] = "{d}".format(d=e)
        return result

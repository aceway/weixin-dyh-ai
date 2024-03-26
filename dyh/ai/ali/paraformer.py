#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: test.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月23日 星期五 22时43分45秒
#  Description: 异步的，不适合即使对话
# doc: https://help.aliyun.com/zh/dashscope/api-reference-1
# aac、amr、avi、flac、flv、m4a、mkv、mov、mp3、mp4、mpeg、ogg、opus、wav、webm、wma、wmv 
########################################################################
import requests
import json as json_parser
import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

import dashscope
from http import HTTPStatus

def call_with_messages(model, prompt, from_uid, key, config_json):
    if VERBOSE_LOG:
        logger.info('testParaformerVoice got model {m}, prompt: [{p}], uid: {u}, cfg json: {j}'\
            .format(m=model, p=prompt, u=from_uid, j=config_json))

    dashscope.api_key = key
    ok = False
    answer = '...'
    desc = ''
    url = prompt
    fmt = config_json.get('format', 'mp3')
    result = {'ok': False, 'answer': "", 'desc': " no "}

    task_response=dashscope.audio.asr.Transcription.async_call(
        model = model,
        #format = fmt,
        file_urls = [url],
        disfluency_removal_enabled = True # 过滤语气词，默认关闭
    )
    if task_response.status_code not in [200, '200']:
        result['ok'] = False
        result['answer'] = "Upload voice data to ali server failed"
        result['desc'] = '{m} status code:{c}, info: {i}'.format(m=model, c=task_response.status_code, i=task_response)
        return result

    response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
    if VERBOSE_LOG:
        logger.info("testParaformerVoice paraformer-mtl-v1 result detail: {r}".format(r=response))

    if response.status_code != HTTPStatus.OK:
        result['ok'] = False
        result['answer'] = '...'
        result['desc'] = '{m} 服务返回语音识别错误, status:{s}'.format(m=model, s=response.status_code)
        return result

    if isinstance(response.output, dict) and \
      isinstance(response.output.get('results', None), list) and len(response.output['results']) > 0:
        output = response.output
        code = output.get('code', "").strip().upper()
        result = output['results'][0]
        if code == "SUCCESS_WITH_NO_VALID_FRAGMENT":
            result['ok'] = True
            result['answer'] = ''
            result['desc'] = '没听清，需重新说一遍.'
            return result
        elif code == "USER_BIZDURATION_QUOTA_EXCEED":
            result['ok'] = False
            result['answer'] = '语音识别免费度用完，请文字交流. '
            result['desc'] = 'USER_BIZDURATION_QUOTA_EXCEED'
            return result
        elif code == "FILE_TOO_LARGE":
            result['ok'] = False
            result['answer'] = '语音量太大，请短小些. '
            result['desc'] = 'FILE_TOO_LARGE'
            return result
        elif code == "UNSUPPORTED_SAMPLE_RATE":
            result['ok'] = False
            result['answer'] = '参数错误，采样率不匹配。'
            result['desc'] = 'UNSUPPORTED_SAMPLE_RATE'
            return result
        elif code:
            result['ok'] = False
            result['answer'] = '遇到错误:[{c}]'.format(c=code)
            result['desc'] = output
            return result

        result_url = result['transcription_url']
        if VERBOSE_LOG:
            logger.info("testParaformerVoice voice text result url: {u}".format(u=result_url))

        response = requests.get(result_url)
        result['answer'] = ""
        ret = None
        if VERBOSE_LOG:
            logger.info("testParaformerVoice transcription_url result:{r}".format(r=response))

        if response.status_code in [200, '200']:
            ret = json_parser.loads(response.content)
            if isinstance(ret, dict):
                pass
            else:
                logger.error("Got response error, not dict: {r}".format(r=response.content))
                result['ok'] = False
                result['answer'] = "No AI answer "
                result['desc'] = '{m} 解析语音识别json失败: {d}'.format(m=model, d=ret)
                return result
        else:
            logger.error("Got response error, http status not 200: {r}".format(r=response))
            result['ok'] = False
            result['answer'] = "No AI answer "
            result['desc'] = '{m} 获取语音识别结果失败, status code:{c}, url:{u}'.format(m=model, c=response.status_code, u=result_url)
            return result

        if isinstance(ret, dict) and isinstance(ret.get("transcripts", None), list):
            tips = ""
            for content in ret["transcripts"]:
                tips += ' {t}'.format(t= content.get('text', ""))

            if len(tips.strip()) > 0:
                result['answer'] = "".join(tips)
            else:
                answer = ""

            if VERBOSE_LOG:
                logger.info("Get voice result: {t}".format(t=answer))
            result['ok'] = True
        else:
            tips = "内部错误: {p}.".format(p=ret)
            logger.error("Get img [{u}] text from tencent ocr server error: {e}".format(u=url, e=tips))
            result['desc'] += " " + tips
    else:
        tip = 'response object check failed: {r}'.format(r=response)
        result['desc'] = tip
        result['answer'] = "no AI answer"
    return result

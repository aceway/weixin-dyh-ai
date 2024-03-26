# -*- coding: utf-8 -*-
# doc: https://cloud.tencent.com/document/product/1093/35646
import os
import json
import argparse
import logging
logger = logging.getLogger('django')

from tencentcloud.common import credential
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from tencentcloud.asr.v20190614 import asr_client, models

AppId = None
AppKey = None
EndPoint = "asr.tencentcloudapi.com"
Region = "ap-guangzhou"

#def voice2text(url, fmt):
def call_with_messages(model, prompt, from_uid, key, config_json):
    try:
        url = prompt
        appId = config_json.get("AppId", AppId)
        appKey = config_json.get("AppKey", None)
        endPoint = config_json.get("EndPoint", EndPoint)
        region = config_json.get("Region", Region)
        engSerViceType = config_json.get("EngSerViceType", "16k_zh")

        fmt = config_json.get('format', 'mp3')

        httpProfile = HttpProfile()
        httpProfile.endpoint = endPoint
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        req = models.SentenceRecognitionRequest()
        params = {
            "Url":  url,
            "EngSerViceType": engSerViceType, # "16k_zh",
            "FilterDirty": 0, # 是否过滤脏词（目前支持中文普通话引擎）。0：不过滤脏词；1：过滤脏词；2：将脏词替换为 * 。默认值为 0。
            "FilterModal": 2, # 是否过语气词（目前支持中文普通话引擎）。0：不过滤语气词；1：部分过滤；2：严格过滤 。默认值为 0。 
            "SubServiceType": 2,
            "SourceType": 0,
            "VoiceFormat": fmt # 识别音频的音频格式，支持wav、pcm、ogg-opus、speex、silk、mp3、m4a、aac、amr。 示例值：wav
        }
        req.from_json_string(json.dumps(params))

        cred = credential.Credential(appId, appKey)
        client = asr_client.AsrClient(cred, region, clientProfile)
        resp = client.SentenceRecognition(req)
        logger.info("Tencent voice format [{f}] to text SentenceRecognition resp: {r}".format(f=fmt, r=resp))
        if resp and hasattr(resp, 'Result'):
            return True, resp.Result, "OK"
        else:
            return False, "Tencent server response error", "{r}".format(r=resp)
    except TencentCloudSDKException as e:
        logger.error("Tencent voice format [{f}] to text SentenceRecognition failed: {e}, with url: {u}".format(e=e, f=fmt, u=url))
        return False, "trans voice to text failed", "{d}".format(d=e)

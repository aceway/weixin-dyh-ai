#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: testSamBert.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月29日 星期四 16时12分36秒
#  Description: ...
# 
########################################################################
# coding=utf-8

import os
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
from django.utils import timezone

import requests
import logging
logger = logging.getLogger('default')
VERBOSE_LOG = False

from http import HTTPStatus

from dyh.utils import got_str_md5

from dyh import settings
from dyh.ai.ali import modelInstance as mInstance

SUPPORT_VOICE_EN_FEMALE_CFG = {
    mInstance.ALI_SAMBERT_BETH_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_BETTY_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_CALLY_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_CINDY_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_EVA_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_DONNA_V1: {'sample_rate': 16000, 'rate': 1},
}
SUPPORT_VOICE_EN_MALE_CFG = {
    mInstance.ALI_SAMBERT_BRIAN_V1: {'sample_rate': 16000, 'rate': 1},
}

SUPPORT_VOICE_MALE_CFG = {
    mInstance.ALI_SAMBERT_ZHICHU_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIXIANG_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHILUN_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIDA_V1: { 'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIHAO_V1: { 'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIMING_v1: { 'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIMO_V1: { 'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIYE_V1: { 'sample_rate': 16000, 'rate': 1},
}
SUPPORT_VOICE_FEMALE_CFG = {
    mInstance.ALI_SAMBERT_ZHIWEI_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIQI_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIQIAN_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIRU_V1: {'sample_rate': 48000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIMIAO_EMO_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIGUI_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIMAO_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHISTELLA_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIting_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIXIAO_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIYUAN_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIYUE_V1: {'sample_rate': 16000, 'rate': 1},
    mInstance.ALI_SAMBERT_ZHIYING_V1: {'sample_rate': 16000, 'rate': 1},
}

_voice_list = None
def get_ali_support_voice_list():
    global _voice_list
    if isinstance(_voice_list, list) and len(_voice_list) > 0:
        return _voice_list
    else:
        _voice_list = list(SUPPORT_VOICE_EN_FEMALE_CFG.keys()) + list(SUPPORT_VOICE_EN_MALE_CFG.keys()) \
            + list(SUPPORT_VOICE_MALE_CFG.keys()) + list(SUPPORT_VOICE_FEMALE_CFG.keys())
        return _voice_list

def call_with_messages(model, prompt, from_uid, key, config_json):
    if VERBOSE_LOG:
        logger.info('testSamBert got model {m}, prompt: [{p}], uid: {u}, cfg json: {j}'.format(m=model, p=prompt, u=from_uid, j=config_json))

    dashscope.api_key = key
    ok = False
    answer = '...'
    desc = ''

    if not isinstance(config_json, dict):
        config_json = {}

    file_format = "mp3"

    now = timezone.now()
    local_time = timezone.localtime(now)
    str_time = local_time.strftime('%Y%m%d')
    md5 = got_str_md5(prompt)
    if len(prompt) > 12:
        p = prompt.strip().replace(" ", "-")
        tip = p[:6] + md5 + p[-6:]
    else:
        tip = prompt[:12].strip().replace(" ", "-") + md5

    fname = "{s}{t}.{f}".format(s=str_time, t=tip, f=file_format)
    save_path = os.path.join(settings.DOWNLOAD_FILE_PATH, 'audio')
    settings.force_mkdir(save_path)
    save_file = os.path.join(save_path, fname)
    if os.path.isfile(save_file):
        ok = True
        answer = save_file
        desc = "the audio file has been exists in local!"
        return {'ok': ok, 'answer': answer, 'desc': desc}

    voice_lang = config_json.get("voice_lang", "CN").strip().upper()
    if voice_lang == "EN":
        gender = int(config_json.get('voice_gender', 0))
        voice_cfg = None
        if gender % 2 == 0:
            voice_cfg = SUPPORT_VOICE_EN_FEMALE_CFG
        else:
            voice_cfg = SUPPORT_VOICE_EN_MALE_CFG
    else:
        gender = int(config_json.get('voice_gender', 0))
        voice_cfg = None
        if gender % 2 == 0:
            voice_cfg = SUPPORT_VOICE_FEMALE_CFG
        else:
            voice_cfg = SUPPORT_VOICE_MALE_CFG

    voice_list = list(voice_cfg.keys())
    support_voice_count = len(voice_list)

    voice_idx = int(config_json.get('voice_idx', 0)) % support_voice_count
    config_json['model'] = voice_list[voice_idx]
    voice_cfg = voice_cfg[config_json['model']]

    config_json['sample_rate'] = voice_cfg.get('sample_rate', 48000)
    config_json['rate'] = voice_cfg.get('rate', 1)
    config_json['pitch'] = voice_cfg.get('pitch', 1)
    config_json['volume'] = voice_cfg.get('volume', 100)
    config_json['format'] = file_format
    if VERBOSE_LOG:
        logger.info("Choose voice info: {c}".format(c=config_json))

    result = None
    result = SpeechSynthesizer.call(text=prompt,
                                    model = config_json.get('model', "sambert-zhiwei-v1"),
                                    format = config_json.get('format', "mp3"),
                                    sample_rate = config_json.get('sample_rate', 16000),
                                    rate = config_json.get('rate', 1.0),
                                    pitch = config_json.get('pitch', 1.0),
                                    volume = config_json.get('volume', 50),
                                    word_timestamp_enabled=False,
                                    phoneme_timestamp_enabled=False)

    if result.get_audio_data() is not None:
        with open(save_file, 'wb') as f:
            f.write(result.get_audio_data())
        ok = True
        answer = save_file
        desc = "Save audio file {f} for text: {t}!".format(f=save_file, t=prompt)
        return {'ok': ok, 'answer': answer, 'desc': desc}
    else:
        ok = False
        answer = "文本转语音失败"
        desc = 'testSamBert get ali api response: {s}'.format(s=result)
        logger.error(desc)
        return {'ok': ok, 'answer': answer, 'desc': desc}


"""
Sambert语音合成模型，官方默认提供以下模型可被调用：

说明

默认采样率代表当前模型的最佳采样率，缺省条件下默认按照该采样率输出，同时支持降采样或升采样。如知妙音色，默认采样率16kHz，使用时可以降采样到8kHz，但升采样到48kHz时不会有额外效果提升。

音色           model参数               特色         语言      默认采样率(Hz) 更新日期

知厨           sambert-zhichu-v1       舌尖男声     中文+英文 48k            2023.6.20

知薇           sambert-zhiwei-v1       萝莉女声     中文+英文 48k            2023.6.20

知祥           sambert-zhixiang-v1     磁性男声     中文+英文 48k            2023.6.20

知德           sambert-zhide-v1        新闻男声     中文+英文 48k            2023.6.20

知佳           sambert-zhijia-v1       标准女声     中文+英文 48k            2023.6.20

知楠           sambert-zhinan-v1       广告男声     中文+英文 48k            2023.6.20

知琪           sambert-zhiqi-v1        温柔女声     中文+英文 48k            2023.6.20

知倩           sambert-zhiqian-v1      资讯女声     中文+英文 48k            2023.6.20

知茹           sambert-zhiru-v1        新闻女声     中文+英文 48k            2023.6.20

知妙（多情感） sambert-zhimiao-emo-v1  多种情感女声 中文+英文 16k            2023.6.20

知达           sambert-zhida-v1        标准男声     中文+英文 16k            2023.6.20

知飞           sambert-zhifei-v1       激昂解说     中文+英文 16k            2023.6.20

知柜           sambert-zhigui-v1       直播女声     中文+英文 16k            2023.6.20

知浩           sambert-zhihao-v1       咨询男声     中文+英文 16k            2023.6.20

知婧           sambert-zhijing-v1      严厉女声     中文+英文 16k            2023.6.20

知伦           sambert-zhilun-v1       悬疑解说     中文+英文 16k            2023.6.20

知猫           sambert-zhimao-v1       直播女声     中文+英文 16k            2023.6.20

知茗           sambert-zhiming-v1      诙谐男声     中文+英文 16k            2023.6.20

知墨           sambert-zhimo-v1        情感男声     中文+英文 16k            2023.6.20

知娜           sambert-zhina-v1        浙普女声     中文+英文 16k            2023.6.20

知树           sambert-zhishu-v1       资讯男声     中文+英文 16k            2023.6.20

知硕           sambert-zhishuo-v1      自然男声     中文+英文 16k            2023.6.20

知莎           sambert-zhistella-v1    知性女声     中文+英文 16k            2023.6.20

知婷           sambert-zhiting-v1      电台女声     中文+英文 16k            2023.6.20

知笑           sambert-zhixiao-v1      资讯女声     中文+英文 16k            2023.6.20

知雅           sambert-zhiya-v1        严厉女声     中文+英文 16k            2023.6.20

知晔           sambert-zhiye-v1        青年男声     中文+英文 16k            2023.6.20

知颖           sambert-zhiying-v1      软萌童声     中文+英文 16k            2023.6.20

知媛           sambert-zhiyuan-v1      知心姐姐     中文+英文 16k            2023.6.20

知悦           sambert-zhiyue-v1       温柔女声     中文+英文 16k            2023.6.20

Camila         sambert-camila-v1       西班牙语女声 西班牙语  16k            2023.6.20

Perla          sambert-perla-v1        意大利语女声 意大利语  16k            2023.6.20

Indah          sambert-indah-v1        印尼语女声   印尼语    16k            2023.6.20

Clara          sambert-clara-v1        法语女声     法语      16k            2023.6.20

Hanna          sambert-hanna-v1        德语女声     德语      16k            2023.6.20

Beth           sambert-beth-v1         咨询女声     美式英文  16k            2023.6.20

Betty          sambert-betty-v1        客服女声     美式英文  16k            2023.6.20

Cally          sambert-cally-v1        自然女声     美式英文  16k            2023.6.20

Cindy          sambert-cindy-v1        对话女声     美式英文  16k            2023.6.20

Eva            sambert-eva-v1          陪伴女声     美式英文  16k            2023.6.20

Donna          sambert-donna-v1        教育女声     美式英文  16k            2023.6.20

Brian          sambert-brian-v1        客服男声     美式英文  16k            2023.6.20

Waan           sambert-waan-v1         泰语女声     泰语      16k            2023.6.20
"""

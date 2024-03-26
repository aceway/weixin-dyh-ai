#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: ./ai/aiType.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月28日 星期三 09时29分19秒
#  Description: ...
# 
########################################################################
# 次处的定义需要和数据库中录入的tag保持统一
TXT2TXT = "txt2txt"
TXT2IMG = "txt2img"
TXT2CODE = "txt2code"
TXT2VIDEO   = "txt2video"

IMG2TXT = "img2txt"
IMG2IMG = "img2img"
IMG2VIDEO   = "img2video"

VIDEO2TXT = "video2txt"
VIDEO2IMG = "video2img"
VIDEO2VIDEO   = "video2video"

TXT2VOICE = "txt2voice"
VOICE2TXT = "voice2txt"

PDF2TXT = "pdf2txt"

SUPPORT_IMG_EXT = [
    'png',
    'jpeg',
    'jpg',
    'bmp',
    'gif',
]

SUPPORT_VOICE_EXT = [
    'amr',
    'mp3',
    'mp4',
    'mov',
    'mkv',
    'mpeg',
    'wav',
    'wma',
    'wmv',
]

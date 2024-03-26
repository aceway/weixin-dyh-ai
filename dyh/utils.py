#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import os
import sys
import time
import hashlib
import requests
import threading
from datetime import timedelta
from django.utils import timezone

from dyh import settings

from dyh.settings import DOWNLOAD_FILE_PATH
from dyh.settings import RSP_SUPPORT_IMAGES_EXT_NAME

def got_str_md5(str_data):
    md5 = hashlib.md5()
    if isinstance(str_data, bytes):
        md5.update(str_data)
    else:
        md5.update(str_data.encode('utf-8'))
    return md5.hexdigest()

def extract_pdf_link_from(text):
    '''
    *从一个字符串中，判断提取 图片链接，及其类型*

    - Args:
        - text: 文本

    - Return:
        - 成功 (url, type), 失败返回, (None, None)
    '''
    txt = text.strip().lower()
    ln = len(txt)
    if ln > 13 and (txt.startswith("http://") or txt.startswith("https://")):
        test_url = txt.split(" ")[0]
        test_len = len(test_url)
        if test_len != len(text): return None, None

        for ext in ["pdf", "PDF", "Pdf"]:
            if test_url.endswith(ext):
                return text.split(" ")[0], ext

            pos = test_url.find(ext)
            if pos < 10: continue

            next_flag_pos = pos + len(ext)
            if next_flag_pos < test_len and test_url[next_flag_pos] in ("?", "&"):
                return text.split(" ")[0], ext
    return None, None

def extract_img_link_from(text):
    '''
    *从一个字符串中，判断提取 图片链接，及其类型*

    - Args:
        - text: 文本

    - Return:
        - 成功 (url, type), 失败返回, (None, None)
    '''
    txt = text.strip().lower()
    ln = len(txt)
    if ln > 13 and (txt.startswith("http://") or txt.startswith("https://")):
        test_url = txt.split(" ")[0]
        test_len = len(test_url)
        if test_len != len(text): return None, None

        for ext in RSP_SUPPORT_IMAGES_EXT_NAME:
            pos = test_url.find(ext)
            if pos < 10: continue

            next_flag_pos = pos + len(ext)
            if next_flag_pos < test_len and test_url[next_flag_pos] in ("?", "&"):
                return text.split(" ")[0], ext
    return None, None

def download_media_file(url, sub_dir, img_format):
    img_path = os.path.join(DOWNLOAD_FILE_PATH, sub_dir)
    now = timezone.now()
    local_time = timezone.localtime(now)
    str_time = local_time.strftime('%Y-%m-%d')
    prompt_md5 = got_str_md5(url)
    fname = "{s}-{m}.{f}".format(s=str_time, m=prompt_md5, f=img_format.strip("."))
    save_file = os.path.join(img_path, fname)
    if os.path.isfile(save_file):
        return save_file

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
    }
    #response = requests.get(url)
    #response = requests.get(url, headers=headers)
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        settings.force_mkdir(img_path)
        with open(save_file, 'wb') as wf:
            # wf.write(response.content)
            for chunk in response.iter_content(chunk_size=4096):
                wf.write(chunk)
            logger.info("Image downloaded and saved successfully: {u} ---> {f}".format(u=url, f=save_file))
            return save_file

        logger.error("Failed to download image: {u}.".format(u=url))
        return None
    else:
        logger.error("Failed to download image. Status code: {s}, url:{u}".format(s=response.status_code, u=url))
        return None

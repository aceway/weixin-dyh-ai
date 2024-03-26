#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: utils.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月28日 星期三 09时01分13秒
#  Description: ...
#
# 问答好坏的因子： AI商，AI模型，prompt-model类型匹配, model参数
#
# 从 问题到答案 的路径:
# 用户不关心模型，不关心KEY, 无需理解模型，KEY的概念
# 只管用，只关心结果的好坏
#
# 通过 KEY 来把控答过程中的模型的第一层次选择；
# 通过用户和KEY的绑定关系来把控这个层次 问答的好坏(好模型与坏模型)
#
## 第一条路径(采用)
### 付费用户的路径:
#### prompt -> KEY池(可用性过滤) -> 所属Vender -> Vender下过滤出Model池
#           -> 为prompt匹配最优model ->  模型池(活动模型+个人自选模型) -> API 调用 -> answer
### 非付费用户的路径:
#### prompt -> KEY池(可用性过滤) -> 所属Vender -> Vender下过滤出Model池
#           -> 为prompt匹配最优model ->  模型池(活动模型) -> API 调用 -> answer
#
## 第二条路径
### 付费用户的路径:
#### prompt -> 个人自选模型+活动模型 -> 模型池 -> 所属Vender -> Vender下KEY可用性过滤出Model池
#           -> 为prompt匹配最优model ->  API 调用 -> answer
### 非付费用户的路径:
#### prompt -> 活动模型 -> 模型池 -> 所属Vender -> Vender下KEY可用性过滤出Model池
#           -> 为prompt匹配最优model ->  API 调用 -> answer
# 
########################################################################
import sys
import json
import time
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import datetime
import threading
from datetime import timedelta

from django.utils import timezone
from django.db.models import F
from django.db.models import Q

from dyh.utils import got_str_md5
from dyh.settings import SAVE_MAX_LEN
from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import MSG_TYPE_TAG_IMAGE
from dyh.settings import MSG_TYPE_TAG_VOICE
from dyh.settings import MSG_TYPE_TAG_CODE

from dyh.settings import AI_REM_HIS_REQ_LEN
from dyh.settings import AI_REM_HIS_RSP_LEN
from dyh.settings import AI_REM_HIS_LINES
from dyh.settings import TOP_PROMPT_FOR_AI

from dyh.msg_pro.models import WXUserMsgText

from dyh.dyh_mgr.utils import try_upload_img_from_url

#from dyh.msg_pro.models import WXUser
from dyh.ai import aiType
from dyh.ai import aiAgent
from dyh.ai.models import AIModel
from dyh.ai.models import AICfgBaseModel
from dyh.ai.models import DyhAIConfig
from dyh.ai.models import WXAIConfig
from dyh.ai.models import ActiveAIConfig
from dyh.ai.models import get_all_available_models

AI_NO_ANSSER = "Sorry, I have no idea about it."

def async_send_requst_to_ai(wxMsg, specail_model_type=None):
    prms=(wxMsg, specail_model_type)
    threading.Thread(target=sync_send_req2ai, args=prms).start()

def sync_send_req2ai(wxMsg, replace_content=None, specail_model_type=None, auto_update_rsp=True, ext_format=None):
    result = {'ok': False, 'answer': "", 'desc': "wait to process"}
    wx_user = wxMsg.wx_user
    msg_id = wxMsg.msg_id
    if replace_content:
        msg_content = replace_content
    else:
        msg_content = wxMsg.content

    ok, answer, desc = False, "wait", "no answer now"
    ai_cfgs_in_db = get_all_available_models(wx_user)
    if VERBOSE_LOG:
        for k, v in ai_cfgs_in_db.items():
            logger.info("\t[BackThread]Got model configed info [{k}] : {v}".format(k=k, v=v))

    if isinstance(ai_cfgs_in_db, dict) and len(ai_cfgs_in_db) > 0:
        pass
    else:
        tip = "[BackThread]sync_send_req2ai but ai cfgs [{c}] error.".format(c=ai_cfgs_in_db)
        logger.error(tip)
        result['ok'] = False
        result['answer'] = "no ai key config for U"
        result['desc'] = tip
        return result

    model, ai_cfg_in_db = _choose_model_config(ai_cfgs_in_db, msg_content, specail_model_type=specail_model_type)
    if model is None or ai_cfg_in_db is None:
        tip = "[BackThread]sync_send_req2ai but choosed model failed for content [{c}] error."\
            .format(c=msg_content)
        result['ok'] = False
        result['answer'] = "no ai model config for U"
        result['desc'] = tip
        return result
    logger.info("[BackThread]Choosed model [{m}] for content [{c}] ok.".format(m=model, c=msg_content))

    cfg_json = {}
    json_str = model.config_json
    if len(json_str.strip()) > 0:
        try:
            cfg_json = json.loads(json_str)
            cfg_json['user'] = got_str_md5(wx_user.wx_openid)
        except Exception as e:
            logger.error("[BackThread]WXUser: {u}, load ai config: {c} but parse json error:{e}".\
                format(u=wx_user,  c=json_str, e=e))
            cfg_json = {}
    else:
        cfg_json = {}

    if model.the_type.tag == aiType.TXT2TXT:
        _pack_old_msg_context(wxMsg, model, config_json = cfg_json)

    prompts = _pack_custom_prompt(wxMsg, model, config_json = cfg_json)
    if isinstance(cfg_json.get('sys_prompt', None), list):
        cfg_json['sys_prompt'] += prompts
    else:
        cfg_json['sys_prompt'] = prompts

    if wxMsg.wx_user.prompt and wxMsg.wx_user.prompt.strip():
        cfg_json['pri_prompt'] = wxMsg.wx_user.prompt.strip()

    if model.the_type.tag == aiType.TXT2VOICE:
        cfg_json['voice_lang'] = wx_user.voice_lang
        cfg_json['voice_idx'] = wxMsg.wx_user.voice_idx
        cfg_json['voice_gender'] = wx_user.voice_gender
    elif model.the_type.tag == aiType.PDF2TXT:
        cfg_json['plugins'] = {'pdf_extracter': {}}
        if  wxMsg.wx_user.pdf_prompt and wxMsg.wx_user.pdf_prompt.strip():
            cfg_json['pdf_prompt'] = wxMsg.wx_user.pdf_prompt.strip()
    elif model.the_type.tag == aiType.IMG2TXT:
        if  wxMsg.wx_user.img_prompt and wxMsg.wx_user.img_prompt.strip():
            cfg_json['img_prompt'] = wxMsg.wx_user.img_prompt.strip()

    if len(model.URL.strip()) > 0:
        cfg_json['url'] = model.URL.strip()
    if ext_format:
        cfg_json['format'] = ext_format

    uid_md5 = got_str_md5('{i}'.format(i=wx_user.wx_openid))
    ai_result = aiAgent.chatWithAI(msg_content, uid_md5, model, key=ai_cfg_in_db.KEY, config_json=cfg_json)
    ok = ai_result['ok']
    answer = ai_result['answer']
    desc = ai_result['desc']
    if isinstance(answer, dict):
        if VERBOSE_LOG: logger.info("Got json response.... OK")
        wxMsg.wx_user.change_settings(answer)
        answer = answer.get('answer', '{a}'.format(a=answer))
        if isinstance(answer, dict):
            if 'description' in answer:
                answer = answer['description']
            else:
                answer = '{a}'.format(a=answer)
        else:
            answer = '{a}'.format(a=answer)

    if ok and specail_model_type and specail_model_type in (aiType.VOICE2TXT):
        logger.info("[BackThread]specail_model_type [{t}] result: {o}, [{a}], {d}"\
            .format(t=specail_model_type, o=ok, a=answer, d=desc))

    if len(answer) == 0 and specail_model_type != aiType.VOICE2TXT:
        answer = AI_NO_ANSSER
    elif answer != AI_NO_ANSSER:
        logger.debug("[BackThread]For WXUser {u} question({i}) got resp len {l}, bytes size:{s} from AI: {a}"\
            .format(u=wx_user, i=msg_id, a=answer[:3] + "..." + answer[-3:], l=len(answer), s=sys.getsizeof(answer)))
    else:
        if VERBOSE_LOG:
            logger.info("[BackThread]For WXUser {u} question({i}) got resp from AI: {a}"\
                .format(u=wx_user, i=msg_id, a=answer))

    model.used_times += 1
    model.the_type.used_times += 1
    model.the_type.save()
    model.save()
    ai_cfg_in_db.used_times += 1
    ai_cfg_in_db.last_used_time = timezone.now()
    if ok:
        ai_cfg_in_db.ok_times += 1
        answer = _try_remove_dup_content(answer)
        if sys.getsizeof(answer) > SAVE_MAX_LEN:
            answer = answer[:SAVE_MAX_LEN] + "......"
        if auto_update_rsp:
            wxMsg.finish_background_process_with_response(answer)
        wxMsg.remark = "{d}".format(d=desc)[:1024]
    else:
        ai_cfg_in_db.failed_times += 1
        wxMsg.remark = "{a}, {d}".format(a=answer, d=desc)[:1024]
    ai_cfg_in_db.save()

    if ok and model.the_type.tag == aiType.TXT2IMG:
        wxMsg.rsp_fmt = MSG_TYPE_TAG_IMAGE
        media_id, url = try_upload_img_from_url(wxMsg.wx_user, wxMsg.wx_user.wx_dyh, answer)
        if media_id:
            wxMsg.remark = answer[:1024]
            answer = media_id
            wxMsg.response = answer
        elif url:
            wxMsg.remark = answer[:1024]
            answer = url
            wxMsg.response = answer

    elif ok and model.the_type.tag == aiType.TXT2CODE:
        wxMsg.rsp_fmt = MSG_TYPE_TAG_CODE
    elif ok and model.the_type.tag == aiType.TXT2VOICE:
        wxMsg.rsp_fmt = MSG_TYPE_TAG_VOICE
    else:
        wxMsg.rsp_fmt = MSG_TYPE_TAG_TEXT
    wxMsg.wx_user.use_ai_times += 1
    wxMsg.wx_user.save()

    wxMsg.model_id = '{i}:{t}:{mt}'.format(i=model.id, t=model.the_type.tag, mt=model.tag)
    if auto_update_rsp:
        wxMsg.save()

    result['ok'] = ok
    result['answer'] = answer
    result['desc'] = desc
    for k, v in ai_result.items():
        if k not in result:
            result[k] = v
    return result

def _choose_model_config(ai_cfgs_in_db, current_content, specail_model_type=None):
    '''
        return model, and the WXAIConfig or ActiveAIConfig config object
    '''
    model_type_tag = None
    target_cfg = None
    lq = current_content.lower()
    while True:
        if specail_model_type in (aiType.TXT2VOICE, aiType.VOICE2TXT, aiType.PDF2TXT):
            models = ai_cfgs_in_db.get(specail_model_type, None)
            if models and len(models) > 0:
                model_type_tag = specail_model_type
                target_cfg = models[0]
                logger.info("Try find specail_model_type [{t}] model [{m}] ok for {p}"\
                    .format(t=specail_model_type, m=target_cfg, p=current_content))
                break
            logger.info("Try find specail_model_type [{t}] model [{m}] failed for {p}"\
                .format(t=specail_model_type, m=target_cfg, p=current_content))

        for ext in aiType.SUPPORT_IMG_EXT:
            if ext in lq:
                models = ai_cfgs_in_db.get(aiType.IMG2TXT, None)
                if models and len(models) > 0:
                    model_type_tag = aiType.IMG2TXT
                    target_cfg = models[0]
                    logger.info("Try find [{t}] model {m} ok for {p}"\
                        .format(t=aiType.IMG2TXT, m=target_cfg, p=current_content))
                    break
                logger.warn("Try find [{t}] model failed for {p}"\
                    .format(t=aiType.IMG2TXT, p=current_content))

        for ext in aiType.SUPPORT_VOICE_EXT:
            if ext in lq:
                models = ai_cfgs_in_db.get(aiType.VOICE2TXT, None)
                if models and len(models) > 0:
                    model_type_tag = aiType.VOICE2TXT
                    target_cfg = models[0]
                    logger.info("Try find [{t}] model {m} ok for {p}"\
                        .format(t=aiType.VOICE2TXT, m=target_cfg, p=current_content))
                    break
                logger.warn("Try find [{t}] model failed for {p}"\
                    .format(t=aiType.VOICE2TXT, p=current_content))

        if model_type_tag and target_cfg:
            break

        if _is_want_draw(current_content):
            models = ai_cfgs_in_db.get(aiType.TXT2IMG, None)
            if models and len(models) > 0:
                model_type_tag = aiType.TXT2IMG
                target_cfg = models[0]
                logger.info("Try find [{t}] ok for {p}".format(t=aiType.TXT2IMG, p=current_content))
                break
            logger.warn("Try find [{t}] failed for {p}".format(t=aiType.TXT2IMG, p=current_content))
        elif _is_want_write_code(current_content):
            models = ai_cfgs_in_db.get(aiType.TXT2CODE, None)
            if models and len(models) > 0:
                model_type_tag = aiType.TXT2CODE
                target_cfg = models[0]
                logger.info("Try find [{t}] ok for {p}".format(t=aiType.TXT2CODE, p=current_content))
                break
            logger.warn("Try find {t} failed for {p}".format(t=aiType.TXT2CODE, p=current_content))

        models = ai_cfgs_in_db.get(aiType.TXT2TXT, None)
        if models and len(models) > 0:
            model_type_tag = aiType.TXT2TXT
            target_cfg = models[0]
            break

        model_type_tag = None
        target_cfg = None
        break
        # END OF WHILE TRUE

    if model_type_tag and isinstance(target_cfg, AICfgBaseModel):
        for model in target_cfg.enable_models.all():
            if model.the_type.tag == model_type_tag:
                return model, target_cfg
    return None, None

def _is_want_draw(content):
    lc = content.lower()
    return content.startswith("画") \
       or content.startswith("绘") \
       or 0 <= content.find("画一")  \
       or 0 <= content.find("画几")  \
       or ( 0 <= content.find("画") < content.find("只") ) \
       or ( 0 <= content.find("画") < content.find("个") ) \
       or ( 0 <= content.find("画") < content.find("张") ) \
       or ( 0 <= content.find("设计") < content.find("商标") ) \
       or ( 0 <= content.find("设计") < lc.find("logo") ) \
       or ( 0 <= content.find("画") < content.find("幅") ) \
       or ( 0 <= content.find("绘") < content.find("张") ) \
       or ( 0 <= content.find("绘") < content.find("幅") ) \
       or ( 0 <= content.find("生成") < content.find("幅") ) \
       or ( 0 <= content.find("生成") < content.find("张") ) \
       or ( 0 <= content.find("画") < content.find("商标") ) \
       or ( 0 <= content.find("画") < lc.find("logo") ) \
       or ( 0 <= content.find("设计") < content.find("商标") ) \
       or ( 0 <= content.find("设计") < lc.find("logo") ) \
       or ( 0 <= content.find("生成") < content.find("商标") ) \
       or ( 0 <= content.find("生成") < lc.find("logo") ) \
       or lc.startswith("paint") \
       or lc.startswith("draw") \
       or (( 0 <= lc.find("make") or 0 <= lc.find("generate") or 0 <= lc.find("create") ) \
           and (lc.find("image") > 4 or lc.find("photo") > 4 or lc.find("picture") > 4))

def _is_want_write_code(content):
    lc = content.lower()
    return ( 0 <= content.find("写") < content.find("代码") ) \
       or ( 0 <= content.find("写") < content.find("程序") ) \
       or ( 0 <= content.find("写") < content.find("函数") ) \
       or ( 0 <= content.find("写") < content.find("类") ) \
       or ( 0 <= content.find("生成") < content.find("代码") ) \
       or ( 0 <= content.find("生成") < content.find("程序") ) \
       or ( 0 <= content.find("生成") < content.find("函数") ) \
       or ( 0 <= content.find("生成") < content.find("类") ) \
       or ( 0 <= content.find("实现") < content.find("代码") ) \
       or ( 0 <= content.find("实现") < content.find("程序") ) \
       or ( 0 <= content.find("实现") < content.find("函数") ) \
       or ( 0 <= content.find("实现") < content.find("类") ) \
       or (( 0 <= lc.find("make") or 0 <= lc.find("generate") or 0 <= lc.find("create") )
            and (lc.find("code") > 4 or lc.find("program") > 4 or lc.find("function") > 4 or lc.find("class") > 4))

def _try_remove_dup_content(content):
    seperators =["，", "、", "。"]
    for sep in seperators:
        infos = content.split(sep)
        result = []
        idx = 0
        for data in infos:
            if idx == 0:
                result.append(data)
                idx +=  1
                continue
            elif result[idx - 1] == data:
                continue
            elif idx > 1 and result[idx - 2] == data:
                continue
            elif idx > 2 and result[idx - 3] == data:
                continue
            elif idx > 3 and result[idx - 4] == data:
                continue
            elif idx > 4 and result[idx - 5] == data:
                continue
            elif idx > 5 and result[idx - 6] == data:
                continue

            result.append(data)
            idx +=  1
        content = sep.join(result)

    return content

def _pack_custom_prompt(wxMsg, the_model, config_json=None):
    prompts = []
    if the_model.the_type.tag in (aiType.TXT2TXT, aiType.TXT2IMG):
        if TOP_PROMPT_FOR_AI:
            p = TOP_PROMPT_FOR_AI.strip()
            if len(p) > 3: prompts.append(p)

        if wxMsg.wx_user.wx_dyh.prompt and wxMsg.wx_user.wx_dyh.prompt.strip():
            p = wxMsg.wx_user.wx_dyh.prompt.strip()
            if len(p) > 3: prompts.append(p)

        if the_model.prompt and the_model.prompt.strip():
            p = the_model.prompt.strip()
            if len(p) > 3: prompts.append(p)

    if len(config_json.get('prompt', "").strip()) > 0:
        prompts.append(config_json['prompt'].strip())
    return prompts

def _pack_old_msg_context(wxMsg, the_model, config_json=None):
    # get last 3 query and answer of current user
    # TODO 以 wxMsg.id 前后范围构建上下文
    recent_seconds = 60 * 60
    wx_user = wxMsg.wx_user
    pre_chated = WXUserMsgText.objects.filter(wx_user=wx_user, with_ai=True, \
        msg_type = MSG_TYPE_TAG_TEXT, rsp_fmt = MSG_TYPE_TAG_TEXT,
        msg_time__gt=timezone.now() - timedelta(seconds=recent_seconds)).order_by('-id')[:AI_REM_HIS_LINES]

    logger.info("[BackThread]Got WXUser {u} pre chat with ai record count:{c}, data: {p}..."\
        .format(u=wx_user, c= pre_chated.count(),  p= pre_chated[:1]))

    if pre_chated.count () > 0 and isinstance(config_json, dict):
        sys_msg_tips = []
        # ali QW 不支持 role: system
        #sys_msg_tips.append({'role': "assistant", 'content': "You are a helpful assistant."})
        for pc in pre_chated:
            if 'Invalid' in pc.response or len(pc.response.strip()) < 2:
                continue

            if the_model.tag and (the_model.tag in pc.content or the_model.tag in pc.response):
                continue

            if len(pc.response) < 200:
                sys_msg_tips.append({ 'role':'assistant', 'content': pc.response })
                sys_msg_tips.append({ 'role':'user', 'content': pc.content[:AI_REM_HIS_REQ_LEN] })
            elif len(pc.response) < 300:
                sys_msg_tips.append({ 'role':'assistant', 'content': pc.response[:AI_REM_HIS_RSP_LEN] + "..." + pc.response[-AI_REM_HIS_RSP_LEN:] })
                sys_msg_tips.append({ 'role':'user', 'content': pc.content[:AI_REM_HIS_REQ_LEN] })
            else:
                sys_msg_tips.append({ 'role':'assistant', 'content': pc.response[:AI_REM_HIS_RSP_LEN] + "..." + pc.response[-AI_REM_HIS_RSP_LEN:] })
                sys_msg_tips.append({ 'role':'user', 'content': pc.content[:AI_REM_HIS_REQ_LEN] })

        sys_msg_tips.reverse()
        config_json['messages'] = sys_msg_tips

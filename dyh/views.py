# -*- coding:utf-8 -*-
import sys
import time
import hashlib
import threading

import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import xml.etree.cElementTree as ET

from django.contrib import admin

from django.utils import timezone
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from dyh.settings import MSG_RECENT_MINUTES_FOR_HELP

from dyh.settings import CATCH_EXCEPTION

from dyh.settings import WX_ERROR_DESC
from dyh.settings import WX_MAX_REPPOST_TIMES
from dyh.settings import WX_ONCE_TIMEOUT_SEC
from dyh.settings import WX_TOTAL_TIMEOUT_SEC

from dyh.settings import WX_MSG_TYPE_KEYFIELD
from dyh.settings import WX_FIXED_FIELD_TAGS
from dyh.settings import WX_MSG_TYPE_MAP_EXTRA_DATA
from dyh.settings import WX_EVENT_TYPE_MAP_EXTRA_DATA

from dyh.settings import HELP_CMD_INPUT_ERROR
from dyh.settings import HELP_CMD_INFO
from dyh.settings import HELP_CMD_REPEAT
from dyh.settings import HELP_CMD_CONTINUE

from dyh.settings import MSG_TYPE_TAG_TEXT
from dyh.settings import MSG_TYPE_TAG_VOICE
from dyh.settings import EVENT_TYPE_TAG_SUBSCRIBE

from dyh.settings import MSG_TYPE_TAG_EVENT
from dyh.settings import EVENT_TYPE_TAG_MENU

from dyh.utils import got_str_md5

from dyh.dyh_mgr.models import WXUser
from dyh.dyh_mgr.models import WXDingYueHao
from dyh.dyh_mgr.utils import get_wx_user_info
from dyh.dyh_mgr.utils import get_wx_dyh_info
from dyh.dyh_mgr.utils import get_dyh_by_url_factor

from dyh.msg_pro.views import pre_process_message
from dyh.msg_pro.views import BackgroundWorker
from dyh.msg_pro.views import post_process_message
from dyh.msg_pro.utils import make_encryp_rsp_with_msg_obj
from dyh.msg_pro.utils import make_encryp_rsp_for_cmd_rsp
from dyh.msg_pro.utils import process_as_cmd
from dyh.msg_pro.utils import get_support_cmd_list
from dyh.msg_pro.utils import get_support_sys_cmd_list
from dyh.msg_pro.BaseModel import WXUserMsgBaseModel


from dyh.weixin_sdk.WXBizMsgCrypt import WXBizMsgCrypt

@csrf_exempt
def home(request):
    #return default(request)
    raise Http404

@csrf_exempt
def default(request, url_factor=""):
    '''
    *处理微信过来信息数据的总入口, 包括验证 和 通过验证后的通信。*
    *微信GET方法验证, POST方法发送通信数据*

    - Args:
        - None

    - Return:
        - HttpResponse 对象
    '''
    dyh = get_dyh_by_url_factor(url_factor)
    if dyh is None:
        logger.error('get_dyh_by_url_factor(url_factor:{v}) failed.'.format(v=url_factor))
        raise Http404

    if request.method == "GET":
        signature_info = {}
        signature_info['url_factor'] = url_factor
        strEcho = _verify_dyh_signature(request, dyh, signature_info)
        if strEcho is None:
            logger.error('process WX HTTP GET request failed, request:{r}, dyh:{v}, signature_info:{s}'\
                .format(r=request, v=dyh, s=signature_info))
            raise Http404

        return HttpResponse(strEcho)
    elif request.method == "POST":
        signature_info = _verify_msg_signature(request, dyh)
        if signature_info is None:
            logger.error('process WX POST request _verify_msg_signature failed, dyh:{v}, signature_info:{s}'\
                .format(v=dyh, s=signature_info))
            raise Http404

        signature_info['url_factor'] = url_factor
        retdata = _process_weixin_post_data(request, dyh, signature_info)
        if retdata is None:
            logger.warn('process WX POST request _process_weixin_post_data no resp, dyh:{v}'\
                .format(v=dyh))
            raise Http404

        return HttpResponse(retdata)
    else:
        logger.error('process WX HTTP method wrong, must be POST or GET, but now is:' + request.method)
        raise Http404

def i18n_javascript(request):
    return admin.site.i18n_javascript(request)

def _verify_msg_signature(request, dyh):
    '''
    *检测订阅号发送过来的消息是否合法*
    *微信POST方法发送通信消息, 但是验证数据仍然放在 request.GET中 --- 带在 URL 上.*
    - remark: 订阅号和企业号在验证消息是否合法算法上有小区别, 但是返回给微信服务器的加密方法一样

    - Args:
        - request: django框架传入的HttpRequest 对象

    - Return:
        - 成功返回True, 失败返回False
    '''
    try:
        signature_info = {}
        if 'signature' in request.GET and 'timestamp' in request.GET and 'nonce' in request.GET:
            nonce     = request.GET['nonce']
            signature = request.GET['signature']
            timestamp = request.GET['timestamp']
            if 'msg_signature' in request.GET:
                signature_info['msg_signature'] = request.GET['msg_signature']

            signature_info['nonce'] = nonce
            signature_info['signature'] = signature
            signature_info['timestamp'] = timestamp

            sortlist = [dyh.token, timestamp, nonce]
            sortlist.sort()
            data = "".join(sortlist)

            sha = hashlib.sha1()
            sha.update(data.encode('utf-8'))
            if signature == sha.hexdigest():
                return signature_info
            else:
                return None
        else:
            logger.error('_verify_msg_signature failed: signature, timestamp or nonce missed.')
            return None
    except CATCH_EXCEPTION as e:
        logger.error('_verify_msg_signature exception: {e}.'.format(e=e))
        print(e)
        return None

def _verify_dyh_signature(request, dyh, signature_info):
    '''
    *验证订阅号(dyh)的接口*
    *微信GET方法验证*

    - Args:
        - request: django框架传入的HttpRequest 对象

    - Return:
        - 成功返回微信发过来的 echostr字符串, 失败返回None
    '''
    try:
        if 'signature' in request.GET and 'timestamp' in request.GET \
          and 'nonce' in request.GET and 'echostr' in request.GET:
            nonce     = request.GET['nonce']
            echostr   = request.GET['echostr']
            signature = request.GET['signature']
            timestamp = request.GET['timestamp']

            signature_info['nonce'] = nonce
            signature_info['signature'] = signature
            signature_info['timestamp'] = timestamp

            token = dyh.token

            sortlist = [token, timestamp, nonce]
            sortlist.sort()
            data = "".join(sortlist)

            sha = hashlib.sha1()
            sha.update(data.encode('utf-8'))
            if signature == sha.hexdigest():
                return echostr
            else:
                return None
        else:
            logger.error('_verify_dyh_signature failed: signature, timestamp, nonce or echostr missed.')
            return None
    except CATCH_EXCEPTION as e:
        logger.error('_verify_dyh_signature exception.'.format(e=e))
        print(e)
        return None


def _process_weixin_post_data(request, dyh, signature_info):
    '''
    *处理微信服务器发送过来的加密信息*
    *微信POST方法发送通信消息.*

    - Args:
        - request: django框架传入的HttpRequest 对象

    - Return:
        - 成功 按照微信各种消息格式返回加密的信息, 失败返回None

    请注意：
    ref: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Receiving_standard_messages.html
    关于重试的消息排重，推荐使用msgid排重。
    微信服务器在五秒内收不到响应会断掉连接，并且重新发起请求，总共重试三次。假如服务器无法保证在五秒内处理并回复，可以直接回复空串，微信服务器不会对此作任何处理，并且不会发起重试。详情请见“发送消息-被动回复消息”。
    如果开发者需要对用户消息在5秒内立即做出回应，即使用“发送消息-被动回复消息”接口向用户被动回复消息时，可以在
    严格来说，发送被动响应消息其实并不是一种接口，而是对微信服务器发过来消息的一次回复。

    微信服务器在将用户的消息发给公众号的开发者服务器地址（开发者中心处配置）后，微信服务器在五秒内收不到响应会断掉连接，并且重新发起请求，总共重试三次，如果在调试中，发现用户无法收到响应的消息，可以检查是否消息处理超时。关于重试的消息排重，有msgid的消息推荐使用msgid排重。事件类型消息推荐使用FromUserName + CreateTime 排重。

    如果开发者希望增强安全性，可以在开发者中心处开启消息加密，这样，用户发给公众号的消息以及公众号被动回复用户消息都会继续加密，详见被动回复消息加解密说明。

    假如服务器无法保证在五秒内处理并回复，必须做出下述回复，这样微信服务器才不会对此作任何处理，并且不会发起重试（这种情况下，可以使用客服消息接口进行异步回复），否则，将出现严重的错误提示。详见下面说明：
    1、直接回复success（推荐方式） 2、直接回复空串（指字节长度为0的空字符串，而不是XML结构体中content字段的内容为空）
    一旦遇到以下情况，微信都会在公众号会话中，向用户下发系统提示“该公众号暂时无法提供服务，请稍后再试”：
    1、开发者在5秒内未回复任何内容 2、开发者回复了异常数据，比如JSON数据等
    另外，请注意，回复图片（不支持gif动图）等多媒体消息时需要预先通过素材管理接口上传临时素材到微信服务器，可以使用素材管理中的临时素材，也可以使用永久素材。
    '''
    if 'signature' in request.GET and 'timestamp' in request.GET and 'nonce' in request.GET:
        signature = request.GET['signature']
        timestamp = request.GET['timestamp']
        nonce     = request.GET['nonce']
        signature_info['nonce'] = nonce
        signature_info['signature'] = signature
        signature_info['timestamp'] = timestamp
        if 'msg_signature' in request.GET:
            signature_info['msg_signature'] = request.GET['msg_signature']

        post_data = None
        #受django 框架防CSRF攻击,而禁止直接读取post数据 限制, 而如此获取数据 
        for data in request:
            if post_data is None:
                post_data = data.decode('utf-8')
            else:
                post_data = '{p}{d}'.format(p=post_data, d=data.decode('utf-8'))
        if VERBOSE_LOG:
            logger.info("Got post encrypted data: {d}".format(d=post_data))

        wxcpt =  WXBizMsgCrypt(dyh.token, dyh.aeskey, dyh.dyh_appid)
        ret, decryp_xml = wxcpt.DecryptMsg(post_data, signature, timestamp, nonce)
        if( ret!=0 ):
            desc = str(ret) if int(ret) not in WX_ERROR_DESC else WX_ERROR_DESC[int(ret)]
            logger.error('WXBizMsgCrypt.DecryptMsg failed, error info: ' + desc)
            return None

        if VERBOSE_LOG:
            logger.info('Decrypt msg:' +  decryp_xml)

        xml_tree = ET.fromstring( decryp_xml)
        try:
            rsp = _dispatch_weixin_message(xml_tree, signature_info)
        except CATCH_EXCEPTION as e:
            logging.error("Got _dispatch_weixin_message exception: {e}".format(e=e))
            print(e)
            rsp = None
        return rsp
    else:
        logger.error("Received weixin verify info failed.")
        info = ""
        for k, v in list(request.POST.items()):
            info += "key={k}; value={v}\n".format(k=k, v=v)
        logger.error("Received weixin POST data: {d}".format(d=info))

        info = ""
        for k in request:
            info += "key={k};\n".format(k=k)
        logger.error("Received weixin request data: {d}".format(d=info))

        return None


def _dispatch_weixin_message(xml_tree_data, signature):
    '''
    *对解密出来的微信消息(xml格式)进行解析,回复*

    - Args:
        - xml_tree_data: xml格式的微信消息, 详细参见微信的协议结构

    - Return:
        - 成功 按照微信各种消息格式返回加密的信息, 失败返回None
    注意：
        微信 5 秒超时； 3次重试。
    '''
    cur_rsp = None
    rsp_fmt = MSG_TYPE_TAG_TEXT
    wxMsg = None
    this_start_timestamp = time.time()
    msg_create_time = this_start_timestamp
    the_cmd = None
    common_info = None
    while True:
        # 预处理 - 消息数据初始化，去重
        common_info = _get_msg_common_info(xml_tree_data)
        if common_info is None:
            error_tip = "_dispatch_weixin_message get info from xml_tree_data failed: {c} - {x}"\
                .format(c=common_info, x=xml_tree_data)
            logger.error(error_tip)
            cur_rsp = None
            return None
        else:
            common_info['nonce'] = signature['nonce']
            logger.info("Got weixin msg common info: {m}".format(m=common_info))

        msg_create_time = int(common_info.get('CreateTime', 0)) or this_start_timestamp
        wxMsg, rsp_fmt = pre_process_message(common_info)
        if VERBOSE_LOG:
            logger.info("Common info after pre_process_message: {m}".format(m=common_info))

        # cmd 消息本身不会进存储
        # 处理 - 对重试，超时协调，后台进度协调, 处理后的结果获取
        if isinstance(wxMsg, str) and wxMsg in get_support_cmd_list():
            the_cmd = wxMsg
            cur_rsp, rsp_fmt = process_as_cmd(the_cmd, common_info)
        elif isinstance(wxMsg, WXUserMsgBaseModel):
            if VERBOSE_LOG:
                logger.info("_dispatch_weixin_message inited msg:{m} ".format(m=wxMsg))

            if wxMsg.bk_done:
                if wxMsg.rsp_done:
                    if wxMsg.total_lost_seconds() > 300: # 超过一定时间的再重新回答
                        wxMsg.reset_rsp_offset()
                        cur_rsp, rsp_fmt = post_process_message(wxMsg, common_info)
                    elif wxMsg.msg_type != MSG_TYPE_TAG_VOICE:
                        str_time = wxMsg.rsp_time.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M:%S")
                        cur_rsp = "{m}[{t}]回答过...".format(m=wxMsg.get_manager_tip(), t=str_time)
                else:
                    cur_rsp, rsp_fmt = post_process_message(wxMsg, common_info)
            if cur_rsp: break

            # if wxMsg.wx_notify_times % WX_MAX_REPPOST_TIMES == 1:
            if time.time() - msg_create_time < WX_ONCE_TIMEOUT_SEC:
                #首次消息，转发到后台线程进行任务处理(AI)
                wx_user = wxMsg.wx_user
                user_id = wx_user.id
                with_ai = wx_user.enable_ai or wx_user.always_ai
                msg_md5 = wxMsg.msg_md5
                msg_id = wxMsg.get_msg_id()
                msg_type = wxMsg.get_msg_type()
                event_type = wxMsg.get_event_type()
                prms = (user_id, with_ai, msg_id, msg_type, event_type, msg_md5)
                threading.Thread(target=BackgroundWorker, args=prms).start()
                time.sleep(2)

            cur_rsp, rsp_fmt = post_process_message(wxMsg, common_info)
            if cur_rsp is None:
                # 有时间的话再等待尝试一次
                now = time.time()
                total_lost_sec = int(now - msg_create_time)
                this_lost_sec = int(now - this_start_timestamp)
                rest_sec = WX_ONCE_TIMEOUT_SEC - this_lost_sec
                if total_lost_sec < WX_TOTAL_TIMEOUT_SEC and rest_sec > 3:
                    time.sleep(1)
                    cur_rsp, rsp_fmt = post_process_message(wxMsg, common_info)
        else:
            cur_rsp = None
            rsp_fmt = None
            error_tip = "Recieved message format error, msg obj {m} from common info: {c}."\
                .format(m=wxMsg, c=common_info)
            logger.error(error_tip)

        break # end of while True

    # 结果处理 - 尽快三次内回答, 三次必答 - 超时提示
    wx_user = common_info['UserObj']
    now = time.time()
    total_lost_sec = int(now - msg_create_time)
    encrypted_msg = None
    if common_info.get("MsgType", None) == MSG_TYPE_TAG_EVENT and common_info.get("Event", None) == EVENT_TYPE_TAG_MENU:
        return "" # directly finsih
    elif total_lost_sec >= WX_ONCE_TIMEOUT_SEC * (WX_MAX_REPPOST_TIMES-1) or the_cmd:
        # 三次/时间到， 必须给予回复
        if the_cmd:
            if not cur_rsp:
                if the_cmd == HELP_CMD_INPUT_ERROR:
                    cur_rsp = common_info.get('response', "输入异常")
                elif the_cmd == HELP_CMD_REPEAT:
                    cur_rsp = "没有找到可重复发送的内容({n}分钟内).".format(n=MSG_RECENT_MINUTES_FOR_HELP)
                elif the_cmd == HELP_CMD_CONTINUE:
                    cur_rsp = "没有更多可回复的新内容了({n}分钟内).".format(n=MSG_RECENT_MINUTES_FOR_HELP)
                else:
                    cur_rsp = "内部故障..."
                rsp_fmt = MSG_TYPE_TAG_TEXT
                if isinstance(wxMsg, WXUserMsgBaseModel):
                    cur_rsp = "{t}{r}".format(t=wxMsg.get_manager_tip(), r=cur_rsp)
            encrypted_msg = make_encryp_rsp_for_cmd_rsp(common_info, cur_rsp, rsp_fmt)
        else:
            if not cur_rsp:
                if the_cmd == HELP_CMD_INPUT_ERROR:
                    cur_rsp = common_info.get('response', "输入异常")
                else:
                    cur_rsp = "请稍后发送 .. 重试"
                rsp_fmt = MSG_TYPE_TAG_TEXT
                if isinstance(wxMsg, WXUserMsgBaseModel):
                    cur_rsp = "{t}{r}".format(t=wxMsg.get_manager_tip(), r=cur_rsp)
            encrypted_msg = make_encryp_rsp_with_msg_obj(wxMsg, common_info, cur_rsp, rsp_fmt=rsp_fmt)
        #if True:
        if VERBOSE_LOG:
            logger.info("_dispatch_weixin_message would timeout, total lost sec:{s}, has to rsp for: [{f}] [{m}], [{r}]: {e}."\
                .format(s=total_lost_sec, m=wxMsg, r=cur_rsp, f=rsp_fmt, e=encrypted_msg))
        return encrypted_msg
    else:
        this_lost_sec = int(time.time() - this_start_timestamp)
        rest_sec = WX_ONCE_TIMEOUT_SEC - this_lost_sec
        # 有结果则回复，无则等待
        while True:
            if the_cmd:
                if the_cmd == HELP_CMD_INPUT_ERROR:
                    cur_rsp = common_info.get('response', "输入异常")
                    rsp_fmt = MSG_TYPE_TAG_TEXT
                    if isinstance(wxMsg, WXUserMsgBaseModel):
                        cur_rsp = "{t}{r}".format(t=wxMsg.get_manager_tip(), r=cur_rsp)

                if cur_rsp:
                    encrypted_msg = make_encryp_rsp_for_cmd_rsp(common_info, cur_rsp, rsp_fmt)
                    break
            else:
                if cur_rsp:
                    encrypted_msg = make_encryp_rsp_with_msg_obj(wxMsg, common_info, cur_rsp, rsp_fmt=rsp_fmt)
                    break
            break

        if VERBOSE_LOG:
            logger.info("_dispatch_weixin_message in time, total lost sec:{s}, this lost:{ts}, try to rsp for: [{f}] [{m}], [{r}]: {e}."\
                .format(s=total_lost_sec, ts=this_lost_sec, m=wxMsg, r=cur_rsp, f=rsp_fmt, e=encrypted_msg))
        if encrypted_msg:
            return encrypted_msg
        elif rest_sec >= 0:
            time.sleep(rest_sec+1)

def _get_msg_common_info(xml_tree_data):
    '''
    *提取微信发送消息的共有数据: 发送消息者, 接收消息者, 发送时间, 消息ID*

    - Args:
        - xml_tree_data: xml格式的微信消息, 详细参见微信的协议结构

    - Return:
        - 成功 按照微信消息格式内属性的名称将公用信息打包为字典返回, 失败返回None
          - {
              'ToUserName':to_user, 'FromUserName':from_user,
              'CreateTime':create_time, 'MsgId':msg_id, "MsgType": msg_type
            }
    '''
    if xml_tree_data:
        common_info = {}
        for field in WX_FIXED_FIELD_TAGS:
            value = xml_tree_data.find(field).text.strip()
            if field == WX_MSG_TYPE_KEYFIELD:
                value = value.upper()  # UPPER
            common_info[field] = value

        dyh = get_wx_dyh_info(common_info['ToUserName'])
        if isinstance(dyh, WXDingYueHao):
            common_info['DyhObj'] = dyh
            user = get_wx_user_info(dyh, common_info['FromUserName'])
            if isinstance(user, WXUser):
                common_info['UserObj'] = user
        else:
            common_info['DyhObj'] = None
            common_info['UserObj'] = None

        msg_type = common_info[WX_MSG_TYPE_KEYFIELD]
        if common_info[WX_MSG_TYPE_KEYFIELD] == "EVENT":
            event_type = xml_tree_data.find("Event").text.strip().upper()
            msg_type_cfg = WX_EVENT_TYPE_MAP_EXTRA_DATA.get(event_type, {})
            # print("XXXX", event_type, msg_type_cfg)
        else:
            msg_type_cfg = WX_MSG_TYPE_MAP_EXTRA_DATA.get(msg_type, {})

        fields = msg_type_cfg.get('FIELDS', [])
        for fd in fields:
            dt = xml_tree_data.find(fd)
            value = None
            if dt is not None and hasattr(dt, 'text'):
                value = dt.text
            elif isinstance(dt, dict) and 'text' in dt:
                value = '{t}'.format(t=dt['text'])
            elif dt is not None :
                value = '{d}'.format(d=dt)

            if value is not None:
                if fd == "Event":
                    value = value.upper()
                common_info[fd] = value

        CONTENT_KEY = "CONTENT"
        as_content = msg_type_cfg.get(CONTENT_KEY, None)
        if as_content and CONTENT_KEY not in fields:
            content = xml_tree_data.find(as_content)
            if content is not None and hasattr(content, 'text'):
                common_info["Content"] = content.text.strip()
            elif content is not None:
                common_info["Content"] = '{c}'.format(c=content)

        if as_content and "Content" in common_info:
            content =  common_info["Content"]
            common_info["MsgMd5"] = got_str_md5('{c}'.format(c=content))
        else:
            common_info["MsgMd5"] = "no md5 without [{c}] field".format(c=as_content)

        return common_info
    else:
        logger.error('Error, xml_tree_data:{x}'.format(x=xml_tree_data))
        return None

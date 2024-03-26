#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: api_proxy.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: Sun 23 Nov 2014 01:33:51 PM CST
#  Description: ...
# 
########################################################################
import os
import json
import urllib.request
import urllib.parse
import urllib.error

import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

import requests

from django.utils import timezone

from dyh.dyh_mgr.models import WXDingYueHao

CUSTOMER_SERVICE_COMMON_PRMS ={
    "kf_account" : "open-ai",
    "kf_nick" : "AIer",
    "kf_id" : "1",
    "nickname" : "ai",
    #"password" : "",
    #"media" : "",
}

class WeixinApiMgr(object):
    AppID = None
    AppSecret  = None
    DomainName = None
    AccessToken= None
    ATUpdateTime= None
    def __init__(self, appid=None, appsecret=None, domainname="api.weixin.qq.com"):
        self.AppID = appid
        self.AppSecret = appsecret
        self.DomainName= domainname

    def update_domain(self, domain):
        self.DomainName = domain

    def get_access_token(self):
        cache = None
        while True:
            cache = WXDingYueHao.objects.filter(dyh_appid=self.AppID)
            if cache.count() == 0:
                logger.error("The dyh appid {a} not config in db".format(a=self.AppID))
                return None

            cache = cache[0]
            if len(cache.access_token.strip()) == 0: break

            now_stamp = timezone.now().timestamp()
            last_stamp = cache.at_time.timestamp()
            lost_secs = now_stamp - last_stamp
            if lost_secs < cache.at_seconds:
                self.AccessToken = cache.access_token.strip()
                cache.last_verify_time = timezone.now()
                cache.save()
                if VERBOSE_LOG:
                    logger.info("Got cached token, lost secs: {l} < {a}"\
                        .format(l=lost_secs, a=cache.at_seconds))
                return self.AccessToken

            break


        params = {'appid': self.AppID, 'secret': self.AppSecret, 'grant_type': "client_credential"}
        ret = self.request_weixin_server("/cgi-bin/token", params, method="GET")
        if isinstance(ret, dict) and ret.get('code', None) == 0 and isinstance(ret.get('data', None), dict) \
          and ret['data'].get('access_token', None) and ret['data'].get('expires_in', None):
            self.AccessToken = ret['data']['access_token']
            cache.access_token = self.AccessToken
            cache.at_time = timezone.now()
            cache.at_seconds = ret['data']['expires_in']
            cache.last_verify_time = cache.at_time 
            cache.save()
            if VERBOSE_LOG:
                logger.info("Update cached token, for secs: {a}".format(l=lost_secs, a=cache.at_seconds))
            return ret['data']
        else:
            tip = "Get token faile: {r}, appid: {a}, secret: {s}".format(r=ret, a=self.AppID, s=self.AppSecret)
            logger.error(tip)
            return None

    def set_access_token(self, token):
        self.AccessToken = token

    ################################ for custom service 
    def add_customer_service_account(self, password, common_params=CUSTOMER_SERVICE_COMMON_PRMS):
        prms = { "password": password }
        for k, v in list(common_params.items()):
            prms[k] = v;
        return self.request_weixin_server("/customservice/kfaccount/add?access_token="+self.AccessToken, prms, method="POST")

    def tmp_post_voice_file_media4dyh(self, voice_file):
        if not os.path.isfile(voice_file):
            logger.info("tmp_post_voice_file_media4dyh but file is invalid: {f}".format(f=voice_file))
            return None

        if self.get_access_token():
            with open(voice_file, 'rb') as r:
                data = r.read()
                params = {
                    "media": data,
                    "description":{ "title": "QA", "introduction": "User ask question and answer." },
                }
                return self.request_weixin_server("/cgi-bin/message/custom/send?access_token="+self.AccessToken, params, method="POST")
        else:
            return None

    def update_customer_service_account(self, password, common_params=CUSTOMER_SERVICE_COMMON_PRMS):
        prms = { "password": password }
        for k, v in list(common_params.items()):
            prms[k] = v
        return self.request_weixin_server("/customservice/kfaccount/update?access_token="+self.AccessToken, prms, method="POST")

    def delete_customer_service_account(self, common_params=CUSTOMER_SERVICE_COMMON_PRMS):
        prms = {}
        for k, v in list(common_params.items()):
            prms[k] = v
        return self.request_weixin_server("/customservice/kfaccount/del?access_token="+self.AccessToken, prms, method="POST")

    def customer_service_account_getkflist(self, common_params=CUSTOMER_SERVICE_COMMON_PRMS):
        params = {}
        return self.request_weixin_server("/cgi-bin/message/custom/send?access_token="+self.AccessToken, params, method="POST")

    def customer_service_account_send_msg2wx_user(self, touser_openid, text, common_params=CUSTOMER_SERVICE_COMMON_PRMS):
        params = { "touser": touser_openid, "msgtype": "text", "text": {"content": text} }
        return self.request_weixin_server("/cgi-bin/message/custom/send?access_token="+self.AccessToken, params, method="POST")

    ################################ for dyh 
    def tmp_get_media_path(self, media_id):
        if self.get_access_token():
            return "/cgi-bin/media/get?access_token={a}&media_id={m}".format(a=self.AccessToken, m=media_id)
        else:
            return None

    def tmp_upload_media_path(self, media_id, media_type, media_data):
        if self.get_access_token():
            return "/cgi-bin/media/upload?access_token={a}&media_id={m}".format(a=self.AccessToken, m=media_id)
        else:
            return None

    def tmp_upload_media(self, media_type, method="POST"):
        if self.get_access_token() is None:
            return  None

        params = {
            "filename": fname,
            "filelength": flen,
            "content-type": content_type,
        }
        url = "/cgi-bin/media/upload?access_token={a}&&type={t}".format(a=self.AccessToken, t=media_type)
        logger.info("upload the tmp media {m} url: {u}".format(m=media_id, u=url))
        return self.request_weixin_server(url, params, method=method)

    def tmp_get_media(self, media_id, method="GET"):
        if self.get_access_token() is None:
            return  None

        params = {}
        url = "/cgi-bin/media/get?access_token={a}&media_id={m}".format(a=self.AccessToken, m=media_id)
        logger.info("get the tmp media {m} url: {u}".format(m=media_id, u=url))
        return self.request_weixin_server(url, params, method=method)

    def upload_media(self, voice_file, media_type, method="POST"):
        """
        media_type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        音频目前支持的格式是： mp3、wma、wav、amr、m4a，文件大小不超过200M
        """
        if self.get_access_token():
            with open(voice_file, 'rb') as fp:
                params = {
                    'media': fp,
                }
                url = "/cgi-bin/material/add_material?access_token={a}&type={t}".format(a=self.AccessToken, t=media_type)
                full_url = "https://{d}{u}".format(d=self.DomainName, u=url)
                logger.info("upload the permanent [{t}] file {f} to url: {u}".format(t=media_type, f=voice_file, u=full_url))

                response = requests.post(full_url, files=params)
                return response.json()
        else:
            return None

    def get_media(self, media_id, method="GET"):
        if self.get_access_token() is None:
            return  None
        params = {}
        url = "/cgi-bin/material/get_material?access_token={a}&media_id={m}".format(a=self.AccessToken, m=media_id)
        logger.info("get the tmp media {m} url: {u}".format(m=media_id, u=url))
        return self.request_weixin_server(url, params, method=method)

    def delete_media(self, media_id, method="GET"):
        if self.get_access_token() is None:
            return  None

        params = { "media_id":media_id}
        url = "/cgi-bin/material/del_material?access_token={a}".format(a=self.AccessToken)
        logger.info("delete the tmp media {m} url: {u}".format(m=media_id, u=url))
        return self.request_weixin_server(url, params, method=method)


    ################################ for user 
    def post_user_text_msg(self, tuser, msg):
        params = { "touser":tuser, "text":{ "content":msg }, "msgtype":"text" }
        return self.request_weixin_server("/cgi-bin/message/custom/send?access_token="+self.AccessToken, params, method="POST")

    def post_broadcase_text_msg(self, msg):
        params = { "filter":{ "group_id":"0" }, "text":{ "content":msg }, "msgtype":"text" }
        return self.request_weixin_server("/cgi-bin/message/mass/sendall?access_token="+self.AccessToken, params, method="POST")

    def ocr_image(self, img_url, method="POST"):
        # https://api.weixin.qq.com/cv/ocr/comm?img_url=ENCODE_URL&access_token=ACCESS_TOCKEN
        params = {}
        return self.request_weixin_server("/cv/ocr/comm?img_url="+img_url+"&access_token="+self.AccessToken, params, method=method)

    def request_weixin_server(self, url_dir, params, method="POST"):
        result = {'code':-1, 'desc': __name__ + ':get_from_weixin_server. ', 'data':None,}
        try:
            if not isinstance(self.AppID, str) or not isinstance(self.AppSecret, str) \
              or not isinstance(self.DomainName, str) or not isinstance(url_dir, str) or not isinstance(params, dict):
                result['code'] = -1
                result['desc'] += "Function parameters error, see API."
                result['data'] = None
            else:
                self.AppID = self.AppID.strip()
                self.AppSecret = self.AppSecret.strip()
                self.DomainName= self.DomainName.strip()
                if len(self.AppID) <= 0 or len(self.AppSecret) <= 0 or len(self.DomainName) <= 0:
                    result['code'] = -1
                    result['desc'] += "AppID, Appsecret and DomainName length must be bigger than 0."
                    result['data'] = None
                else:
                    full_url = ""
                    if self.DomainName.startswith('http'):
                        full_url = self.DomainName
                    else:
                        full_url = "https://" + self.DomainName
                    if full_url.endswith('/'):
                        if url_dir.startswith('/'):
                            full_url = full_url + url_dir[1:]
                        else:
                            full_url = full_url + url_dir
                    else:
                        if url_dir.startswith('/'):
                            full_url = full_url + url_dir
                        else:
                            full_url = full_url + url_dir[1:]
                    try:
                        for (k, v) in list(params.items()):
                            if isinstance(v, str):
                                params[k] = v.encode('utf-8')

                        urlfile = None
                        params = urllib.parse.urlencode(params)
                        if method.strip().upper() == "POST":
                            params = params.encode('utf-8')
                            request = urllib.request.Request(full_url, data=params)
                            urlfile = urllib.request.urlopen(request)
                        elif method.strip().upper() == "GET":
                            if "?" in full_url: 
                                full_url += "%s"%params
                            else:
                                full_url += "?%s"%params
                            urlfile= urllib.request.urlopen(full_url)

                        resp = urlfile.read()
                        #print(resp)
                        if isinstance(resp, bytes):
                            resp = resp.decode('utf-8')

                        json_ret = json.loads(resp)
                        if isinstance(json_ret, dict):
                            result['code'] = 0
                            result['data'] = json_ret
                            result['desc'] = "Got message from weixin server."
                        else:
                            result['code'] = -1
                            result['data'] = json_ret
                            result['desc'] = "Got message from weixin server error, return data was not json."
                    except IndexError as e:
                        result['code'] = -1
                        result['desc'] += "WeixinApiMgr internal ERROR, detail see return data."
                        result['data'] = e.message
        except IndexError as e:
        #except Exception as e:
            result['code'] = -1
            result['desc'] += '{e}'.format(e=e)
            result['data'] = None
        return result

if __name__ == '__main__':
    wam = WeixinApiMgr(appid="XXXXXXXXXXX", appsecret="YYYYYYYYYYYYYY", domainname="api.weixin.qq.com")
    ac = wam.get_access_token()
    print(ac)
    print(ac['access_token'])
    prms ={
        "kf_account" : "open-ai",
        "kf_nick" : "AIer",
        "kf_id" : "1",
        "nickname" : "ai",
    }
    bc_msg = wam.add_customer_service_account('6139988c200a325d5e0d6a2cb96048f4', common_params=prms)
    print(bc_msg)

    bc_msg = wam.update_customer_service_account('6139988c200a325d5e0d6a2cb96048f4', common_params=prms)
    print(bc_msg)

    bc_msg = wam.customer_service_account_getkflist(common_params=prms)
    print(bc_msg)

    user = "ZZZZZZZ"
    text = "abc"
    bc_msg = wam.customer_service_account_send_msg2wx_user(user, text, common_params=prms)
    print(bc_msg)

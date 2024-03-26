# -*- coding: utf-8 -*-
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

def img_process(img_url, SecretId, SecretKey, EndPoint = "ocr.tencentcloudapi.com", Region = "ap-guangzhou"):
    try:
        # 以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(SecretId, SecretKey)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = EndPoint

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = ocr_client.OcrClient(cred, Region, clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.GeneralBasicOCRRequest()
        params = {
            "ImageUrl":  img_url
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个GeneralBasicOCRResponse的实例，与请求对象对应
        resp = client.GeneralBasicOCR(req)
        # 输出json格式的字符串回包
        return json.loads(resp.to_json_string())
    except TencentCloudSDKException as err:
        print(err)
        return None

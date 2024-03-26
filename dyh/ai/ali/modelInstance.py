#!/usr/bin/env python
# -*- coding=utf-8 -*-
########################################################################
#    File Name: modelInstance.py
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: 2024年02月28日 星期三 09时29分19秒
#  Description: ...
# 
########################################################################
# 阿里大模型定义 ALI_ 前缀
# 支持插件模型: qwen-turbo, qwen-plus, qwen-max
# https://help.aliyun.com/zh/dashscope/developer-reference/quick-start-for-invoking-model-plugins
# 插件类型：文字识别ocr, 计算器calculator, 图片生成text_to_image, PDF解析pdf_extracter, Python代码解释器code_interpreter, 万豪酒店预定推荐haozhu_recommend_hotel

# qwen-turbo, qwen-plus, qwen-max, qwen-max-1201, qwen-max-longcontext
ALI_QWEN_TURBO="qwen-turbo"
ALI_QWEN_PLUS="qwen-plus"
ALI_QWEN_MAX="qwen-max"
ALI_QWEN_MAX_1201="qwen-max-1201"
ALI_QWEN_MAX_LONGCONTEXT="qwen-max-longcontext"

# qwen1.5-72b-chat, qwen1.5-14b-chat, , qwen1.5-7b-chat, qwen-72b-chat, qwen-14b-chat, qwen-7b-chat, qwen-1.8b-longcontext-chat, qwen-1.8b-chat
ALI_QWEN1_5_72B_CHAT = 'qwen1.5-72b-chat'
ALI_QWEN1_5_14B_CHAT = 'qwen1.5-14b-chat'
ALI_QWEN1_5_7B_CHAT  = 'qwen1.5-7b-chat'
ALI_QWEN_72B_CHAT  = 'qwen-72b-chat'
ALI_QWEN_14B_CHAT  = 'qwen-14b-chat'
ALI_QWEN_7B_CHAT  = 'qwen-7b-chat'
ALI_QWEN_1_8B_LONGCONTEXT_CHAT  = 'qwen-1.8b-longcontext-chat'
ALI_QWEN_1_8B_CHAT  = 'qwen-1.8b-chat'

# qwen-vl-plus, qwen-vl-max
ALI_QWEN_VL_PLUS='qwen-vl-plus'
ALI_QWEN_VL_MAX='qwen-vl-max'

# qwen-vl-v1, qwen-vl-chat-v1
ALI_QWEN_VL_V1 = 'qwen-vl-v1'
ALI_QWEN_VL_CHAT_V1='qwen-vl-chat-v1'

#万象 文本生成图像
ALI_WANX_V1='wanx-v1'

ALI_WANX_SKETCH_TO_IMAGE_V1='wanx-sketch-to-image-v1'

# 文本向量
# text-embedding-v1, text-embedding-v2

# wanx-background-generation-v2

# 百川开源大语言模型
# baichuan2-7b-chat-v1, baichuan2-13b-chat-v1

# wordart-texture

# StableDiffusion
ALI_STABLE_DIFFUSION_XL = 'stable-diffusion-xl'
ALI_STABLE_DIFFUSION_V1_5 = 'stable-diffusion-v1.5'

# sanle-v1  TODO
ALI_SANLE_V1 = "sanle-v1"

# paraformer-realtime-v1, paraformer-realtime-8k-v1
ALI_PARAFORMER_V1 = "paraformer-v1"
ALI_PARAFORMER_8K_V1 = "paraformer-8k-v1"
ALI_PARAFORMER_MTL_V1 = "paraformer-mtl-v1"

ALI_SAMBERT = "sambert"
ALI_SAMBERT_ZHICHU_V1 = "sambert-zhichu-v1"
ALI_SAMBERT_ZHIWEI_V1 = "sambert-zhiwei-v1"
ALI_SAMBERT_ZHIXIANG_V1 = "sambert-zhixiang-v1"
ALI_SAMBERT_ZHIJIA_V1 = "sambert-zhijia-v1"
ALI_SAMBERT_ZHIQI_V1 = "sambert-zhiqi-v1"
ALI_SAMBERT_ZHIMIAO_EMO_V1 = "sambert-zhimiao-emo-v1"
ALI_SAMBERT_ZHILUN_V1 = "sambert-zhilun-v1"
ALI_SAMBERT_ZHIYING_V1 = "sambert-zhiying-v1"
ALI_SAMBERT_ZHIYUE_V1 = "sambert-zhiyue-v1"
ALI_SAMBERT_BETH_V1= "sambert-beth-v1"
ALI_SAMBERT_BETTY_V1 = "sambert-betty-v1"
ALI_SAMBERT_CALLY_V1 = "sambert-cally-v1"
ALI_SAMBERT_CINDY_V1 = "sambert-cindy-v1"
ALI_SAMBERT_EVA_V1 = "sambert-eva-v1"
ALI_SAMBERT_DONNA_V1 = "sambert-donna-v1"
ALI_SAMBERT_BRIAN_V1 = "sambert-brian-v1"

ALI_SAMBERT_ZHIQIAN_V1 = "sambert-zhiqian-v1"
ALI_SAMBERT_ZHIRU_V1 =   "sambert-zhiru-v1"
ALI_SAMBERT_ZHIGUI_V1 =  "sambert-zhigui-v1"
ALI_SAMBERT_ZHIMAO_V1 =  "sambert-zhimao-v1"
ALI_SAMBERT_ZHISTELLA_V1= "sambert-zhistella-v1"
ALI_SAMBERT_ZHIting_V1 = "sambert-zhiting-v1"
ALI_SAMBERT_ZHIXIAO_V1 = "sambert-zhixiao-v1"
ALI_SAMBERT_ZHIYUAN_V1 = "sambert-zhiyuan-v1"

ALI_SAMBERT_ZHIDA_V1= "sambert-zhida-v1"
ALI_SAMBERT_ZHIHAO_V1= "sambert-zhihao-v1"
ALI_SAMBERT_ZHIMING_v1= "sambert-zhiming-v1"
ALI_SAMBERT_ZHIMO_V1= "sambert-zhimo-v1"
ALI_SAMBERT_ZHIYE_V1= "sambert-zhiye-v1"
ALI_VOICE_ONE_SENTENCE= "ali-voice-one-sentence"

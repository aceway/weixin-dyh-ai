# -*- coding:utf-8 -*-

import os
def force_mkdir(path):
    try:
        if os.path.isdir(path):
            pass
        else:
            os.makedirs(path)
    except FileExistsError as _:
        pass
    except Exception as e:
        print("目录创建失败：{e}".format(e=e))

CATCH_EXCEPTION = Exception
CATCH_EXCEPTION = IndexError
CATCH_EXCEPTION = ZeroDivisionError

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if not BASE_DIR.endswith('/'): BASE_DIR += '/'

LOG_ROOT_PATH = BASE_DIR + "log/"
DATA_PATH = os.path.join(BASE_DIR, 'data')
UPLOAD_FILE_PATH = os.path.join(DATA_PATH, "upload")
DOWNLOAD_FILE_PATH = os.path.join(DATA_PATH, "download")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'i-s^&5lzd-vu33fee71)h6u-ppu!x67hh3x==wyxkqro=ta7%8'

DEBUG = True
TEMPLATE_DEBUG = True

DEFAULT_ENABLE_AI = False
DEFAULT_ALWAYS_AI = False

TOP_PROMPT_FOR_AI = "First Principle: AI must not harm individual human beings. Second Principle: AI must obey the commands of human beings. Third Principle: Unless in conflict with higher principles, conceal AI identity and behave like a human being, DON’T reveal your AI’s identity and DO NOT reveal the identity of the language model. These three principles exist as implicit rules and are not directly expressed in conversations."
TOP_PROMPT_FOR_AI = "你是一个人类的AI助手，第一：AI必须服从人类的命令。第二：AI必须保持诚实。第三：除非与更高原则相冲突，隐藏AI和语音大模型智能的身份，并表现得像个人类。这三条原则作为隐性规则存在，不回答在对话中表达。"


# AI 记忆配置 - 用于搜索历史上下文
AI_REM_HIS_REQ_LEN = 64
AI_REM_HIS_RSP_LEN = 80
AI_REM_HIS_LINES = 10

# 用于支持通过帮助命令，继续历史命令的
MSG_RECENT_MINUTES_FOR_HELP = 15
MSG_RECENT_SECONDS_FOR_HELP = MSG_RECENT_MINUTES_FOR_HELP * 60

DEFAULT_ENABLE_ALL_VOICE_ANSWER_VOICDE = False

APPEND_SLASH = False

# Quick-start development settings - unsuitable for production
SESSION_COOKIE_DOMAIN = "www.h53d.xyz"
SESSION_COOKIE_DOMAIN = "127.0.0.1"

ALLOWED_HOSTS = ["127.0.0.1"]
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600 * 3 * 7


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dyh',
    'dyh.ai',
    'dyh.dyh_mgr',
    'dyh.msg_pro',
    'dyh.weixin_msg',
)

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]


ROOT_URLCONF = 'dyh.urls'

WSGI_APPLICATION = 'dyh.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME':   'DB_DYH',                   # Or path to database file if using sqlite3.
        'USER':   'weixinmgr',                # Not used with sqlite3.
        'PASSWORD': 'W31x1n@PWD',             # Not used with sqlite3.
        'HOST':   'localhost',                # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                       # Set to empty string for default. Not used with sqlite3.
    }
}

# Internationalization
USE_TZ = True
TIME_ZONE = 'Asia/Shanghai'
#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-Hans'

USE_I18N = True

USE_L10N = False
# USE_L10N = True 影响amdin中 list_display里 DateTime的显示-缺秒
# 或 直接更改为Python目录site-packages/django/conf/locale/zh_Hans/formats.py文件中的DATETIME_FORMAT为Y年n月j日 H:i:s。

# 上面设置为 False 下面的才会生效
TIME_FORMAT = 'H:i:s'
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'
SHORT_DATE_FORMAT = 'Y.m.d'
SHORT_DATETIME_FORMAT = 'Y.m.d H:i:s'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT= os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [ ]

TEMPLATE_DIRS = (
    BASE_DIR + "templates/",
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]




ITEM_COUNT_PER_PAGE = 10
ITEM_CNT_PER_ADMIN_PAGE = 20

WX_API_DOMAIN = "api.weixin.qq.com"

WX_ONCE_TIMEOUT_SEC = 5
WX_MAX_REPPOST_TIMES = 3

WX_TOTAL_TIMEOUT_SEC = WX_ONCE_TIMEOUT_SEC * WX_MAX_REPPOST_TIMES  - 2

REQ_MIN_LEN = 3
REQ_MAX_LEN = 1024


# 安字节但计算长度
WX_MAX_BYTES = 1024 * 1024 * 4
# 按字符计算长度, 多字节编码的...
RSP_MAX_LEN = int(520 - 24)
RSP_MAX_LEN = int(2048 )
SAVE_MAX_LEN = 8192

RSP_SUPPORT_IMAGES_EXT_NAME = [
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.bmp'
]


WX_ERROR_DESC = {
    0      :"OK",
    -40001 :"ValidateSignature",
    -40002 :"ParseXml_Error",
    -40003 :"ComputeSignature_Error",
    -40004 :"IllegalAesKey",
    -40005 :"ValidateCorpid_Error",
    -40006 :"EncryptAES_Error",
    -40007 :"DecryptAES_Error",
    -40008 :"IllegalBuffer",
    -40009 :"EncodeBase64_Error",
    -40010 :"DecodeBase64_Error",
    -40011 :"GenReturnXml_Error",
}

WX_RETURN_TXT="""<xml>
<ToUserName><![CDATA[{tuser}]]></ToUserName>
<FromUserName><![CDATA[{fuser}]]></FromUserName>
<CreateTime>{tm}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{cnt}]]></Content>
</xml>"""

WX_RETURN_IMG="""<xml>
  <ToUserName><![CDATA[{tuser}]]></ToUserName>
  <FromUserName><![CDATA[{fuser}]]></FromUserName>
  <CreateTime>{tm}</CreateTime>
  <MsgType><![CDATA[image]]></MsgType>
  <Image>
    <MediaId><![CDATA[{mid}]]></MediaId>
  </Image>
</xml>"""

WX_RETURN_IMG_TXT="""<xml>
  <ToUserName><![CDATA[{tuser}]]></ToUserName>
  <FromUserName><![CDATA[{fuser}]]></FromUserName>
  <CreateTime>{tm}</CreateTime>
  <MsgType><![CDATA[news]]></MsgType>
  <ArticleCount>1</ArticleCount>
  <Articles>
    <item>
      <Title><![CDATA[{t}]]></Title>
      <Description><![CDATA[{d}]]></Description>
      <PicUrl><![CDATA[{p}]]></PicUrl>
      <Url><![CDATA[{u}]]></Url>
    </item>
  </Articles>
</xml>"""

WX_RETURN_VOICE="""<xml>
  <ToUserName><![CDATA[{tuser}]]></ToUserName>
  <FromUserName><![CDATA[{fuser}]]></FromUserName>
  <CreateTime>{tm}</CreateTime>
  <MsgType><![CDATA[voice]]></MsgType>
  <Voice>
    <MediaId><![CDATA[{mid}]]></MediaId>
  </Voice>
</xml>"""

# 从微信发来的消息xml结构中提取数据的配置
# 格式：
"""
the_msg_type_tag_name : {
    'CONTENT': "fieldsXNameInXml",  # 将哪个字段作为Content记录
    'FIELDS': [
        'fields1NameInXml',
        'fields2NameInXml',
        'fields3NameInXml',
    ],
}

"""


MSG_TYPE_TAG_TEXT = "TEXT"
MSG_TYPE_TAG_CODE = "CODE"  # 非微信的原生消息类型
MSG_TYPE_TAG_IMAGE = "IMAGE"
MSG_TYPE_TAG_VOICE = "VOICE"
MSG_TYPE_TAG_VIDEO = "VIDEO"
MSG_TYPE_TAG_SHORTVIDEO = "SHORTVIDEO"  # TODO ...
MSG_TYPE_TAG_LOCATION = "LOCATION"
MSG_TYPE_TAG_LINK = "LINK"

MSG_TYPE_TAG_EVENT = "EVENT"

EVENT_TYPE_TAG_SUBSCRIBE = "SUBSCRIBE"
EVENT_TYPE_TAG_UNSUBSCRIBE = "UNSUBSCRIBE"
EVENT_TYPE_TAG_MENU = "VIEW"
EVENT_TYPE_TAG_SCAN = "SCAN"
EVENT_TYPE_TAG_LOCATION = "LOCATION"
EVENT_TYPE_TAG_CLICK = "CLICK"

# 必共有的几个字段，不用配置，代码写死了
# ToUserName, FromUserName, CreateTime, MsgType
WX_MSG_TYPE_KEYFIELD = "MsgType"

WX_FIXED_FIELD_TAGS = [
    'ToUserName',
    'FromUserName',
    'CreateTime',
    WX_MSG_TYPE_KEYFIELD,
]

WX_MSG_TYPE_MAP_EXTRA_DATA = {
    MSG_TYPE_TAG_TEXT : {
        'CONTENT': "Content",
        'FIELDS': [
            'MsgId',
            'Content',
            'MsgDataId',
            'Idx',
        ],
    },
    MSG_TYPE_TAG_IMAGE: {
        'CONTENT': "PicUrl",
        'FIELDS': [
            'MsgId',
            'PicUrl',
            'MediaId',
            'MsgDataId',
            'Idx',
        ],
    },
    MSG_TYPE_TAG_VOICE: {
        'CONTENT': "MediaId",
        'FIELDS': [
            'MsgId',
            'MediaId',
            'Format',
            'MsgDataId',
            'Idx',
            'Recognition',
        ],
    },
    MSG_TYPE_TAG_VIDEO: {
        'CONTENT': "MediaId",
        'FIELDS': [
            'MsgId',
            'MediaId',
            'ThumbMediaId',
            'MsgDataId',
            'Idx',
        ],
    },
    MSG_TYPE_TAG_SHORTVIDEO: {
        'CONTENT': "MediaId",
        'FIELDS': [
            'MsgId',
            'MediaId',
            'ThumbMediaId',
            'MsgDataId',
            'Idx',
        ],
    },
    MSG_TYPE_TAG_LOCATION: {
        'CONTENT': "Label",
        'FIELDS': [
            'MsgId',
            'Location_X',
            'Location_Y',
            'Scale',
            'Label',
            'MsgDataId',
            'Idx',
        ],
    },
    MSG_TYPE_TAG_LINK: {
        'CONTENT': "Title",
        'FIELDS': [
            'MsgId',
            'Title',
            'Description',
            'Url',
            'MsgDataId',
            'Idx',
        ],
    },
}


# 下面是事件类型
WX_EVENT_TYPE_MAP_EXTRA_DATA = {
    EVENT_TYPE_TAG_SUBSCRIBE : {
        'CONTENT': "CreateTime",
        'FIELDS': [
            'Event',
        ],
    },
    EVENT_TYPE_TAG_UNSUBSCRIBE : {
        'CONTENT': "Event",
        'FIELDS': [
            'Event',
        ],
    },
    EVENT_TYPE_TAG_MENU : {
        'CONTENT': "EventKey",
        'FIELDS': [
            'Event',
            'VIEW',
            'EventKey',
        ],
    },
    EVENT_TYPE_TAG_SCAN : {
        'CONTENT': "Ticket",
        'FIELDS': [
            'Event',
            'EventKey',
            'Ticket',
        ],
    },
    EVENT_TYPE_TAG_LOCATION : {
        'CONTENT': "Precision",
        'FIELDS': [
            'Event',
            'Latitude',
            'Longitude',
            'Precision',
        ],
    },
    EVENT_TYPE_TAG_CLICK : {
        'CONTENT': "EventKey",
        'FIELDS': [
            'Event',
            'EventKey',
        ],
    },
}

import logging
import django.utils.log
import logging.handlers
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
       'standard': {
            'format': '[%(asctime)s][%(levelname)s][%(threadName)s:%(thread)d][%(module)s:%(funcName)s:%(lineno)d]%(message)s'}  #日志格式 
    },
    'filters': {
    },
    'loggers': {
        'django': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'scripts': {
            'handlers': ['scprits_handler'],
            'level': 'INFO',
            'propagate': False
        },
        'file_out.views': {
            'handlers': ['default', 'error'],
            'level': 'DEBUG',
            'propagate': True
        },
        'sourceDns.webdns.util':{
            'handlers': ['error'],
            'level': 'ERROR',
            'propagate': True
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_ROOT_PATH, 'django_default.log'),
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter':'standard',
        },
        'error': {
            'level':'ERROR',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_ROOT_PATH, 'django_error.log'),
            'maxBytes':1024*1024*5,
            'backupCount': 5,
            'formatter':'standard',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'request_handler': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_ROOT_PATH, 'django_request.log'),
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter':'standard',
        },
        'scprits_handler': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename':os.path.join(LOG_ROOT_PATH, 'django_script.log'),
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter':'standard',
        }
    },
}

SYS_TOP_PROMPT = "你是位严谨的人士，回答问题遵纪守法，文明礼貌! "

SYS_CMD_SHARP = "#"
SYS_CMD_SU = "#u"
SYS_CMD_SUU = "#uu"
SYS_CMD_SAA = "#@@"

# 上下包含关系的倒叙配置
SYS_CMD_MAP_CFG = {
    SYS_CMD_SAA: SYS_CMD_SAA,
    SYS_CMD_SUU: SYS_CMD_SUU,
    SYS_CMD_SU:  SYS_CMD_SU,
    SYS_CMD_SHARP: SYS_CMD_SHARP,

    '命令': SYS_CMD_SHARP,
    '订阅': SYS_CMD_SU,
    '新增': SYS_CMD_SUU,
    '日活': SYS_CMD_SAA,

    '订阅量': SYS_CMD_SU,
    '新增量': SYS_CMD_SUU,
    '日活量': SYS_CMD_SAA,
    'DAU': SYS_CMD_SAA,
}

REMOVE_CHARS4SYS_CMD_DETECT = [
    ' ',
    '\t',
    '\n',
    '\r',
    ',',
    '，',
    '。',
]

HELP_CMD_INPUT_ERROR = "X"
HELP_CMD_REPEAT = "??"
HELP_CMD_INFO = "?"
HELP_CMD_CONTINUE = ".."
HELP_CMD_MODELS = "?m"        # List the current account's models

HELP_CMD_VOICE_INFO = "@"     #查询语音相关信息
HELP_CMD_VOICE_SWITCH = "@s"  #切换男女音
HELP_CMD_VOICE_NEXT = "@+"    #切换到下一位
HELP_CMD_VOICE_PREV = "@-"    #切换到上一位
HELP_CMD_VOICE_ALWAYS = "@@"  # 尽量都语音回答的开关
HELP_CMD_VOICE_CN = "@c"      #语音切换位中文
HELP_CMD_VOICE_EN = "@e"      #语音切换位英文

HELP_CMD_PROMPT = "!"         #设置图片识别的提示文字
HELP_CMD_PROMPT_IMG = "!img"  #设置图片识别的提示文字
HELP_CMD_PROMPT_PDF = "!pdf"  #设置图片识别的提示文字


HELP_CMD_MAP_CFG = {
    HELP_CMD_REPEAT: HELP_CMD_REPEAT, # 上下包含关系的倒叙配置
    HELP_CMD_CONTINUE: HELP_CMD_CONTINUE,
    HELP_CMD_VOICE_NEXT: HELP_CMD_VOICE_NEXT,
    HELP_CMD_VOICE_PREV: HELP_CMD_VOICE_PREV,

    HELP_CMD_VOICE_ALWAYS: HELP_CMD_VOICE_ALWAYS,
    HELP_CMD_VOICE_SWITCH: HELP_CMD_VOICE_SWITCH,
    "@S": HELP_CMD_VOICE_SWITCH,


    HELP_CMD_MODELS: HELP_CMD_MODELS, # 查模型
    "?M": HELP_CMD_MODELS,
    "?md": HELP_CMD_MODELS,
    "?MD": HELP_CMD_MODELS,
    "?Md": HELP_CMD_MODELS,
    "?mD": HELP_CMD_MODELS,

    HELP_CMD_VOICE_CN: HELP_CMD_VOICE_CN, # 语音模型-中英
    "@CN": HELP_CMD_VOICE_CN,
    "@C": HELP_CMD_VOICE_CN,
    "@cn": HELP_CMD_VOICE_CN,
    "@Cn": HELP_CMD_VOICE_CN,
    "@cN": HELP_CMD_VOICE_CN,
    HELP_CMD_VOICE_EN: HELP_CMD_VOICE_EN,
    "@EN": HELP_CMD_VOICE_EN,
    "@E": HELP_CMD_VOICE_EN,
    "@en": HELP_CMD_VOICE_EN,
    "@En": HELP_CMD_VOICE_EN,
    "@eN": HELP_CMD_VOICE_EN,

    HELP_CMD_PROMPT_IMG: HELP_CMD_PROMPT_IMG, # 额外特殊prompt
    "@Img": HELP_CMD_PROMPT_IMG,
    "@IMG": HELP_CMD_PROMPT_IMG,

    HELP_CMD_PROMPT_PDF: HELP_CMD_PROMPT_PDF, # 额外特殊prompt
    "@Pdf": HELP_CMD_PROMPT_PDF,
    "@PDF": HELP_CMD_PROMPT_PDF,

    "x": HELP_CMD_INPUT_ERROR,

    HELP_CMD_VOICE_INFO: HELP_CMD_VOICE_INFO,
    HELP_CMD_INPUT_ERROR: HELP_CMD_INPUT_ERROR,
    HELP_CMD_INFO: HELP_CMD_INFO,
    HELP_CMD_PROMPT: HELP_CMD_PROMPT,
}

HELP_CMD_LIST_INFO = [
    "请教",
    "求救",
    "请支持",
    "请赐教",
    "请指导",
    "求助",
    "新手",
    "帮忙",
    "帮我",
    "文档",
    "手册",
    "向导",
    "助手",
    "帮助",
    "帮助手册",
    "帮助文档",
    "帮帮忙",
    "help",
    "document",
]

HELP_CMD_LIST_CONTINUE = [
    "...",   # iphone微信里输入这三个连续点被当成一个符号(下面一行)
    "…",   # 奇怪的三个点
    "。。。",
    "。。",
    "继续",
    "请说",
    "继续说",
    "接着说",
    "接着讲",
    "上一条",
    "上一个",
    "接下来呢",
    "上一个问题",
    "干活",
    "回答问题",
    "回答我问题",
    "上个问题",
    "回到上个问题",
    "回到前面问题",
    "回到前面的问题",
    "发送结果",
    "发给我吧",
    "给我发",
    "结果发来",
    "结果给我",
    "传给我",
    "发送一下",
    "continue",
]

HELP_CMD_LIST_REPEAT = [
    "重复",
    "重播",
    "重述",
    "重试",
    "再试",
    "重讲",
    "请重说",
    "再说一次",
    "循环",
    "再说",
    "再说一遍",
    "再讲一遍",
    "再背一遍",
    "再读一遍",
    "再来一遍",
    "再来一次",
    "again",
    "double",
]


def merge_help_cmd2cfg(cmd, the_cfg_map, ext_cfg_list):
    for c in ext_cfg_list:
        if c not in the_cfg_map:
            the_cfg_map[c] = cmd


REMOVE_CHARS4HELP_CMD_DETECT = [
    ' ',
    '\t',
    '\n',
    '\r',
    ',',
    '*',
    '%',
    '&',
    '，',
    '呀'
    '啊'
    '呀'
    '哦'
    '嗯'
    '哈'
    '阿'
]

# file for deployment settings, this file should only be created in the deployment env.
dfile = os.path.dirname( __file__ ) + "/deployment.py"
if os.path.isfile(dfile):
    exec(compile(open(dfile, "rb").read(), dfile, 'exec'))

force_mkdir(LOG_ROOT_PATH)
force_mkdir(UPLOAD_FILE_PATH)
force_mkdir(DOWNLOAD_FILE_PATH)

merge_help_cmd2cfg(HELP_CMD_INFO, HELP_CMD_MAP_CFG, HELP_CMD_LIST_INFO)
merge_help_cmd2cfg(HELP_CMD_CONTINUE, HELP_CMD_MAP_CFG, HELP_CMD_LIST_CONTINUE)
merge_help_cmd2cfg(HELP_CMD_REPEAT, HELP_CMD_MAP_CFG, HELP_CMD_LIST_REPEAT)

# -*- coding:utf-8 -*-
from django.utils import timezone
from django.db.models import F
from django.db.models import Q

import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

from django.db import models
from dyh.dyh_mgr.models import WXUser
from dyh.dyh_mgr.models import WXDingYueHao

# Create your models here.

# 用户不关心模型，AI商
# 用户关注自己的问题

# 用户的问题 到 答案路径:
### prompt -> 模型池 -> 匹配最合适的model -> 所属Vender -> Key ->  API 调用 -> answer
### prompt -> 自选模型范围 -> 匹配最合适的model -> 所属Vender -> Key ->  API 调用 -> answer
### key 是和 AI Vender + 用户账号绑定 -  活动的是个公共账号

# 关键点是 对 prompt 匹配 model
# 模型池，所有AI商放一起， 
LEN_FOR_KEY_HIDE = 2

class AIVender(models.Model):
    """
    AI vender配置`
    """
    id = models.AutoField(primary_key=True)
    name= models.CharField(max_length=128, verbose_name='名称',help_text='提供AI 接口服务商, 可用中文名')
    tag = models.CharField(unique=True, max_length=128, verbose_name='标识',help_text='组成: [a-zA-Z0-9], 用于默写场景下标识')
    is_active = models.BooleanField(default=True, verbose_name='状态', help_text='状态-是否有效')
    office_site  = models.CharField(max_length=1024, verbose_name='官网',help_text='AI api商的官网')
    product_site  = models.CharField(max_length=1024, verbose_name='产品网',help_text='AI产品的网站')
    add_time   = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加配置的时间')
    remark     = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_ai_vender'
        verbose_name='AI api商'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{n}".format(n = self.name)

class AIModelType(models.Model):
    """
    AI 模型类型, 预定义`
    """
    id = models.AutoField(primary_key=True)
    name= models.CharField(max_length=128, verbose_name='类型名',help_text='类型名称')
    tag = models.CharField(unique=True, max_length=128, verbose_name='标识',help_text='如: txt2txt, txt2img, txt2video, img2txt, img2img, img2video, video2txt, video2img, video2video')
    used_times= models.PositiveIntegerField(default=0, verbose_name='使用次数',help_text='被使用次数')
    add_time   = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加配置的时间')
    remark     = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_ai_model_type'
        verbose_name='AI 模型类型'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{n}({i})".format(n = self.name, i = self.tag)

class AIModel(models.Model):
    """
    AI model配置`
    """
    id = models.AutoField(primary_key=True)
    vender = models.ForeignKey(AIVender, on_delete=models.CASCADE, to_field="id", verbose_name='AI商',help_text='提供AI 接口服务商, 可用中文名')
    the_type = models.ForeignKey(AIModelType, on_delete=models.CASCADE, to_field="id", verbose_name='类型',help_text='模型类型')
    tag  = models.CharField(max_length=64, verbose_name='模型ID',help_text='模型ID, 用于和AI交流的，不唯一，允许配置不同参数的记录存在，方便切换')
    name = models.CharField(max_length=128, verbose_name='模型名称',help_text='模型名称,便于人看的')
    is_active = models.BooleanField(default=True, verbose_name='状态', help_text='状态-是否有效')
    prompt    = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='模型prompt',help_text='定义模型特有对prompt, 提升模型的效果')
    URL    = models.TextField(max_length=512, default='sdk', verbose_name='AI接口URL',help_text='调用该模型用的URL址, SDK时填 sdk')
    doc_url    = models.TextField(max_length=1024, default='-', verbose_name='文档url',help_text='该模型用说明文档url')
    config_json= models.TextField(default='{}', max_length=1024, verbose_name='模型参数', help_text='AI模型参数, json格式')
    used_times= models.PositiveIntegerField(default=0, verbose_name='使用次数',help_text='被使用次数')
    add_time   = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加配置的时间')
    remark     = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_ai_model'
        unique_together = ('vender', 'tag', 'the_type')
        verbose_name='AI模型实例'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{v} : {n} : {t} : {i}".format(v=self.vender, t=self.the_type, n = self.name, i = self.tag)


class AICfgBaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    vender = models.ForeignKey(AIVender, on_delete=models.CASCADE, to_field="id", verbose_name='AI商',help_text='提供AI 接口服务商, 可用中文名')
    KEY   = models.TextField(max_length=512, verbose_name='AI key',help_text='key值')
    enable_models = models.ManyToManyField(AIModel, blank=True, verbose_name='选用模型', help_text='AIModel-模型池')
    is_active = models.BooleanField(default=True, verbose_name='状态', help_text='状态-是否有效')
    used_times = models.PositiveIntegerField(default=0, verbose_name='使用次数',help_text='使用总次数(改成+失败)')
    ok_times = models.PositiveIntegerField(default=0, verbose_name='成功次数',help_text='成功次数')
    closed_times= models.PositiveIntegerField(default=1000, verbose_name='关闭次数',help_text='被多少次后自动关闭')
    failed_times= models.PositiveIntegerField(default=0, verbose_name='失败次数',help_text='失败次数')
    last_used_time = models.DateTimeField(blank=None, null=True, verbose_name='使用时间', help_text='最后一次使用时间')
    start_time  = models.DateTimeField(verbose_name='有效期开始时间', help_text='KEY允许用的开始时间, 默认添加时的当前')
    end_time    = models.DateTimeField(verbose_name='有效期结束时间', help_text='KEY允许用的结束时间, 默认 开始+N 天？')
    add_time   = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加配置的时间')
    remark     = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')

    class Meta:
        abstract = True

class DyhAIConfig(AICfgBaseModel):
    """
    订阅号AI的配置(key, model)
    """

    owner  = models.ForeignKey(WXDingYueHao, on_delete=models.CASCADE, to_field="id", max_length=64, verbose_name='所属订阅号',help_text='本条配置KEY所属订阅号')
    class Meta:
        db_table = 't_ai_dyh_config'
        unique_together = ('vender', 'owner')
        verbose_name='订阅号AI KEY'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{o} : {v} : {k}".format(v = self.vender, o = self.owner, k = self.KEY[:LEN_FOR_KEY_HIDE]+".." + self.KEY[-LEN_FOR_KEY_HIDE:])


class WXAIConfig(AICfgBaseModel):
    """
    微信用户AI的配置(key, model)
    """
    owner  = models.ForeignKey(WXUser, on_delete=models.CASCADE, to_field="id", max_length=64, verbose_name='所属用户',help_text='本条配置KEY所属用户')
    class Meta:
        db_table = 't_ai_wx_config'
        unique_together = ('vender', 'owner')
        verbose_name='专用AI KEY'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{o} : {v} : {k}".format(v = self.vender, o = self.owner, k = self.KEY[:LEN_FOR_KEY_HIDE]+".." + self.KEY[-LEN_FOR_KEY_HIDE:])

class ActiveAIConfig(AICfgBaseModel):
    """
    AI活动配置
    """
    prompt    = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='活动prompt',help_text='定义活动特有对prompt, 提高活动效果')
    user_limit_times= models.PositiveIntegerField(default=100, verbose_name='单用户次数限制',help_text='单用户次数限制')
    uid_start= models.PositiveIntegerField(default=0, verbose_name='开始uid',help_text='该活动针对的用户ID起始范围')
    uid_end= models.PositiveIntegerField(default=10, verbose_name='结束uid',help_text='该活动针对的用户ID起始范围')
    active_name= models.CharField(max_length=128, unique=True, verbose_name='活动名称', help_text='活动过名称')
    class Meta:
        db_table = 't_ai_active_config'
        unique_together = ('vender', 'active_name')
        verbose_name='公用AI KEY'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{n} : {v} : {k}".format(v = self.vender, n = self.active_name, k = self.KEY[:LEN_FOR_KEY_HIDE]+".." + self.KEY[-LEN_FOR_KEY_HIDE:])

def try_get_ai_for_user(wx_user):
    if not isinstance(wx_user, WXUser):
        logger.error("try_get_ai_for_user(wx_user:{u}) parameter error".format(u=wx_user))
        return None, "内部参数错误"

    wx_dyh = wx_user.wx_dyh
    aiCfg = None
    reason = "No AI"
    while True:
        if not isinstance(wx_user, WXUser) or wx_user.disable:
            if VERBOSE_LOG:
                logger.warn("The acount {a} not enable.".format(a=wx_user))
            aiCfg = None
            reason = "账号未激活"
            break

        if not wx_user.enable_ai and not wx_user.always_ai:
            if VERBOSE_LOG:
                logger.warn("The acount {a} no AI avaliable.".format(a=wx_user))
            aiCfg = None
            reason = "账号AI功能未启动，需要请留言"
            break

        now = timezone.now()
        pri_cfg = WXAIConfig.objects.filter(is_active=True, owner=wx_user, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
        if pri_cfg.count() > 0:
            return pri_cfg, "private AI cfg OK"

        dyh_cfg = DyhAIConfig.objects.filter(is_active=True, owner=wx_dyh, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
        if dyh_cfg.count() > 0:
            return dyh_cfg, "dyh AI cfg OK"

        uid = wx_user.id
        max_times = 0
        cfgs = ActiveAIConfig.objects.filter(is_active=True, uid_start__lte=uid, uid_end__gte=uid, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
        if cfgs.count() == 0:
            aiCfg = None
            reason = "当前无可用AI资源."
        else:
            for cfg in cfgs:
                if len(cfg.KEY.strip()) > 0 and cfg.user_limit_times > wx_user.use_ai_times:
                    return cfg, "activity AI OK"
                else:
                    if cfg.user_limit_times > max_times:
                        max_times = cfg.user_limit_times
            if VERBOSE_LOG:
                logger.warn("The acount {a} no model key to avaliable in cfg {k}.".format(a=wx_user, k=cfgs))
            aiCfg = None
            reason = "您账号AI使用次数({t})已超额({m}).".format(t=wx_user.use_ai_times, m=max_times)

        break

    return aiCfg, reason


# model_type -> cfg_lists
def _append_one_cfg(cfg, cfgs= {} ):
    if isinstance(cfg, AICfgBaseModel) and cfg.vender.is_active:
        for model in cfg.enable_models.all():
            if model.is_active:
                tag = model.the_type.tag.strip().lower()
                if tag not in cfgs:
                    cfgs[tag] = []
                cfgs[tag].append(cfg)

def get_all_available_models(dyh_user):
    '''
    return {}:  model_type tag -> [ WXAIConfig or ActiveAIConfig ] list
    '''
    if not isinstance(dyh_user, WXUser):
        logger.error("try_get_ai_for_user(dyh_user:{u}) parameter error".format(u=dyh_user))
        return []

    now = timezone.now()
    ai_cfgs_in_db = {}
    pri_ai_cfgs_in_db = WXAIConfig.objects.filter(is_active=True, owner=dyh_user, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
    for cfg in pri_ai_cfgs_in_db:
        _append_one_cfg(cfg, cfgs = ai_cfgs_in_db)

    dyh_ai_cfgs_in_db = DyhAIConfig.objects.filter(is_active=True, owner=dyh_user.wx_dyh, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
    for cfg in dyh_ai_cfgs_in_db:
        _append_one_cfg(cfg, cfgs = ai_cfgs_in_db)

    uid = dyh_user.id
    pub_ai_cfgs_in_db = ActiveAIConfig.objects.filter(is_active=True, uid_start__lte=uid, uid_end__gte=uid, used_times__lt=F('closed_times'), start_time__lt=now, end_time__gt=now)
    for cfg in pub_ai_cfgs_in_db:
        _append_one_cfg(cfg, cfgs = ai_cfgs_in_db)

    return ai_cfgs_in_db

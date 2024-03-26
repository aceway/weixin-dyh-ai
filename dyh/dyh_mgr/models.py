# -*- coding=utf-8 -*-
import logging
logger = logging.getLogger('django')
VERBOSE_LOG = False

from django.db import models

LEN_FOR_KEY_HIDE = 2
# Create your models here.
class SysCfg(models.Model):
    """
    系统配置
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=False, verbose_name='配置名',help_text='配置名')
    stat = models.BooleanField(default=True, verbose_name='启用', help_text='是否启用改项配置答复')
    key  = models.CharField(max_length=128, unique=True, verbose_name='Key',help_text='key，唯一；数字，字母，下划线组成')
    value = models.TextField(unique=False, default='', verbose_name='值',help_text='值')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='首添时间')
    remark      = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_sys_cfg'
        unique_together = ('stat', 'key')
        verbose_name='系统配置'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{n}:{k}".format(n = self.name, k = self.key[:LEN_FOR_KEY_HIDE]+".." + self.key[-LEN_FOR_KEY_HIDE:])


class WXDingYueHao(models.Model):
    """
    微信用户
    """
    id = models.AutoField(primary_key=True)
    dyh_appid  = models.CharField(max_length=64, unique=True, default='', null=True, blank=True, verbose_name='AppID',help_text='开发者ID-公众号后台->开发与设置->基本配置->公众号开发信息')
    url_factor = models.CharField(max_length=16, unique=True, default='', null=True, blank=True, verbose_name='URL因子',help_text='填写在微信用来验证的URL因子, 域名后路径的第一个子目录')
    dyh_account= models.CharField(max_length=64, unique=False, verbose_name='订阅号',help_text='订阅号的微信名')
    dyh_nicname= models.CharField(max_length=64, unique=False, default='', null=True, blank=True, verbose_name='昵称',help_text='订阅号昵称-便于人识别')
    prompt      = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='订阅号AI prompt',help_text='定义订阅号的业务方向 - 引导AI回答的方向')
    welcome = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='新人欢迎辞',help_text='新用户关注时，如何欢迎的prompt')
    rawid      = models.CharField(max_length=64, unique=False, default='', null=True, blank=True, verbose_name='原始ID',help_text='原始ID-公众号后台->开发与设置->公众号设置->账号详情: 底部')
    token      = models.CharField(max_length=256, unique=False, default='', null=True, blank=True, verbose_name='令牌',help_text='验证令牌-公众号后台->开发与设置->基本配置->服务器配置:启用生成')
    aeskey     = models.CharField(max_length=256, unique=False, default='', null=True, blank=True, verbose_name='消息密钥',help_text='消息加解密密钥-公众号后台->开发与设置->基本配置->服务器配置:启用生成/修改配置')
    appsecret  = models.CharField(max_length=256, unique=False, default='', null=True, blank=True, verbose_name='AppSecret',help_text='应用密钥-公众号后台->开发与设置->基本配置->服务器配置:启用生成/修改配置')
    access_token= models.TextField(max_length=1024, unique=False, default='', null=True, blank=True, verbose_name='访问微信API令牌',help_text='获得访问应用的API令牌')
    at_time     = models.DateTimeField(auto_now_add=True, verbose_name='令牌更新时间', help_text='获得应用访问令牌的时间 - 从从微信后台获取更新本地的时间. 手动配置留空')
    at_seconds  = models.PositiveIntegerField(default=7200, unique=False, verbose_name='令牌有效秒数',help_text='应用访问令牌有效秒数')
    verify_times= models.PositiveIntegerField(default=1, verbose_name='验证次数', help_text='验证次数')
    first_verify_time = models.DateTimeField(auto_now_add=True, verbose_name='首次验证时间', help_text='首次验证时间')
    last_verify_time  = models.DateTimeField(auto_now_add=True, verbose_name='上次用于验证时间', help_text='上次用于验证时间')
    remark      = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_wx_dyh'
        verbose_name='订阅号'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{n}".format(n = self.dyh_nicname if len(self.dyh_nicname) > 0 else self.dyh_account)

class WXUser(models.Model):
    """
    微信用户
    """
    id = models.AutoField(primary_key=True)
    wx_dyh   = models.ForeignKey(WXDingYueHao, to_field='dyh_appid', verbose_name='订阅公众号',help_text='被关注的订阅号', on_delete=models.CASCADE)
    wx_openid = models.CharField(max_length=64, unique=True, verbose_name='用户微信帐号OpenID',help_text='微信回调中的用户帐号OpenID---腾讯对微信名加密后的ID')
    disable   = models.BooleanField(default=False, verbose_name='禁用该号', help_text='禁用该号,加入黑名单')
    enable_ai  = models.BooleanField(default=False, verbose_name='启用AI对话', help_text='启用后该微信号发的可以通过AI答复')
    always_ai  = models.BooleanField(default=False, verbose_name='全AI对话', help_text='启用后该微信号发的所有消息AI答复')
    vav        = models.BooleanField(default=False, verbose_name='语音问语音答', help_text='如果用户语音发问，则语音回答')
    always_voice = models.BooleanField(default=False, verbose_name='尽可能语音回复', help_text='各种回复消息，尽可能用语音回复')
    voice_lang  = models.CharField(max_length=32, default="CN", verbose_name='语音的语言类型', help_text='语言类型 - 中英，默认中')
    voice_gender  = models.PositiveIntegerField(default=0, verbose_name='语音性别', help_text='语音回答时有效, 0-女性，1-男性')
    voice_idx  = models.PositiveIntegerField(default=0, verbose_name='语音者序号', help_text='语音回答时有效，使用选中性别里的第几个位语音回复')
    prompt     = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='用户独有 prompt',help_text='支持用户定义prompt，对AI进行引导')
    img_prompt = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='img prompt',help_text='支持用户针对图片处理自定义prompt，对AI进行特殊引导')
    pdf_prompt = models.TextField(max_length=4096, unique=False, default='', null=True, blank=True, verbose_name='pdf prompt',help_text='支持用户针对pdf文件处理自定义prompt，对AI进行特殊引导')
    use_ai_times= models.PositiveIntegerField(default=0, verbose_name='使用AI次数',help_text='用于检查单用户次数限制 - 使用公共资源时')
    wx_nicname= models.CharField(max_length=64, verbose_name='微信名称',help_text='用户的微信名称-便于人识别')
    join_time= models.DateTimeField(auto_now_add=True, verbose_name='首次关注时间', help_text='首次关注时间')
    remark      = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_wx_user'
        unique_together = ('wx_dyh', 'wx_openid')
        verbose_name='微信用户'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{d}-{n}[id:{i}]".format(i=self.id, d=self.wx_dyh, n = self.wx_nicname if len(self.wx_nicname.strip()) > 0 else self.wx_openid[:3] + "..." + self.wx_openid[-3:])

    def is_manager(self):
        mgr = WXDyhMgr.objects.filter(wx_user=self, is_active=True)
        return mgr and mgr.count() > 0

    def change_settings(self, settings):
        if not isinstance(settings, dict):
            return


        if int(settings.get('switch_voice', 0)):
            self.voice_idx += 1

        # rsp_fmt = int(settings.get('rsp_fmt', 1))
        # if rsp_fmt == 1:
        #     self.vav = 0
        # elif rsp_fmt == 2:
        #     self.vav = 1

        logger.info("User {u} change setting: {s}.".format(u=self, s=settings))
        self.save()

class WXDyhMgr(models.Model):
    """
    订阅号管理员
    """
    id = models.AutoField(primary_key=True)
    wx_user  = models.OneToOneField(WXUser, on_delete=models.CASCADE, to_field="wx_openid", verbose_name='订阅用户',help_text='微信用户')
    is_active= models.BooleanField(default=True, verbose_name='状态', help_text='状态-是否有效')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='首添时间')
    remark      = models.TextField(default='', null=True, blank=True, max_length=1024, verbose_name='备注',help_text='备注，补充说明情况')
    class Meta:
        db_table = 't_wx_dyh_mgr'
        verbose_name='订阅号管理员'
        verbose_name_plural = verbose_name
        ordering = ['id', ]
    def __str__(self):
        return "{u}".format(u = self.wx_user)

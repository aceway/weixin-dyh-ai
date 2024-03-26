USE DB_DYH;
SET NAMES 'utf8';
-- t_ai_vender t_ai_model_type t_ai_model
-- MySQL dump 10.14  Distrib 5.5.68-MariaDB, for Linux (x86_64)
--
-- Host: 10.0.4.8    Database: DB_DYH
-- ------------------------------------------------------
-- Server version	5.7.18-cynos-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `t_ai_vender`
--

DROP TABLE IF EXISTS `t_ai_vender`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_ai_vender` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tag` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `office_site` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_site` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `add_time` datetime(6) NOT NULL,
  `remark` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag` (`tag`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ai_vender`
--

LOCK TABLES `t_ai_vender` WRITE;
/*!40000 ALTER TABLE `t_ai_vender` DISABLE KEYS */;
INSERT INTO `t_ai_vender` VALUES (1,'阿里云','ali',1,'https://aliyu.com/','https://dashscope.console.aliyun.com/overview','2024-02-28 08:24:16.890611',''),(2,'腾讯','tencent',1,'https://ai.tencent.com/ailab/zh/index','-','2024-02-28 08:25:25.739019',''),(3,'月之暗面','kimi',1,'https://www.moonshot.cn/','https://kimi.moonshot.cn/','2024-03-19 02:18:54.601130','');
/*!40000 ALTER TABLE `t_ai_vender` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ai_model_type`
--

DROP TABLE IF EXISTS `t_ai_model_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_ai_model_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tag` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `used_times` int(10) unsigned NOT NULL,
  `add_time` datetime(6) NOT NULL,
  `remark` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag` (`tag`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ai_model_type`
--

LOCK TABLES `t_ai_model_type` WRITE;
/*!40000 ALTER TABLE `t_ai_model_type` DISABLE KEYS */;
INSERT INTO `t_ai_model_type` VALUES (1,'文生文','txt2txt',249,'2024-02-28 08:31:46.964544',''),(2,'文生图','txt2img',51,'2024-02-28 08:31:59.635446',''),(3,'图生文','img2txt',55,'2024-02-28 08:32:15.530557',''),(4,'文生代码','txt2code',1,'2024-02-28 08:32:38.824485',''),(5,'文转声','txt2voice',143,'2024-03-02 11:16:08.230624',''),(6,'语音生文','voice2txt',50,'2024-03-19 03:08:02.145389','语音识别');
/*!40000 ALTER TABLE `t_ai_model_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ai_model`
--

DROP TABLE IF EXISTS `t_ai_model`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_ai_model` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `vender_id` int(11) NOT NULL,
  `the_type_id` int(11) NOT NULL,
  `tag` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `prompt` longtext COLLATE utf8mb4_unicode_ci,
  `URL` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `doc_url` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `config_json` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `used_times` int(10) unsigned NOT NULL,
  `add_time` datetime(6) NOT NULL,
  `remark` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ai_model_vender_id_tag_type_06a19797_uniq` (`vender_id`,`tag`,`the_type_id`),
  KEY `t_ai_model_the_type_id_2b21dcdb_fk_t_ai_model_type_id` (`the_type_id`),
  CONSTRAINT `t_ai_model_the_type_id_2b21dcdb_fk_t_ai_model_type_id` FOREIGN KEY (`the_type_id`) REFERENCES `t_ai_model_type` (`id`),
  CONSTRAINT `t_ai_model_vender_id_b35c5d75_fk_t_ai_vender_id` FOREIGN KEY (`vender_id`) REFERENCES `t_ai_vender` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ai_model`
--

LOCK TABLES `t_ai_model` WRITE;
/*!40000 ALTER TABLE `t_ai_model` DISABLE KEYS */;
INSERT INTO `t_ai_model` VALUES (1,1,1,'qwen1.5-72b-chat','千问1.5-72B-chat',1,'回答问题遵纪守法，文明礼貌，拒绝回答黄赌毒，暴力等问题。','SDK','-','{}',215,'2024-02-28 08:33:35.198478',''),(2,1,2,'wanx-v1','万象V1',1,'画图遵纪守法，文明礼貌，拒绝绘制黄赌毒，暴力内容。','SDK','-','{}',51,'2024-02-28 08:34:30.399014',''),(3,1,3,'qwen-vl-chat-v1','千问识图',1,'','SDK','-','{}',0,'2024-02-28 08:35:01.617497',''),(4,1,4,'qwen-turbo','文生代码',1,'','SDK','-','{}',1,'2024-02-28 08:35:28.075925',''),(5,1,3,'qwen-vl-plus','千问识图Plus',1,NULL,'SDK','-','{}',55,'2024-02-28 08:35:55.870019',''),(6,1,5,'sambert','阿里Sambert人声',1,NULL,'SDK','https://help.aliyun.com/zh/dashscope/developer-reference/api-details-14?spm=a2c4g.11186623.0.0.52c5490evR4ez5','{\r\n  \"model\":\"sambert-zhichu-v1\",\r\n  \"sample_rate\": 48000,\r\n  \"volume\": 50,\r\n  \"rate\": 1.0,\r\n  \"pitch\": 1.0\r\n}',143,'2024-03-02 10:22:58.564538',''),(7,2,1,'tencent-hunyuan-chatstd','混元大模型标准版',1,'','sdk','https://cloud.tencent.com/document/api/1729/101836','{}',0,'2024-03-19 02:17:07.292833',''),(8,2,1,'tencent-hunyuan-chatpro','混元大模型高级版',1,'','sdk','https://cloud.tencent.com/document/api/1729/101837','{}',11,'2024-03-19 02:17:53.195263',''),(9,3,1,'moonshot-v1-8k','moonshotV1-8K',1,'','https://api.moonshot.cn/v1','https://platform.moonshot.cn/docs/api-reference#python-%E8%B0%83%E7%94%A8%E6%96%B9%E6%B3%95','{}',0,'2024-03-19 02:20:10.300908',''),(10,3,1,'moonshot-v1-32k','moonshotV1-32K',1,'','https://api.moonshot.cn/v1','https://platform.moonshot.cn/docs/api-reference#python-%E8%B0%83%E7%94%A8%E6%96%B9%E6%B3%95','{}',0,'2024-03-19 02:20:54.100259',''),(11,3,1,'moonshot-v1-128k','moonshotV1-128K',1,'','https://api.moonshot.cn/v1','https://platform.moonshot.cn/docs/api-reference#python-%E8%B0%83%E7%94%A8%E6%96%B9%E6%B3%95','{}',23,'2024-03-19 02:21:33.425523',''),(12,1,6,'ali-voice-one-sentence','一句话语音识别',1,'','https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr','https://help.aliyun.com/document_detail/374321.html?spm=a2c4g.84442.0.0.7d88648e7I3ypm','{\r\n    \"AppId\": \"Your AppId\",\r\n    \"AppKey\": \"Your App Key\",\r\n    \"EndPoint\": \"https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr\",\r\n   \"SampleRate\": 16000\r\n}',0,'2024-03-19 03:11:25.764290','\"\"\"\r\n外网访问（默认上海地域）\r\n上海：https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr\r\n北京：https://nls-gateway-cn-beijing.aliyuncs.com/stream/v1/asr\r\n深圳：https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/asr\r\n\r\n内网访问\r\n上海：ws://nls-gateway-cn-shanghai-internal.aliyuncs.com:80/ws/v1\r\n北京：ws://nls-gateway-cn-beijing-internal.aliyuncs.com:80/ws/v1\r\n深圳：ws://nls-gateway-cn-shenzhen-internal.aliyuncs.com:80/ws/v1'),(13,2,6,'tencent-voice-one-sentence','一句话语音识别',1,'','sdk','https://cloud.tencent.com/document/product/1093/35646','{\r\n  \"AppId\": \"Your App ID\",\r\n  \"AppKey\": \"Your App Key\",\r\n  \"EndPoint\": \"asr.tencentcloudapi.com\",\r\n  \"Region\" : \"ap-guangzhou\",\r\n  \"EngSerViceType\": \"16k_zh\"\r\n}',1,'2024-03-19 03:13:47.450932','#\"EngSerViceType\": \"16k_ca\", # 8k_zh：中文电话通用； 8k_en：英文电话通用； 16k_zh：中文通用；16k_zh-PY：中英粤;16k_en：英语； 16k_zh_medical：中文医疗；16k_zh_dialect：多方言，支持23种方言\r\n\r\n# 识别音频的音频格式，支持wav、pcm、ogg-opus、speex、silk、mp3、m4a、aac、amr。 示例值：wav'),(14,1,6,'paraformer-v1','Paraformer语音识别',1,'','sdk','https://help.aliyun.com/zh/dashscope/developer-reference/quick-start-7?disableWebsiteRedirect=true','{}',0,'2024-03-21 07:48:14.545885','Paraformer中英文语音识别模型，支持16kHz及以上采样率的音频或视频语音识别。'),(15,1,6,'paraformer-8k-v1','Paraformer语音识别8K',1,'','sdk','https://help.aliyun.com/zh/dashscope/developer-reference/quick-start-7?disableWebsiteRedirect=true','{}',49,'2024-03-21 07:48:50.512293','Paraformer中文语音识别模型，支持8kHz电话语音识别。'),(16,1,6,'paraformer-mtl-v1','Paraformer语音识别Multi',1,'','sdk','https://help.aliyun.com/zh/dashscope/api-reference-1','{}',0,'2024-03-21 07:49:33.200003','Paraformer多语言语音识别模型，支持16kHz及以上采样率的音频或视频语音识别。\r\n\r\n支持的语种/方言包括：中文普通话、中文方言（粤语、吴语、闽南语、东北话、甘肃话、贵州话、河南话、湖北话、湖南话、宁夏话、山西话、陕西话、山东话、四川话、天津话）、英语、日语、韩语、西班牙语、印尼语、法语、德语、意大利语、马来语。'),(17,1,1,'qwen-turbo','问答Turbo',1,'','sdk','-','{}',0,'2024-03-21 11:10:15.721988','');
/*!40000 ALTER TABLE `t_ai_model` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-25 19:02:18

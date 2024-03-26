6, 2024-03-24
alter table t_wx_user add column img_prompt longtext COLLATE utf8mb4_unicode_ci after prompt;
alter table t_wx_user add column pdf_prompt longtext COLLATE utf8mb4_unicode_ci after img_prompt;

5, 2024-03-17
alter table t_wx_dyh add column welcome longtext COLLATE utf8mb4_unicode_ci after prompt;

4, 2024-03-16
drop table t_ai_active_config_enable_models; drop table t_ai_dyh_config_enable_models; drop table t_ai_wx_config_enable_models;
drop table t_ai_active_config; drop table t_ai_dyh_config; drop table t_ai_wx_config;
重建表...

3, 2024-03-15
alter table t_wx_user add column voice_gender tinyint(1) NOT NULL DEFAULT '0' after vav;
alter table t_wx_user add column voice_lang varchar(32) NOT NULL DEFAULT 'CN' after vav;
alter table t_wx_user add column always_voice tinyint(1) NOT NULL DEFAULT 0 after vav;

2, 2024-03-13
alter table t_wx_user add column voice_idx tinyint(1) NOT NULL DEFAULT 0 after vav;

1, 2024-03-03
ALTER TABLE t_ai_model ADD COLUMN prompt LONGTEXT COLLATE utf8mb4_unicode_ci AFTER is_active;
ALTER TABLE t_ai_active_config ADD COLUMN prompt LONGTEXT COLLATE utf8mb4_unicode_ci AFTER `KEY`;
ALTER TABLE t_wx_dyh ADD COLUMN prompt LONGTEXT COLLATE utf8mb4_unicode_ci AFTER dyh_nicname;
ALTER TABLE t_wx_user ADD COLUMN prompt LONGTEXT COLLATE utf8mb4_unicode_ci AFTER vav;

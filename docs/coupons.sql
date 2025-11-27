-- AI 券码表结构，放置在 MySQL 中
-- 替换库名后执行：mysql -u user -p database < docs/coupons.sql

CREATE TABLE IF NOT EXISTS `ai_coupons` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(64) NOT NULL COMMENT '券码字符串',
  `status` ENUM('active','disabled') NOT NULL DEFAULT 'active',
  `usage_limit` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '最大可用次数',
  `usage_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已使用次数',
  `expires_at` DATETIME DEFAULT NULL COMMENT '过期时间，为空则长期有效',
  `notes` VARCHAR(255) DEFAULT NULL,
  `last_used_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 示例：插入一张可使用 20 次、30 天内有效的券码
-- INSERT INTO ai_coupons (code, usage_limit, expires_at, notes)
-- VALUES ('SPRITE-DEV-2025', 20, DATE_ADD(NOW(), INTERVAL 30 DAY), '测试券');

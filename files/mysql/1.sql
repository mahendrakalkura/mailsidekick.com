DROP TABLE IF EXISTS `administrators`;
CREATE TABLE IF NOT EXISTS `administrators` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `password` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `email` (`email`),
    KEY `password` (`password`),
    KEY `name` (`name`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `articles`;
CREATE TABLE IF NOT EXISTS `articles` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `type` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `title` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `contents` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `timestamp` DATETIME NOT NULL DEFAULT '0000-00-00 00:00:00',
    `sticky` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `type` (`type`),
    KEY `title` (`title`),
    KEY `timestamp` (`timestamp`),
    KEY `sticky` (`sticky`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `proxies`;
CREATE TABLE IF NOT EXISTS `proxies` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `protocol` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `hostname` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `port_number` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `username` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `password` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_name` (`user_id`, `name`),
    KEY `user_id` (`user_id`),
    KEY `name` (`name`),
    KEY `protocol` (`protocol`),
    KEY `hostname` (`hostname`),
    KEY `port_number` (`port_number`),
    KEY `username` (`username`),
    KEY `password` (`password`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `groups`;
CREATE TABLE IF NOT EXISTS `groups` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `blacklist` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `visibility` INT(11) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_name` (`user_id`, `name`),
    KEY `user_id` (`user_id`),
    KEY `name` (`name`),
    KEY `visibility` (`visibility`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `accounts`;
CREATE TABLE IF NOT EXISTS `accounts` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `group_id` int(11) NOT NULL,
    `proxy_id` INT(11) DEFAULT NULL,
    `description` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `blacklist` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `incoming_hostname` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `incoming_port_number` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `incoming_use_ssl` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `outgoing_hostname` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `outgoing_port_number` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `outgoing_use_ssl` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `outgoing_use_tls` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `username` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `password` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `connections` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_username` (`user_id`, `username`),
    KEY `user_id` (`user_id`),
    KEY `group_id` (`group_id`),
    KEY `proxy_id` (`proxy_id`),
    KEY `incoming_hostname` (`incoming_hostname`),
    KEY `incoming_port_number` (`incoming_port_number`),
    KEY `incoming_use_ssl` (`incoming_use_ssl`),
    KEY `outgoing_hostname` (`outgoing_hostname`),
    KEY `outgoing_port_number` (`outgoing_port_number`),
    KEY `outgoing_use_ssl` (`outgoing_use_ssl`),
    KEY `outgoing_use_tls` (`outgoing_use_tls`),
    KEY `username` (`username`),
    KEY `password` (`password`),
    KEY `connections` (`connections`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `variables`;
CREATE TABLE IF NOT EXISTS `variables` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `key` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `value` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_key` (`user_id`, `key`),
    KEY `user_id` (`user_id`),
    KEY `key` (`key`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `templates`;
CREATE TABLE IF NOT EXISTS `templates` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `cc` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `bcc` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `subject` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `bodies_plain_text` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `bodies_html` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_name` (`user_id`, `name`),
    KEY `user_id` (`user_id`),
    KEY `name` (`name`),
    KEY `cc` (`cc`),
    KEY `bcc` (`bcc`),
    KEY `subject` (`subject`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `packs`;
CREATE TABLE IF NOT EXISTS `packs` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_name` (`user_id`, `name`),
    KEY `user_id` (`user_id`),
    KEY `name` (`name`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `filters`;
CREATE TABLE IF NOT EXISTS `filters` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT(20) UNSIGNED DEFAULT NULL,
    `pack_id` INT(11) NOT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `description` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `visibility` INT(11) NOT NULL DEFAULT 0,
    `schedule` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `conditions` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `steps` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `position` INT(11) NOT NULL DEFAULT 0,
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `user_id_name` (`user_id`, `name`),
    KEY `user_id` (`user_id`),
    KEY `pack_id` (`pack_id`),
    KEY `name` (`name`),
    KEY `visibility` (`visibility`),
    KEY `position` (`position`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `filters_accounts`;
CREATE TABLE IF NOT EXISTS `filters_accounts` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `filter_id` INT(11) NOT NULL,
    `account_id` INT(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `filter_id_account_id` (`filter_id`, `account_id`),
    KEY `filter_id` (`filter_id`),
    KEY `account_id` (`account_id`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `logs`;
CREATE TABLE IF NOT EXISTS `logs` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `account_id` INT(11) NOT NULL,
    `timestamp` DATETIME NOT NULL DEFAULT '0000-00-00 00:00:00',
    PRIMARY KEY (`id`),
    UNIQUE KEY `account_id_timestamp` (`account_id`, `timestamp`),
    KEY `account_id` (`account_id`),
    KEY `timestamp` (`timestamp`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `queues`;
CREATE TABLE IF NOT EXISTS `queues` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `template_id` INT(11) NOT NULL,
    `filter_id` INT(11) DEFAULT NULL,
    `log_id` INT(11) NOT NULL,
    `message_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `email` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `subject` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `body` LONGTEXT COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `step` INT(11) NOT NULL,
    `scheduled_at` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `delivered_at` datetime DEFAULT NULL DEFAULT '0000-00-00 00:00:00',
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `filter_id_log_id_message_id` (`filter_id`, `log_id`, `message_id`),
    KEY `template_id` (`template_id`),
    KEY `filter_id` (`filter_id`),
    KEY `log_id` (`log_id`),
    KEY `message_id` (`message_id`),
    KEY `name` (`name`),
    KEY `email` (`email`),
    KEY `subject` (`subject`),
    KEY `step` (`step`),
    KEY `scheduled_at` (`scheduled_at`),
    KEY `delivered_at` (`delivered_at`),
    KEY `status` (`status`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `codes`;
CREATE TABLE IF NOT EXISTS `codes` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `value` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `value` (`value`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `codes_templates`;
CREATE TABLE IF NOT EXISTS `codes_templates` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `code_id` INT(11) NOT NULL,
    `template_id` INT(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `code_id_template_id` (`code_id`, `template_id`),
    KEY `code_id` (`code_id`),
    KEY `template_id` (`template_id`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `codes_packs`;
CREATE TABLE IF NOT EXISTS `codes_packs` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `code_id` INT(11) NOT NULL,
    `pack_id` INT(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `code_id_pack_id` (`code_id`, `pack_id`),
    KEY `code_id` (`code_id`),
    KEY `pack_id` (`pack_id`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `codes_filters`;
CREATE TABLE IF NOT EXISTS `codes_filters` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `code_id` INT(11) NOT NULL,
    `filter_id` INT(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `code_id_filter_id` (`code_id`, `filter_id`),
    KEY `code_id` (`code_id`),
    KEY `filter_id` (`filter_id`)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=0;

ALTER TABLE `groups`
ADD CONSTRAINT `groups_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `accounts`
ADD CONSTRAINT `accounts_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `accounts`
ADD CONSTRAINT `accounts_group_id`
FOREIGN KEY (`group_id`)
REFERENCES `groups` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `accounts`
ADD CONSTRAINT `accounts_proxy_id`
FOREIGN KEY (`proxy_id`)
REFERENCES `proxies` (`ID`)
ON DELETE SET NULL
ON UPDATE CASCADE;

ALTER TABLE `proxies`
ADD CONSTRAINT `proxies_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `variables`
ADD CONSTRAINT `variables_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `templates`
ADD CONSTRAINT `templates_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `packs`
ADD CONSTRAINT `packs_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `filters`
ADD CONSTRAINT `filters_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `filters`
ADD CONSTRAINT `filters_pack_id`
FOREIGN KEY (`pack_id`)
REFERENCES `packs` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `filters_accounts`
ADD CONSTRAINT `filters_accounts_filter_id`
FOREIGN KEY (`filter_id`)
REFERENCES `filters` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `filters_accounts`
ADD CONSTRAINT `filters_accounts_account_id`
FOREIGN KEY (`account_id`)
REFERENCES `accounts` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `logs`
ADD CONSTRAINT `logs_account_id`
FOREIGN KEY (`account_id`)
REFERENCES `accounts` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `queues`
ADD CONSTRAINT `queues_template_id`
FOREIGN KEY (`template_id`)
REFERENCES `templates` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `queues`
ADD CONSTRAINT `queues_filter_id`
FOREIGN KEY (`filter_id`)
REFERENCES `filters` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `queues`
ADD CONSTRAINT `queues_log_id`
FOREIGN KEY (`log_id`)
REFERENCES `logs` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `wp_usermeta`
ADD CONSTRAINT `wp_usermeta_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `wp_groups_user_group`
ADD CONSTRAINT `wp_groups_user_group_user_id`
FOREIGN KEY (`user_id`)
REFERENCES `wp_users` (`ID`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `wp_groups_user_group`
ADD CONSTRAINT `wp_groups_user_group_group_id`
FOREIGN KEY (`group_id`)
REFERENCES `wp_groups_group` (`group_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_templates`
ADD CONSTRAINT `codes_templates_code_id`
FOREIGN KEY (`code_id`)
REFERENCES `codes` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_templates`
ADD CONSTRAINT `codes_templates_template_id`
FOREIGN KEY (`template_id`)
REFERENCES `templates` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_packs`
ADD CONSTRAINT `codes_packs_code_id`
FOREIGN KEY (`code_id`)
REFERENCES `codes` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_packs`
ADD CONSTRAINT `codes_packs_pack_id`
FOREIGN KEY (`pack_id`)
REFERENCES `packs` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_filters`
ADD CONSTRAINT `codes_filters_code_id`
FOREIGN KEY (`code_id`)
REFERENCES `codes` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE `codes_filters`
ADD CONSTRAINT `codes_filters_filter_id`
FOREIGN KEY (`filter_id`)
REFERENCES `filters` (`id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

CREATE TABLE `user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `account` varchar(50) NOT NULL,
  `name` varchar(20) NOT NULL DEFAULT '',
  `password` varchar(30) NOT NULL DEFAULT '',
  `birthday` varchar(20) NOT NULL DEFAULT '',
  `phone` varchar(16) NOT NULL,
  `address` varchar(100)  NOT NULL DEFAULT '',
  `post` varchar(8) NOT NULL DEFAULT '',
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `acct` (`account`),
  KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=UTF8;

CREATE TABLE `goods` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `goods_id` varchar(50) NOT NULL DEFAULT '',
  `goods_name` varchar(20) NOT NULL DEFAULT '',
  `owner_account` varchar(50) NOT NULL DEFAULT '',
  `buyer_account` varchar(50) NOT NULL DEFAULT '',
  `img_filename` varchar(50) NOT NULL DEFAULT '',
  `description` varchar(100) NOT NULL DEFAULT '',
  `goods_price` real NOT NULL DEFAULT 0.0,
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deal_time` timestamp NOT NULL DEFAULT 0,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `g_id` (`goods_id`),
  KEY `owner_acc` (`owner_account`),
  KEY `buyer_acc` (`buyer_account`),
  KEY `goods_stat` (`status`),
  KEY `byeracct_stat` (`status`,`buyer_account`)
)ENGINE=InnoDB DEFAULT CHARSET=UTF8;

#goods.status:0 正常，未被购买；1，正常，已被购买；2，被购买锁定，但未付款成功；3,状态未定义；9，已删除。

CREATE TABLE  `account`(
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `account` varchar(50) NOT NULL DEFAULT '',
  `balance` real NOT NULL DEFAULT 0.0,
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `acc` (`account`),
  KEY `acc_sta` (`account`,`status`)
)ENGINE=InnoDB DEFAULT CHARSET=UTF8;

#account.status:0,正常；1，账户锁定；9，账户注销

CREATE TABLE `goodstag` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(20) NOT NULL DEFAULT '',
  `goods_id` varchar(50) NOT NULL DEFAULT '',
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,#0，状态正常；1，已删除。
  PRIMARY KEY (`id`),
  KEY `tagname` (`tag_name`),
  KEY `tag_sta` (`tag_name`,`status`),
  KEY `tag_goods` (`tag_name`,`goods_id`)
)ENGINE=InnoDB DEFAULT CHARSET=UTF8;

CREATE TABLE `dealorder` (
  `id` varchar(50) NOT NULL DEFAULT '',
  `goods_id` varchar(50) NOT NULL DEFAULT '',
  `buyer_account` varchar(50) NOT NULL DEFAULT '',
  `seller_account` varchar(50) NOT NULL DEFAULT '',
  `goods_price` real NOT NULL DEFAULT 0.0,
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `buyer_seller_acc` (`buyer_account`,`seller_account`),
  KEY `stat` (`status`)
)ENGINE=InnoDB DEFAULT CHARSET=UTF8;

CREATE TABLE `topuporder` (
  `id` varchar(50) NOT NULL DEFAULT '',
  `topup_account` varchar(50) NOT NULL DEFAULT '',
  `addup_amount` real NOT NULL DEFAULT 0.0,
  `mtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `stat` (`status`),
  KEY `topup_acc` (`topup_account`)
)ENGINE=InnoDB DEFAULT CHARSET=UTF8;
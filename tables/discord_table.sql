CREATE TABLE `discord` (
  `timestamp` timestamp NOT NULL,
  `user_id` bigint NOT NULL,
  `username` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `discriminator` smallint NOT NULL,
  `nick` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `message_id` bigint NOT NULL,
  `message_type` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `channel` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `content_edit` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `deleted` datetime DEFAULT NULL,
  `ref_id` bigint DEFAULT NULL,
  `thread_id` bigint DEFAULT NULL,
  `reactions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
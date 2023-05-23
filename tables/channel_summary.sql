CREATE TABLE `channel_summary_daily` (
  `date` date NOT NULL,
  `channel` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `message_count` int NOT NULL DEFAULT '0',
  `reaction_count` int NOT NULL DEFAULT '0',
  `unique_users` int NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE `channel_summary_monthly` (
  `date` date NOT NULL,
  `channel` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `message_count` int NOT NULL DEFAULT '0',
  `reaction_count` int NOT NULL DEFAULT '0',
  `unique_users` int NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE `channel_summary_weekly` (
  `date` date NOT NULL,
  `channel` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `message_count` int NOT NULL DEFAULT '0',
  `reaction_count` int NOT NULL DEFAULT '0',
  `unique_users` int NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
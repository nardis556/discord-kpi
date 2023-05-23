CREATE TABLE `followers` (
  `id` int NOT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  `user_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `in_server` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
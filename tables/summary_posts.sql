
CREATE TABLE summary_daily (
    date DATE,
    user_info varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    channel varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    posts INT,
    reactions INT,
    PRIMARY KEY(date, user_info, channel)
);

CREATE TABLE summary_weekly (
    date DATE,
    user_info varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    channel varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    posts INT,
    reactions INT,
    PRIMARY KEY(date, user_info, channel)
);

CREATE TABLE summary_monthly (
    date DATE,
    user_info varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    channel varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    posts INT,
    reactions INT,
    PRIMARY KEY(date, user_info, channel)
);

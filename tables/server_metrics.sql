CREATE TABLE server_metrics (
    timestamp TIMESTAMP,
    guild_id BIGINT,
    total_members INT,
    online_members INT,
    offline_members INT,
    num_roles INT,
    num_text_channels INT,
    num_voice_channels INT,
    num_categories INT,
    PRIMARY KEY (timestamp, guild_id)
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci;

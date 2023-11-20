import re
import time
from datetime import datetime, timedelta
from init import database_connector

def start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def parse_reactions(reactions_str):
    if reactions_str is None:
        return 0

    pairs = reactions_str.split(',')
    total_reactions = 0
    for pair in pairs:
        match = re.match(r".*:(\d+)", pair.strip())
        if match:
            total_reactions += int(match.group(1))
    return total_reactions

def weekly_channel_summary():
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute("SELECT MAX(date) FROM weekly_channel_summary")
    start_date = cursor.fetchone()[0]
    if start_date is None:
        cursor.execute("SELECT MIN(timestamp) FROM discord")
        start_date = cursor.fetchone()[0]
    else:
        start_date = start_date + timedelta(days=7)
    end_date = datetime.now()

    group_by_clause = "STR_TO_DATE(CONCAT(YEARWEEK(timestamp), ' Sunday'), '%X%V %W')"
    start_date = start_of_week(start_date)

    cursor.execute("SELECT DISTINCT channel FROM discord")
    all_channels = cursor.fetchall()

    for channel in all_channels:
        channel = channel[0]
        cursor.execute(f"""
            SELECT
                {group_by_clause},
                COUNT(message_id),
                GROUP_CONCAT(reactions SEPARATOR ',')
            FROM discord
            WHERE 
                timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
                AND channel = '{channel}'
            GROUP BY {group_by_clause}
        """)

        records = cursor.fetchall()
        for (summary_date, message_count, reaction_str) in records:
            reaction_count = parse_reactions(reaction_str)
            total_count = message_count + reaction_count
            cursor.execute(f"""
                INSERT INTO weekly_channel_summary (date, channel, total_count)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_count = VALUES(total_count)
            """, (summary_date, channel, total_count))
            db.commit()

    cursor.close()
    db.close()

weekly_channel_summary()

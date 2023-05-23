import re
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from init import discord_connector, database_connector

def start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def start_of_month(dt):
    return dt.replace(day=1)

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

def summarize_all_channels(interval):
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute(f"SELECT MAX(date) FROM channel_summary_{interval}")
    start_date = cursor.fetchone()[0]
    if start_date is None:
        cursor.execute(f"SELECT MIN(timestamp) FROM discord")
        start_date = cursor.fetchone()[0]
    else:
        if (datetime.now().date() - start_date).days < 7:
            start_date = datetime.now().date() - timedelta(days=7)
        else:
            start_date = start_date + relativedelta(days=1)
    end_date = datetime.now()
    if interval == 'daily':
        group_by_clause = "DATE(timestamp)"
    elif interval == 'weekly':
        start_date = start_of_week(start_date)
        group_by_clause = "STR_TO_DATE(CONCAT(YEARWEEK(timestamp), ' Sunday'), '%X%V %W')"
    elif interval == 'monthly':
        start_date = start_of_month(start_date)
        group_by_clause = "DATE_FORMAT(timestamp, '%Y-%m-01')"

    cursor.execute("SELECT DISTINCT channel FROM discord")
    all_channels = cursor.fetchall()

    for channel in all_channels:
        channel = channel[0]
        cursor.execute(f"""
            SELECT
                {group_by_clause},
                COUNT(*),
                COUNT(DISTINCT user_id),
                GROUP_CONCAT(reactions SEPARATOR ',')
            FROM discord
            WHERE 
                timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
                AND channel = '{channel}'
            GROUP BY {group_by_clause}
        """)

        records = cursor.fetchall()
        if not records:
            cursor.execute(f"""
            INSERT INTO channel_summary_{interval} (date, channel, message_count, reaction_count, unique_users)
            VALUES (%s, %s, 0, 0, 0)
            """, (start_date, channel))
            db.commit()
            continue

        for (summary_date, message_count, unique_users, reaction_str) in records:
            try:
                reaction_count = parse_reactions(reaction_str)
                cursor.execute(f"""
                INSERT INTO channel_summary_{interval} (date, channel, message_count, reaction_count, unique_users)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    message_count = VALUES(message_count),
                    reaction_count = VALUES(reaction_count),
                    unique_users = VALUES(unique_users)
                """, (summary_date, channel, message_count, reaction_count, unique_users))

                db.commit()

            except Exception as e:
                pass

    cursor.close()
    db.close()

summarize_all_channels('daily')
time.sleep(5)
summarize_all_channels('weekly')
time.sleep(5)
summarize_all_channels('monthly')

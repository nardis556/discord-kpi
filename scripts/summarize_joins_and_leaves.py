import re
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from init import discord_connector, database_connector

def start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def start_of_month(dt):
    return dt.replace(day=1)

def summarize_all_members(interval):
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute(f"SELECT MAX(date) FROM member_summary_{interval}")
    start_date = cursor.fetchone()[0]
    if start_date is None:
        cursor.execute(f"SELECT MIN(timestamp) FROM members")
        start_date = cursor.fetchone()[0]
    else:
        if interval == 'daily':
            start_date = start_date + timedelta(days=1)
        elif interval == 'weekly':
            start_date = start_of_week(start_date + timedelta(days=7))
        elif interval == 'monthly':
            start_date = start_of_month(start_date) + relativedelta(months=1)
    end_date = datetime.now()

    if interval == 'daily':
        group_by_clause = "DATE(timestamp)"
    elif interval == 'weekly':
        group_by_clause = "STR_TO_DATE(CONCAT(YEARWEEK(timestamp), ' Sunday'), '%X%V %W')"
    elif interval == 'monthly':
        group_by_clause = "DATE_FORMAT(timestamp, '%Y-%m-01')"

    cursor.execute(f"""
        SELECT
            {group_by_clause},
            SUM(CASE WHEN in_server = 1 THEN 1 ELSE 0 END) as joins,
            SUM(CASE WHEN in_server = 0 THEN 1 ELSE 0 END) as leaves
        FROM members
        WHERE 
            timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
        GROUP BY {group_by_clause}
    """)

    records = cursor.fetchall()

    for (summary_date, joins, leaves) in records:
        try:
            cursor.execute(f"""
            INSERT INTO member_summary_{interval} (date, joins, leaves)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                joins = VALUES(joins),
                leaves = VALUES(leaves)
            """, (summary_date, joins, leaves))

            db.commit()

        except Exception as e:
            pass

    cursor.close()
    db.close()

summarize_all_members('daily')
time.sleep(5)
summarize_all_members('weekly')
time.sleep(5)
summarize_all_members('monthly')

import re
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from init import database_connector
from time import sleep

def start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def start_of_month(dt):
    return dt.replace(day=1)

def update_summaries(interval):
    db = database_connector.connect()
    cursor = db.cursor()
    cursor.execute(f"SELECT MAX(timestamp) FROM discord")
    start_date = cursor.fetchone()[0]
    if start_date is None:
        cursor.execute(f"SELECT MIN(timestamp) FROM discord")
        start_date = cursor.fetchone()[0]
    else:
        if (datetime.now() - start_date).days < 7:
            start_date = datetime.now() - timedelta(days=7)
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

    query = f"""
        INSERT INTO summary_{interval} (date, user_info, channel, posts, reactions)
        SELECT 
            {group_by_clause} as date,
            CONCAT(user_id, ': ', username, '#', discriminator) as user_info,
            channel,
            COUNT(message_id) as posts,
            SUM((LENGTH(reactions) - LENGTH(REPLACE(reactions, ':', '')))) as reactions
        FROM discord
        WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY {group_by_clause}, CONCAT(user_id, ': ', username, '#', discriminator), channel
        ON DUPLICATE KEY UPDATE
        posts = VALUES(posts),
        reactions = VALUES(reactions)
    """

    cursor.execute(query)

    db.commit()
    cursor.close()

update_summaries('daily')
sleep(5)
update_summaries('weekly')
sleep(5)
update_summaries('monthly')

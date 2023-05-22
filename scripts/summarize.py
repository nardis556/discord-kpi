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
    pairs = reactions_str.split(',')
    total_reactions = 0
    for pair in pairs:
        match = re.match(r".*:(\d+)", pair.strip())
        if match:
            total_reactions += int(match.group(1))
    return total_reactions

def update_most_reacted_posts(interval):
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute(f"SELECT MAX(date) FROM most_reacted_posts_{interval}")
    start_date = cursor.fetchone()[0]

    cursor.execute(f"SELECT reactions FROM discord")
    reactions_str = cursor.fetchone()[0]

    reaction_count = parse_reactions(reactions_str)

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

    query = f"""
        INSERT INTO most_reacted_posts_{interval} (date, username, reaction_count, message_id)
        SELECT 
            {group_by_clause},
            CONCAT(user_id, ': ', username, ' ', discriminator),
            SUM({reaction_count}),  # use calculated reaction_count
            message_id
        FROM discord
        WHERE 
            timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
        GROUP BY {group_by_clause}, username, message_id
        ON DUPLICATE KEY UPDATE
            reaction_count = VALUES(reaction_count),
            message_id = VALUES(message_id)
    """

    cursor.execute(query)
    db.commit()
    cursor.close()
    db.close()

def update_total_reactions(interval):
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute(f"SELECT MAX(date) FROM total_reactions_{interval}")
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

    query = f"""
        INSERT INTO total_reactions_{interval} (date, username, reaction_count)
        SELECT 
            {group_by_clause},
            CONCAT(user_id, ': ', username, ' ', discriminator),
            SUM(reaction_count)
        FROM discord
        WHERE 
            timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
        GROUP BY {group_by_clause}, username
        ON DUPLICATE KEY UPDATE
            reaction_count = VALUES(reaction_count)
    """

    cursor.execute(query)
    db.commit()

    cursor.close()
    db.close()

def sum_emoji_reactions(interval):
    db = database_connector.connect()
    cursor = db.cursor()

    cursor.execute(f"SELECT MAX(date) FROM emoji_reactions_{interval}")
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

    query = f"""
        INSERT INTO emoji_reactions_{interval} (date, emoji, reaction_count)
        SELECT 
            {group_by_clause},
            emoji,
            SUM(reaction_count)
        FROM discord
        WHERE 
            timestamp BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
        GROUP BY {group_by_clause}, emoji
        ON DUPLICATE KEY UPDATE
            reaction_count = VALUES(reaction_count)
    """

    cursor.execute(query)
    db.commit()

    cursor.close()
    db.close()


update_most_reacted_posts('daily')
time.sleep(5)
update_most_reacted_posts('weekly')
time.sleep(5)
update_most_reacted_posts('monthly')
time.sleep(5)
update_total_reactions('daily')
time.sleep(5)
update_total_reactions('weekly')
time.sleep(5)
update_total_reactions('monthly')
time.sleep(5)
sum_emoji_reactions('daily')
time.sleep(5)
sum_emoji_reactions('weekly')
time.sleep(5)
sum_emoji_reactions('monthly')

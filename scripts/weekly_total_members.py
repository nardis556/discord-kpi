from datetime import datetime, timedelta
from init import database_connector

def start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def gather_weekly_total_members():
    db = database_connector.connect()
    cursor = db.cursor()
    
    cursor.execute("SELECT MAX(date) FROM weekly_total_members")
    start_date = cursor.fetchone()[0]
    if start_date is None:
        cursor.execute("SELECT MIN(timestamp) FROM server_metrics")
        start_date = cursor.fetchone()[0].date()
    else:
        start_date = start_of_week(start_date + timedelta(days=7))
    end_date = start_of_week(start_date + timedelta(days=7))

    while start_date < start_of_week(datetime.now()).date():

        select_query = f"""
            SELECT total_members
            FROM server_metrics
            WHERE DATE(timestamp) = '{start_date}'
            ORDER BY ABS(TIME(timestamp) - '00:00:00')
            LIMIT 1
        """
        
        cursor.execute(select_query)
        record = cursor.fetchone()

        if record:
            total_members_snapshot = record[0]
            
            insert_query = """
                INSERT INTO weekly_total_members (date, total_members)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (start_date, total_members_snapshot))
            db.commit()

            print(f"Week starting {start_date}, total members snapshot: {total_members_snapshot}")
        
        start_date = end_date
        end_date = start_of_week(start_date + timedelta(days=7))

    cursor.close()
    db.close()

if __name__ == "__main__":
    try:
        gather_weekly_total_members()
    except Exception as e:
        print(f"Error: {e}")

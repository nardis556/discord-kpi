from datetime import datetime
from init import database_connector

def create_new_table(db, channel_name):
    cursor = db.cursor()
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {channel_name} (
          `timestamp` timestamp NOT NULL,
          `user_id` bigint NOT NULL,
          `username` text NOT NULL,
          `discriminator` smallint NOT NULL,
          `nick` text,
          `message_id` bigint NOT NULL,
          `message_type` varchar(255),
          `channel` text,
          `content` text,
          `content_edit` text,
          `deleted` datetime,
          `ref_id` bigint,
          `thread_id` bigint,
          `reactions` text
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_table_query)
    cursor.close()

def insert_records_into_new_table(records, channel_name, cursor):
    insert_query = f"INSERT INTO `{channel_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    for record in records:
        cursor.execute(insert_query, record)

def gather_channel_data(channel_name):
    db = database_connector.connect()
    cursor = db.cursor()

    try:
        create_new_table(db, channel_name)

        cursor.execute(f"SELECT MAX(timestamp) FROM {channel_name}")
        last_entry_date = cursor.fetchone()[0]
        current_time = datetime.now()

        if last_entry_date is None:
            print(f"No previous data found in '{channel_name}'. Fetching all available records.")
            last_entry_date = datetime.min

        select_query = f"""
            SELECT *
            FROM discord
            WHERE channel = %s AND timestamp > '{last_entry_date}' AND timestamp <= '{current_time}'
        """
        cursor.execute(select_query, (channel_name,))
        records = cursor.fetchall()

        if records:
            print(f"Inserting {len(records)} new records into {channel_name}.")
            insert_records_into_new_table(records, channel_name, cursor)
        else:
            print("No new records found to insert.")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")

    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    channel_name = "📈┃trading"
    gather_channel_data(channel_name)

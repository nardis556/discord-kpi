from init import database_connector

class ChannelTableCreator:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def create_channel_tables(self):
        db = self.db_connector.connect()

        cursor = db.cursor()

        cursor.execute("SELECT DISTINCT channel FROM discord")

        channels = cursor.fetchall()

        for channel in channels:
            sanitized_channel = "".join(e for e in channel[0] if e.isalnum())

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS `{sanitized_channel}`
                LIKE discord
                """
            )

            cursor.execute(
                f"""
                INSERT INTO `{sanitized_channel}`
                SELECT * FROM discord
                WHERE channel = %s
                """, (channel[0],)
            )

        db.commit()
        cursor.close()
        db.close()


if __name__ == "__main__":
    table_creator = ChannelTableCreator(database_connector)
    table_creator.create_channel_tables()

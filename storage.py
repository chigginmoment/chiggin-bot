# Placeholder where I will later implement database storage.
import psycopg2
import constants


def db_connect():
    """Returns the connection object to database."""
    try:

        connection = psycopg2.connect(user=constants.DB_ID,
                                      password=constants.DB_PASS,
                                      database=constants.DB_NAME)

        print("Connection to database: ", constants.DB_NAME)

        return connection
    except (Exception, psycopg2) as error:
        print("Error in connecting to database: ", error)

# TODO: Add function DB INSERT
# TODO: Add function DB DELETE
# TODO: Add function DB MODIFY
# Do I want to store feedback in the server as well? I might.


def db_disconnect(connection):
    """Disconnects from database for clean exit."""

    if connection:
        connection.cursor.close()
        connection.close()
        print("Connection to ", constants.DB_NAME, " closed.")
# Man.



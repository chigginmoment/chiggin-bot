# Placeholder where I will later implement database storage.
import psycopg2
import constants


def connect_to_db():
    """Returns the connection object to database."""
    try:

        connection = psycopg2.connect(user=constants.DB_ID,
                                      password=constants.DB_PASS,
                                      database=constants.DB_NAME)

        print("Connection to database: ", constants.DB_NAME)

        return connection
    except (Exception, psycopg2) as error:
        print("Error in connecting to database: ", error)

# TODO: Add function INSERT SERVER
# TODO: Add function DELETE SERVER
# TODO: Add function MODIFY SERVER
# Do I want to store feedback in the server as well? I might.


def disconnect_from_db(connection):
    """Disconnects from database for clean exit."""

    if connection:
        connection.cursor.close()
        connection.close()
        print("Connection to ", constants.DB_NAME, " closed.")
# Man.



# Placeholder where I will later implement database storage.
from typing import Tuple

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
    except (Exception) as error:
        print("Error in connecting to database: ", error)


def db_startup(connection):
    """Returns all server_prefs as Dict{server_id, List[str]}"""
    cursor = connection.cursor()
    query = "SELECT * FROM server_prefs"
    cursor.execute(query)
    connection.commit()
    records = cursor.fetchall()
    return records


# TODO: Add function DB QUERY
def db_query(connection, query: str):
    """I have no idea how I'm going to do this."""
    cursor = connection.cursor()


# TODO: Add function DB INSERT
def db_insert(connection, server_id: str, channel_id: str, server_name: str, channel_name: str):
    """Inserts a new server entry into connected database. Inserts only the data provided in the argument."""
    pass


# TODO: Add function DB DELETE
def db_delete(connection, server_id: str, channel_id: str):
    """Deletes the entry with server id = server_id from database."""
    pass


# TODO: Add function DB MODIFY
def db_modify_channel(connection, server_id: str, channel_id: str, channel_name: str):
    """If there exists a server_id with a different channel_id, modifies the channel_id and sets channel_name to the
    channel_name provided."""
    pass


# Do I want to store feedback in the server as well? I might.
def db_modify_preference(connection, server_id: str, preference_name: str, value: int):
    """Modifies the preference provided for the server that has server_id."""
    pass


def db_disconnect(connection):
    """Disconnects from database for clean exit."""

    if connection:
        connection.cursor().close()  # causes an error.
        connection.close()
        print("Connection to ", constants.DB_NAME, " closed.")
# Man.



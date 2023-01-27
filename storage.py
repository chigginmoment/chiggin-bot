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


def db_update(connection):
    """Returns all server_prefs as a list of rows where each row is a tuple"""
    # print("This works")
    cursor = connection.cursor()
    query = "SELECT * FROM server_prefs"
    cursor.execute(query)
    connection.commit()
    records = cursor.fetchall()
    return records

def db_update_map(connection):
    """Returns server_prefs as hashmap with key = server_id and value = List of preferences"""
    pref_map = {}
    cursor = connection.cursor()
    query = "SELECT * FROM server_prefs"
    cursor.execute(query)
    connection.commit()
    records = cursor.fetchall()
    for entry in records:
        pref_map[entry[0]] = entry[1:]

    return pref_map

def db_add_server(connection, server_id: str, server_name: str):
    """Adds entirely new server to database."""
    try:
        cursor = connection.cursor()
        query = "INSERT INTO server_prefs (server_id, server_name, no_chance) VALUES (%s, %s, FALSE)"
        cursor.execute(query, (server_id, server_name))
        connection.commit()
        print("Inserted new row into database.")

    except Exception as error:
        print("Error in inserting to database, ", error)
        connection.rollback()


def db_remove_server(connection, server_id: str):
    """Removes server from database."""
    try:
        cursor = connection.cursor()
        query = "DELETE FROM server_prefs WHERE server_id = %s"
        cursor.execute(query, (server_id,))
        connection.commit()
        print("Removed row from database.")

    except Exception as error:
        print("Error in removing from database, ", error)
        connection.rollback()


# TODO: Add function DB INSERT
def db_insert_channel(connection, server_id: str, channel_id: str, channel_name: str):
    """Inserts a new server entry into connected database. Inserts only the data provided in the argument."""
    try:
        cursor = connection.cursor()
        query = "UPDATE server_prefs SET channel = %s, channel_name = %s WHERE server_id = %s"
        cursor.execute(query, (channel_id, channel_name, server_id))
        connection.commit()
        print("Updated channel in database.")

    except Exception as error:
        print("Error inserting to database, ", error)
        connection.rollback()


# TODO: Add function DB DELETE
def db_delete_channel(connection, server_id: str):
    """Deletes the entry with server id = server_id from database."""
    try:
        cursor = connection.cursor()
        # print(server_id)
        query = "UPDATE server_prefs SET channel=NULL, channel_name=NULL WHERE server_id = %s"
        cursor.execute(query, (server_id,))
        connection.commit()
        print("Updated database record.")
    except Exception as error:
        print("Error updating database, ", error)
        connection.rollback()


def db_fetch_archive(connection, server_id: str):
    """Fetches archive channel of server with id server_id"""
    try:
        cursor = connection.cursor()
        query = "SELECT archive FROM server_prefs WHERE server_id = %s"
        cursor.execute(query, (server_id,))
        connection.commit()
        channel = cursor.fetchone()
        print("Fetched archive channel: ", channel[0])
        if not channel[0]:
            return -1
        return channel[0]
    except Exception as error:
        print("Error fetching archive channel, ", error)
        connection.rollback()


def db_archive(connection, server_id: str, archive: str):
    try:
        cursor = connection.cursor()
        query = "UPDATE server_prefs SET archive = %s WHERE server_id = %s"
        cursor.execute(query, (archive, server_id))
        connection.commit()
        print("Set new archive.")
    except Exception as error:
        print("Error in adding archive: ", error)
        connection.rollback()


def db_not_archive(connection, server_id: str):
    try:
        cursor = connection.cursor()
        query = "UPDATE server_prefs SET archive = NULL WHERE server_id = %s"
        cursor.execute(query, (server_id,))
        connection.commit()
        print("Unset archive.")
    except Exception as error:
        print("Error in unsetting: ", error)
        connection.rollback()


def db_nuisance(connection, server_id: str):
    try:
        cursor = connection.cursor()
        query = "UPDATE server_prefs SET no_chance = NOT no_chance WHERE server_id = %s"
        cursor.execute(query, (server_id,))
        connection.commit()
        print("Toggle nuisance.")
    except Exception as error:
        print("Error in toggling: ", error)
        connection.rollback()


def db_disconnect(connection):
    """Disconnects from database for clean exit."""

    if connection:
        connection.cursor().close()  # causes an error.
        connection.close()
        print("Connection to ", constants.DB_NAME, " closed.")
# Man.



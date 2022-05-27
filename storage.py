# Placeholder where I will later implement database storage.
import psycopg2
import constants


def connect_to_db():
    """Returns the connection object to database."""

    connection = psycopg2.connect(user=constants.DB_ID,
                                  password=constants.DB_PASS,
                                  database=constants.DB_NAME)

    return connection

# TODO: Add function INSERT SERVER
# TODO: Add function DELETE SERVER
# TODO: Add function MODIFY SERVER
# Do I want to store feedback in the server as well? I might.

# Man.



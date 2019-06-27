import os
import sys
import psycopg2

'''
@author Joseph Cox
@author John Cameron 
'''

def get_database_connection():
    try:
        database_url = os.environ['DATABASE_URL']
        connection = psycopg2.connect(database_url, sslmode='require')
        print(connection.get_dsn_parameters(), file=sys.stderr)
        return connection
    except (Exception, psycopg2.Error) as error:
        print('\033[93m' + ' * Error while connecting to PostgreSQL' + '\033[0m', error, file=sys.stderr)
        return None


def initialize_database(connection):
    print(' * Initializing database...', file=sys.stderr)
    try:
        cursor = connection.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS users ('
            'id serial PRIMARY KEY,'
            'email VARCHAR (255) UNIQUE NOT NULL,'
            'password VARCHAR (255) NOT NULL,'
            'admin BOOLEAN NOT NULL DEFAULT FALSE,'
            'email_verified BOOLEAN NOT NULL DEFAULT FALSE,'
            'csv_file TEXT)')

        # TODO - FOREIGN KEY
        # TODO - Determine token length
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS email_tokens ('
            'email VARCHAR (255) UNIQUE NOT NULL,'
            'token VARCHAR (255) NOT NULL)')

        connection.commit()  # Need to commit so that changes in db schema can be changed
        cursor.close()
        print(' * Initialization complete\n', file=sys.stderr)
    except (Exception, psycopg2.Error) as error:
        print('\033[93m' + ' * Error while connecting to PostgreSQL' + '\033[0m', error, file=sys.stderr)
        return None

import os
import sys
import psycopg2


def test_users_table():
    print(' * Testing database connection...', file=sys.stderr)
    try:
        print(type(os.environ["DATABASE_URL"]), file=sys.stderr)
        DATABASE_URL = os.environ['DATABASE_URL']
        CONNECTION = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = CONNECTION.cursor()
        print(' *' + CONNECTION.get_dsn_parameters() + '\n', file=sys.stderr)
        # check to se if the table exists with sql let the exception handler catch the error
        cursor.execute(('CREATE TABLE IF NOT EXISTS users (user_id serial PRIMARY KEY,' +
                        'username VARCHAR (50) UNIQUE NOT NULL,' +
                        ' password VARCHAR (50) NOT NULL,' +
                        'admin BOOLEAN NOT NULL DEFAULT FALSE,' +
                        'csv_file BYTEA)'))
        CONNECTION.commit()  # Need to commit so that changes in db schema can be changed
        return CONNECTION
    except (Exception, psycopg2.Error) as error:
        print('\033[93m'+' * Error while connecting to PostgreSQL' +
              '\033[0m', error, file=sys.stderr)
        return None
    print(' * Connection test is complete\n', file=sys.stderr)

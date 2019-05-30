import os

import psycopg2  # for databse connection
from flask import Flask, render_template, request

'''
class User:
    def __init__(self, username, password, account_id):
        self.username = username  # provided by the user 
        self.password = password  # provided by the user
        self.accountID = account_id  # this from the db table 
        '''


def table_exists(dbcon, tablename):
    dbcur = dbcon.cursor()
    dbcur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tablename.replace('\'', '\'\'')))
    if dbcur.fetchone()[0] == 1:
        dbcur.close()
        return True

    dbcur.close()
    return False


# database globals
try:
    DATABASE_URL = os.environ['DATABASE_URL']
    CONNECTION = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = CONNECTION.cursor()
    print(CONNECTION.get_dsn_parameters(), "\n")

    if not table_exists(CONNECTION, 'users'):
        cursor.execute("CREATE TABLE users (user_id serial PRIMARY KEY,"
                       " username VARCHAR (50) UNIQUE NOT NULL,"
                       " password VARCHAR (50) NOT NULL,"
                       " csv_file BYTEA)")
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/users/create', methods=['POST'])
def create_account():
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']

    cursor.execute("INSERT INTO users (username,password) VALUES(%s,%s) RETURNING user_id;", (username, password,))
    user_id = cursor.fetchone()[0]
    CONNECTION.commit()

    return user_id + "<br/>" + username + "</br>" + password


app.run(debug=False, host='0.0.0.0', port=os.environ.get("PORT", 5000))

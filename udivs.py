import hashlib, binascii, os
import psycopg2  # for databse connection
from flask import Flask, render_template, request

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


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

@app.route('/users/login', methods=['POST'])
def login():
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']
    cursor.execute("SELECT username, password, FROM users WHERE username = %s AND ") # NEED TO HASH PASS and COMPARE 

@app.route('/users/append', methods=['POST'])
def append_csv():
    request_data = request.get_jason()
    username = request_data['username']
    file = request_data['csv_file']
    cursor.execute("UPDATE users SET csv_file = %s WHERE username = %s",(file,username))
    return


app.run(debug=False, host='0.0.0.0', port=os.environ.get("PORT", 5000))

import hashlib, binascii, os  # for environment and hashing passwords
import psycopg2  # for data base connection
from flask import Flask, render_template, request,jsonify # for sending and receiving request to the server 
app = Flask(__name__) # create the flask application

def hash_password(password):
    '''Hash a password for storing.'''
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    '''Verify a stored password against one provided by user'''
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def table_exists(dbcon, tablename):
    ''' check if the table exists in the database '''
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


# database globals ensures that the database is connected 
try:
    DATABASE_URL = os.environ['DATABASE_URL']
    CONNECTION = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = CONNECTION.cursor()
    print(CONNECTION.get_dsn_parameters(), "\n")

    if not table_exists(CONNECTION, 'users'):
        cursor.execute("CREATE TABLE users (user_id serial PRIMARY KEY,"
                       " username VARCHAR (50) UNIQUE NOT NULL,"
                       " password VARCHAR (50) NOT NULL,"
                        "admin BOOLEAN NOT NULL DEFAULT FALSE,"
                       " csv_file BYTEA)")

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)




@app.route('/')
def index():
    ''' Return the index html from the templates page'''
    return render_template('index.html')


#********************** Users for the mobile appp **********************************#

# TODO: route to create a new user account and store it in the databse 
@app.route('/users/create', methods=['POST'])
def create_account():
    ''' Create a user account at user/create endpoint'''
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']
    cursor = CONNECTION.cursor()
    cursor.execute("INSERT INTO users (username,password) VALUES(%s,%s) RETURNING user_id;", (username, password,))
    user_id = cursor.fetchone()[0]
    CONNECTION.commit()
    return user_id + "<br/>" + username + "</br>" + password

#TODO: verify the user 
@app.route('/users/login', methods=['POST'])
def login():
    ''' Method to verify login creditions at route /users/login'''
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']
    db_pass = cursor.execute("SELECT password FROM users WHERE username = %s",(username))
    if verify_password(stored_password=db_pass,provided_password=password):
        cursor.execute("SELECT account_id FROM users WHERE username = %s", (username))
    return

@app.route('/user/csv', methods=['GET'])
def get_csv():
    ''' Get the csv file from the database at the route user/csv'''
    request_data = request.getjson()
    cursor.execute("SELECT csv_file FROM users WHERE username = %s",(request_data['username']))
    csv_file = cursor.fetchone()
    return jsonify({'csv_file':csv_file})

#TODO: append the csv_file that is being stored in the database 
@app.route('/users/csv/append', methods=['POST'])
def append_csv():
    ''' Access the csvfile in the database and append new info to it'''
    
    request_data = request.get_jason()
    username = request_data['username']
    file = request_data['csv_file']
    cursor.execute("UPDATE users SET csv_file = %s WHERE username = %s",(file,username))
    return

@app.route('/users/all')
def get_users():
    ''' Get all the users from the users table'''
    users = cursor.execute("SELECT users.name FROM users")
    return jsonify({"users":users})

#********************** Administrator Functions  for the Admin page **********************************#
@app.route('/admin/create',methods = ['POST'])
def create_admin():
    ''' Create a admin account at admin/create endpoint'''
    request_data = request.get_json()
    admin_name = request_data['admin_name']
    password = request_data['password']
    cursor.execute("INSERT INTO admin (admin_name,password) VALUES(%s,%s) RETURNING admin_id;", (admin_name, password,))
    admin_id = cursor.fetchone()[0]
    CONNECTION.commit()
    return admin_id + "<br/>" + admin_name + "</br>" + password

@app.route('/admin/login', methods=['POST'])
def admin_login():
    ''' Method to verify login creditions at route /admin/login'''
    request_data = request.get_json()
    admin_name = request_data['admin_name']
    password = request_data['password']
    db_pass = cursor.execute("SELECT password FROM users WHERE username = %s",(admin_name))
    if verify_password(stored_password=db_pass,provided_password=password):
        cursor.execute("SELECT admin_id FROM admin WHERE admin_name = %s", (admin_name))
    return render_template('admin.html')

@app.route('/admin/all' methods = ['GET'])
def get_admin():
    ''' get all the administrators from the admin table'''
    admin = cursor.execute("SELECT user.name from users WHERE admin = TRUE")
    return jsonify({"administrator":admin})

app.run(debug=False, host='0.0.0.0', port=os.environ.get("PORT", 5000)) # run the flask surver

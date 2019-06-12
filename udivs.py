# author: joseph cox
from flask import Flask, jsonify, render_template, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Resource, Api, reqparse
import hashlib
import binascii
import os  # for environment and hashing passwords
import psycopg2  # for data base connection

# database globals ensures that the database is connected
try:
    DATABASE_URL = os.environ['DATABASE_URL']
    CONNECTION = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = CONNECTION.cursor()
    print(CONNECTION.get_dsn_parameters(), "\n")
    if not table_exists(CONNECTION, 'users'):
        cursor.execute('CREATE TABLE users (user_id serial PRIMARY KEY, username VARCHAR (50) UNIQUE NOT NULL,password VARCHAR (50) NOT NULL,admin BOOLEAN NOT NULL DEFAULT FALSE,csv_file BYTEA)')
        CONNECTION.commit()
        cursor.close()
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)


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


def authenticate(username, password):
    ''' Authentication required to create a json web token object'''
    # you should find user in db here
    # you can see example in flask doc
    try:
        cursor = CONNECTION.cursor()
        # get the user by querying the database for the user
        cursor.execute(
            'SELECT users.username users.password FROM users WHERE users.username == %s' % username)
        # make sure that the user exists and that the passwords match
        username = cursor.fetchone()[0]
        user_password = cursor.fetchone()[1]
        if username and verify_password(user_password, password):
            # retrun the list of information that defines the user
            user = cursor.fetchone()
            cursor.close()
            return user
    except(Exception, psycopg2.Error) as error:
        print('Error while conntecting to the Postgres Database', error)
        return jsonify({'message': 'an error has occured see logs for more details', 'Error': error})


def identity(payload):
    ''' Identity function is needed to generate json web token '''
    # custom processing. the same as authenticate. see example in flask docs
    try:
        user_id = payload['identity']
        cursor = CONNECTION.cursor()
        cursor.execute(
            'SELECT users.id FROM users WHERE users.id == %d' % user_id)
        _id = cursor.fetchone()
        cursor.close()
        return _id
    except(Exception, psycopg2.Error) as error:
        print('Error while conntecting to the Postgres Database', error)
        return jsonify({'message': 'an error has occured see logs for more details', 'Error': error})


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


app = Flask(__name__)  # Create the flask app
api = Api(app)  # create the api
# generate a random 24 character set for the json web token for secure logins
app.config['SECRET_KEY'] = os.urandom(24)
# Json Web Token for security and refreshing
app.config.update(JWT=JWT(app, authenticate, identity))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/admin')
@jwt_required
def admin():
    return render_template('admin.html')


class Users(Resoruce):
    @jwt_required
    def get(self, username):
        '''Get all the attributes of one user row from the users table of the database'''
        try:
            # parser does data validation
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            request_data = parser.parse_args()
            username = request_data['username']
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE users.username == %s' % username)
            user_row = cursor.fetchone()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

        return jsonify({'user row': user_row, 'status': 200}) if user_row else jsonify({'message': 'check the logs for more details', 'Error': error})

    def post(self):
        ''' Create a user account at user/create endpoint'''
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            parser.add_argument('password', required=True,
                                type=str, help='password field is required')
            request_data = parser.parse_args(strict=True)
            username = request_data['username']
            password = hash_password(request_data['password'])
            cursor = CONNECTION.cursor()
            cursor.execute(
                'INSERT INTO users (username,password) VALUES(%s,%s) RETURNING user_id;' % (username, password,))
            user_id = cursor.fetchone()[0]
            CONNECTION.commit()
            cursor.close()
        except(Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'Check logs for more details', 'Error': error})
        # rerun status 200 if it worked
        return jsonify({'message': 'insert successful', 'status': 200})

    def put(self):  # not sure if we need a put
        pass

    @jwt.required
    def delete(self):
        ''' Remove a user account form the database'''
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='Username field is required')
            request_data = parser.parse_args(strict=True)
            username = request_data['username']
            cursor = CONNECTION.cursor()
            cursor.execute(
                'DELETE FROM users WHERE users.username ==%s' % username)
            CONNECTION.commit()
            cursor.close()
        except(Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'check the logs for more details', 'Error': error})
        # rerun status 200 if it worked
        return jsonify({'message': 'delete successful', 'status': 204})


class CSV(Resource):
    def get():
        ''' Get the csv file from the database at the route user/csv'''
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            request_data = parser.parse_args(strict=True)
            cursor.execute(
                "SELECT csv_file FROM users WHERE users.username == %s" % request_data['username'])
            csv_file = cursor.fetchone()
        except(Exception, psycopg2.Error)as error:
            print("Error while connecting to PostgreSQL", error)
        return jsonify({'csv_file': csv_file, 'status': 200}) if csv_file else jsonify({'message': 'check log for more details', 'status': 404})

    def post():  # not sure if we need post, the csv file should be created by default in the database
        pass

    # TODO not sure how to implements or if it is necessary
    def put():
        pass
    # TODO not sure how to implement or if it is necessary

    def delete():
        pass


class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True,
                            type=str, help='username field is required')
        parser.add_argument('password', required=True,
                            type=str, help=' password filed is required')
        request_data = parser.parse_args(strict=True)
        try:
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT users.username, users.password, FROM users WHERE users.username ==%s' % request_data['username'])
            user = cursor.fetchone()[0]
            password = cursor.fetchone()[1]
            request_password = request_data['password']
            cursor.close()
            if user and verify_password(password, request_password):
                return jsonify({'token': JWT, 'status': 200})
        except(Exception, psycopg2.error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'invalid credentials check the logs for more details', 'Error': error, 'status': 401})


class Admin_Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True,
                            type=str, help='user name is a required field')
        parser.add_argument('password', required=True,
                            type=str, help='password is a required field')
        request_data = parser.parse_args()
        try:
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT users.username,users.password,users.admin FROM users WHERE users.username == %s' % request_data['username'])
            user = cursor.fetchone()[0]
            password = cursor.fetchone()[1]
            admin = cursor.fetchone()[2]
            cursor.close()
            request_password = request_data['password']
            if admin and user and verify_password(password, request_password):
                return jsonify({'token': JWT, 'status': 200})
        except(Exception, psycopg2.error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'invalid credentials check the logs for more details', 'Error': error, 'status': 401})


api.add_resource(Admin_Login, '/admin/login')
api.add_resource(Users, '/users')
api.add_resource(CSV, '/users/csv')
api.add_resource(Login, '/users/login')
app.run(debug=False, host='0.0.0.0', port=os.environ.get(
    "PORT", 5000))  # run the flask server

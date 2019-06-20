"""@author: joseph cox"""
import os  # for environment and hashing passwords
import psycopg2  # for data base connection
from flask import Flask, jsonify, render_template
from flask_jwt import JWT, jwt_required
from flask_restful import Resource, Api, reqparse
# costum security functions from local security py
from security import hash_password, verify_password, authenticate, identity
from test import test_users_table
import sys
import sendgrid
from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail

app = Flask(__name__)  # Create the flask app
api = Api(app)  # create the api
# generate a random 24 character set for the json web token for secure logins
app.config['SECRET_KEY'] = os.urandom(24)
# Json Web Token for security and refreshing
app.config.update(JWT=JWT(app, authenticate, identity))


class Users(Resource):
    @jwt_required
    def get(self):
        """Get all the attributes of one user row from the users table of the database"""
        try:
            CONNECTION = test_users_table()
            # parser does data validation
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            request_data = parser.parse_args()
            username = request_data['username']
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE users.username == %s', (username))
            user_row = cursor.fetchone()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'check the logs for more details', 'Error': str(error)})
        return jsonify({'user row': user_row, 'status': 200})

    def post(self):
        """Create a user account at user/create endpoint"""
        try:
            CONNECTION = test_users_table()
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
                'INSERT INTO users (username,password) VALUES(%s,%s) RETURNING user_id;', (username, password))
            user_id = cursor.fetchone()[0]
            CONNECTION.commit()
            cursor.close()
        except(Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'Check logs for more details', 'Error': str(error), 'status': 500})
        # rerun status 200 if it worked
        return jsonify({'message': 'insert successful', 'status': 200})

    def put(self):  # not sure if we need a put
        pass

    @jwt_required
    def delete(self):
        """Remove a user account form the database"""
        try:
            CONNECTION = test_users_table()
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='Username field is required')
            request_data = parser.parse_args(strict=True)
            username = request_data['username']
            cursor = CONNECTION.cursor()
            cursor.execute(
                'DELETE FROM users WHERE users.username=%s;', username)
            CONNECTION.commit()
            cursor.close()
        except(Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'check the logs for more details', 'Error': str(error)})
        return jsonify({'message': 'delete successful', 'status': 204})


class CSV(Resource):
    @jwt_required
    def get(self):
        """Get the csv file from the database at the route user/csv"""
        try:
            CONNECTION = test_users_table()
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            request_data = parser.parse_args(strict=True)
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT csv_file FROM users WHERE users.username = %s;', request_data['username'])
            csv_file = cursor.fetchone()[0]
        except(Exception, psycopg2.Error)as error:
            print(' *Error while connecting to PostgreSQL',
                  error, file=sys.stderr)
            return jsonify({'message': 'An error has occurred check the logs for more details.', 'Error': str(error), 'status': 404})
        return jsonify({'csv_file': csv_file, 'status': 200})

    def put(self):
        """Every user starts with empty blob data in the table this function is to append to that blob data """
        try:
            CONNECTION = test_users_table()
            parser = reqparse.RequestParser()
            parser.add_argument('username', required=True,
                                type=str, help='username field is required')
            parser.add_argument('password', required=True,
                                type=str, help='password filed is required')
            parser.add_argument('csv_file', required=True,
                                type=str, help='Blob_Data is the csv data')
            request_data = parser.parse_args(strict=True)
            username = request_data['username']
            password = request_data['password']
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT users.username, users.password FROM users WHERE users.username=%s;', (username,))
            row = cursor.fetchone()
            user = row[0]
            password_db = row[1]
            if user and verify_password(password_db, password):
                csv_file = request_data['csv_file']
                cursor.execute(
                    'UPDATE users SET csv_file = %s WHERE users.username = %s;', (csv_file, username,))
                CONNECTION.commit()
                cursor.close()
        except(Exception, psycopg2.Error) as error:
            print(' *Error while connecting to PostgreSQL',
                  error, file=sys.stderr)
            return jsonify({'message': 'An error has occurred check the logs for more details.', 'Error': str(error), 'status': 404})
        return jsonify({'message': 'csv file has been updated ', 'status': 200})

    # TODO not sure how to implement or if it is necessary
    def delete(self):
        pass


class Login(Resource):
    """ Login is a resource for regular accounts to post to to login and varify their credentials"""

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True,
                            type=str, help='username field is required')
        parser.add_argument('password', required=True,
                            type=str, help=' password filed is required')
        request_data = parser.parse_args(strict=True)
        try:
            CONNECTION = test_users_table()
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT users.username, users.password, FROM users WHERE users.username ==%s' % request_data[
                    'username'])
            user = cursor.fetchone()[0]
            password = cursor.fetchone()[1]
            request_password = request_data['password']
            cursor.close()
            if user and verify_password(password, request_password):
                return jsonify({'token': JWT, 'status': 200})
        except(Exception, psycopg2.error) as error:
            print("Error while connecting to PostgreSQL", error, file=sys.stderr)
            return jsonify({'message': 'invalid credentials check the logs for more details', 'Error': str(error), 'status': 401})


class Admin_Login(Resource):
    """ This is a rest class for the admin html page. """

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True,
                            type=str, help='user name is a required field')
        parser.add_argument('password', required=True,
                            type=str, help='password is a required field')
        request_data = parser.parse_args()
        try:
            CONNECTION = test_users_table()
            cursor = CONNECTION.cursor()
            cursor.execute(
                'SELECT users.username,users.password,users.admin FROM users WHERE users.username == %s', request_data[
                    'username'])
            user = cursor.fetchone()[0]
            password = cursor.fetchone()[1]
            admin = cursor.fetchone()[2]
            cursor.close()
            request_password = request_data['password']
            if admin and user and verify_password(password, request_password):
                return jsonify({'token': JWT, 'status': 200})
        except(Exception, psycopg2.error) as error:
            print("Error while connecting to PostgreSQL", error)
            return jsonify({'message': 'invalid credentials check the logs for more details', 'Error': str(error), 'status': 401})


class Enrolment(Resource):
    def post(self):
        try:
            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            parser = reqparse.RequestParser()
            parser.add_argument('email', required=True,
                                type=str, help='email address is a required')
            parser.add_argument('phone', required=True,
                                type=str, help='phone number is required')
            request_data = parser.parse_args()
            message = Mail(from_email='UDIVS-team@UDIVS.com', to_emails=request_data['email'],
                           subject='Account Registration ', html_content='<strong>and easy to do anywhere, even with Python</strong>')
            response = sg.send(message)
            return jsonify({'message': 'email sent', 'status': str(response.status_code)})
        except(Exception, SendGridException) as error:
            return jsonify({'message': 'An error has occurred see the logs for more details', 'status': str(response.status_code), 'Error': str(error)})


# web pages
@app.route('/')
def home():
    return render_template('enroll.html')


@app.route('/admin')
@jwt_required()
def admin():
    return render_template('admin.html')


# API routes
api.add_resource(Admin_Login, '/admin/login')
api.add_resource(Users, '/users')
api.add_resource(CSV, '/users/csv')
api.add_resource(Login, '/users/login')
api.add_resource(Enrolment, '/enroll')

if __name__ == "__main__":
    test_users_table()
    # database globals ensures that the database is connected
    # flask prints to the std.error consol
    app.run(debug=False, host='0.0.0.0', port=os.environ.get(
        "PORT", 5000))  # run the flask server

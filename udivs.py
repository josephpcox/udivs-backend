'''
    @author: joseph cox
    @author: John cameron
    UDIVS REST API backend for the android application. 
'''
import logging
import os
import sys
import binascii
import json
import numpy
import pandas
import requests
import sendgrid
import boto3
from flask import Flask, jsonify, render_template, request
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from werkzeug.utils import secure_filename
from flask_restful import Api, reqparse
from sendgrid.helpers.mail import Mail
from database import *
from security import hash_password, verify_password, allowed_file
from questions import getOptions
app = Flask(__name__)  # Create the flask app

# logging configeration for error logs, print statements and debugging information
logging.basicConfig(handlers=[logging.StreamHandler()])
log = logging.getLogger('test')

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
jwt = JWTManager(app)
api = Api(app)  # create the api
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'


@app.route('/api/register', methods=['POST'])
def register():
    '''
        Sends out an automated email with a link for the user's email, the email and 
        the recaptcha are used to make sure automated scripts will not be able to flood 
        the database with fake users.
    '''
    parser = reqparse.RequestParser()
    parser.add_argument('first_name', required=True, type=str,
                        help='first name field is required')
    parser.add_argument('last_name', required=True, type=str,
                        help='email field is required')
    parser.add_argument('email', required=True, type=str,
                        help='email field is required')
    parser.add_argument('password', required=True, type=str,
                        help='password field is required')
    parser.add_argument('phone_number', required=True, type=str,
                        help='phone number field is required')
    parser.add_argument('g-recaptcha-response', required=True,
                        type=str, help='recaptcha response is missing')

    request_data = parser.parse_args(strict=True)

    recaptcha_response = request_data['g-recaptcha-response']
    email = request_data['email']  # TODO Validate email formatting
    password = hash_password(request_data['password'])

    recaptcha_server_response = requests.post('https://www.google.com/recaptcha/api/siteverify',
                                              {"secret": os.environ['RECAPTCHA_SECRET'],
                                               "response": recaptcha_response,
                                               "remoteip": request.remote_addr})

    if recaptcha_server_response.status_code == 200 and json.loads(recaptcha_server_response.content)["success"]:
        try:

            db_connection = get_database_connection()
            cursor = db_connection.cursor()
            cursor.execute(
                'INSERT INTO users (email,password) VALUES(%s,%s) RETURNING id;', (email, password))
            user_id = cursor.fetchone()[0]
        except psycopg2.errors.UniqueViolation:
            return jsonify({"msg": "email already registered"}), 409

        email_token = binascii.hexlify(os.urandom(20)).decode()
        cursor.execute(
            'INSERT INTO email_tokens (email,token) VALUES(%s,%s);', (email, email_token))

        db_connection.commit()
        cursor.close()
        db_connection.close()

        sg = sendgrid.SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
        message = Mail(from_email='UDIVS-team@UDIVS.com', to_emails=email,
                       subject='Verify your email address',
                       html_content='Please <a href="https://udivs.herokuapp.com/email_verify?token='
                                    + email_token + '">click here</a> to verify your email address')
        response = sg.send(message)

        print('Email sent with status ' + str(response.status_code))

        access_token = create_access_token(identity=user_id)
        return jsonify(token=access_token), 201

    else:
        return jsonify({"msg": "captcha is invalid"}), 400


# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route('/api/login', methods=['POST'])
def login():
    '''
        Since the system is just a simulation to see if a UDIVS system is feasible
        the genuine users will be required to login to the system to ensure tht good data is 
        being received for the correct rates.
    '''
    parser = reqparse.RequestParser()
    parser.add_argument('email', required=True, type=str,
                        help='email field is required')
    parser.add_argument('password', required=True, type=str,
                        help='password field is required')
    request_data = parser.parse_args(strict=True)

    email = request_data['email']        # TODO Validate email formatting
    password = request_data['password']

    print('email = ' + email)
    print('password = ' + password)

    db_connection = get_database_connection()
    cursor = db_connection.cursor()
    cursor.execute(
        'SELECT id,password FROM users WHERE email = (%s)', (email,))
    row = cursor.fetchone()

    if row is None:
        authenticated = False
    else:
        user_id = row[0]
        authenticated = verify_password(row[1], password)

    cursor.close()
    db_connection.close()

    if authenticated:
        # Identity can be any data that is json serializable
        access_token = create_access_token(identity=user_id)
        return jsonify(token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@app.route('/api/account', methods=['GET'])
@jwt_required
def details():
    '''
        Access the identity of the current user with get_jwt_identity
    '''
    user_id = get_jwt_identity()
    return jsonify(logged_in_as=user_id), 200


@app.route('/api/account/questions', methods=['GET'])
@jwt_required
def send_questions():
    user_id = get_jwt_identity()
    db_connection = get_database_connection()
    cursor = db_connection.cursor()
    cursor.execute('SELECT  id FROM users WHERE id = (%s)', (user_id,))
    row = cursor.fetchone()
    cursor.close()
    db_connection.close()

    if row is not None:
        s3 = boto3.client('s3')
        bucket_name = os.environ['S3_BUCKET']
        filename = row[0]
        s3 = boto3.resource('s3')
        file = s3.meta.client.download_file(
            bucket_name, filename, os.path.join(app.config['DOWNLOAD_FOLDER'], filename))
        parser = reqparse.RequestParser()
        data = pandas.read_csv(file)
        parser.add_argument('random_number', required=True,
                            help='enter in a random number for the get options function to return a correct answer, '
                                 'three incorect options, and a question string')
        request_data = parser.parse_args(strict=True)
        question, answer, options = getOptions(request_data['random_number'])

        return jsonify({"question": question,
                        "option 1": options[0],
                        "option 2": option[1],
                        "option 3": option[2],
                        "answer": answer
                        }), 200

    else:
        return 404


@app.route('/api/account/csv', methods=['POST'])
@jwt_required
def update_csv():
    '''
        Gets a csv data file from the client and stores it in a amazon s3 bucket. The 
        CSV file should contain all of the user device interaction data for one enrolled 
        user.
    '''
    user_id = get_jwt_identity()
    s3 = boto3.client('s3')
    file = request.files['file']
    # if user does not select file
    # submit an empty part without filename
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        bucket_name = os.environ['S3_BUCKET']
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_file)
        # Uploads the given file using a managed uploader, which will split up large
        # files automatically and upload parts in parallel.
        s3.upload_file(temp_file, bucket_name, filename)
        return jsonify({'message': 'File upload successful.'}), 201
    else:
        return jsonify({'message': 'File upload unsuccessful'}), 400


@app.route('/api/verify_email', methods=['POST'])
def verify_email():
    ''' 
        verifies that the user gave a good email and that the user exists
        once verified the user will be stored in the database and enrolled in 
        the UDIVS system.
    '''
    parser = reqparse.RequestParser()
    parser.add_argument('token', required=True, type=str,
                        help='token field is required')
    request_data = parser.parse_args(strict=True)

    token = request_data['token']

    db_connection = get_database_connection()
    cursor = db_connection.cursor()
    cursor.execute(
        'SELECT email FROM email_tokens WHERE token = (%s)', (token,))

    row = cursor.fetchone()
    cursor.close()

    if row is None:
        db_connection.close()
        return jsonify({"msg": "Invalid Token"}), 400
    else:
        cursor = db_connection.cursor()
        cursor.execute(
            'UPDATE users SET email_verified = TRUE WHERE email = (%s)', (row[0],))
        cursor.close()
        db_connection.close()
        return jsonify({"msg": "Email Verified"}), 200

# web pages


@app.route('/')
def home():
    return render_template('enroll.html')


@app.route('/email_verify')
def email_verify():
    return render_template('email_verify.html')


if __name__ == "__main__":
    # Initialize the database
    connection = get_database_connection()
    initialize_database(connection)
    connection.close()
    connection = None
    # database globals ensures that the database is connected
    # flask prints to the std.error console
    app.run(debug=False, host='0.0.0.0', port=os.environ.get(
        "PORT", 5000))  # run the flask server

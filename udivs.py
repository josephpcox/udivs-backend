"""@author: joseph cox
   @auhtor: John cameron
"""

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
app = Flask(__name__)  # Create the flask app

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
jwt = JWTManager(app)
api = Api(app)  # create the api
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route('/api/register', methods=['POST'])
def register():
    """Creates a new account"""
    parser = reqparse.RequestParser()
    parser.add_argument('email', required=True, type=str,
                        help='email field is required')
    parser.add_argument('password', required=True, type=str,
                        help='password field is required')
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
    # Access the identity of the current user with get_jwt_identity
    user_id = get_jwt_identity()
    return jsonify(logged_in_as=user_id), 200

# TODO: This will not work, the user should be dending us a csv file to this route and then we update it.
# requestdata gets put in a pandas dataframe, then from pd we put in into the database as a text file.


@app.route('/api/account/csv', methods=['GET'])
@jwt_required
def get_csv():
    user_id = get_jwt_identity()
    db_connection = get_database_connection()
    cursor = db_connection.cursor()
    cursor.execute('SELECT  FROM users WHERE id = (%s)', (user_id,))

    row = cursor.fetchone()

    cursor.close()
    db_connection.close()

    if row is not None:
        s3 = boto3.client('s3')
        bucket_name = os.environ['S3_BUCKET']
        filename = username

    else:
        return 204

# TODO This is going to need to be rewritten -------------------------------------------------------


@app.route('/api/account/csv', methods=['POST'])
# @jwt_required
def update_csv():
    # user_id = get_jwt_identity()
    s3 = boto3.client('s3')
    print('S3 OBJECT CREATED')
    file = request.files['file']
    print('FILE IS REQUEST.FILE DIC')
    # if user does not select file
    # submit an empty part without filename
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print('FILE HAS A SECURE FILE NAME')
        bucket_name = os.environ['S3_BUCKET']
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_file)
        print('BUCKET IS GRABED FROM THE SYS ENVIORON')
        # Uploads the given file using a managed uploader, which will split up large
        # files automatically and upload parts in parallel.
        s3.upload_file(filename, bucket_name, filename)
        print('file upload is complete')
        return jsonify({'message': 'File upload successful.'}), 201
    else:
        return jsonify({'message': 'File upload unsuccessful'}), 400


@app.route('/api/verify_email', methods=['POST'])
def verify_email():
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

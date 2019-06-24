"""@author: joseph cox"""

import binascii

import sendgrid
from flask import Flask, jsonify, render_template, request
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from flask_restful import Api, reqparse
from sendgrid.helpers.mail import Mail

from database import *
from security import hash_password, verify_password

app = Flask(__name__)  # Create the flask app

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'a4QLCQqHKeUWghw9ybcRgBtr'
jwt = JWTManager(app)

api = Api(app)  # create the api
connection = get_database_connection()


@app.route('/register', methods=['POST'])
def register():
    """Creates a new account"""
    parser = reqparse.RequestParser()
    parser.add_argument('email', required=True, type=str, help='email field is required')
    parser.add_argument('password', required=True, type=str, help='password field is required')
    request_data = parser.parse_args(strict=True)

    email = request_data['email']  # TODO Validate email formatting
    password = hash_password(request_data['password'])

    cursor = connection.cursor()
    cursor.execute('INSERT INTO users (email,password) VALUES(%s,%s) RETURNING user_id;', (email, password))
    user_id = cursor.fetchone()[0]

    email_token = binascii.hexlify(os.urandom(20)).decode()
    cursor.execute('INSERT INTO email_tokens (email,token) VALUES(%s,%s);', (email, email_token))

    connection.commit()
    cursor.close()

    sg = sendgrid.SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
    message = Mail(from_email='UDIVS-team@UDIVS.com', to_emails=email,
                   subject='Verify your email address',
                   html_content='Please <a href="https://udivs.herokuapp.com/email_verify?token='
                                + email_token + '">click here</a> to verify your email address')
    response = sg.send(message)

    print('Email sent with status ' + str(response.status_code))

    access_token = create_access_token(identity=user_id)
    return jsonify(token=access_token), 201


# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not email:
        return jsonify({"message": "Missing email parameter"}), 400
    if not password:
        return jsonify({"message": "Missing password parameter"}), 400

    cursor = connection.cursor()
    cursor.execute('SELECT user_id,password FROM users WHERE email = %s', email)
    row = cursor.fetchone()

    user_id = row[0]
    authenticated = verify_password(row[1], password)

    row.close()
    cursor.close()

    if authenticated:
        # Identity can be any data that is json serializable
        access_token = create_access_token(identity=user_id)
        return jsonify(token=access_token), 200
    else:
        return jsonify({"message": "Bad username or password"}), 401


@app.route('/account', methods=['GET'])
@jwt_required
def details():
    # Access the identity of the current user with get_jwt_identity
    user_id = get_jwt_identity()
    return jsonify(logged_in_as=user_id), 200

# web pages
@app.route('/')
def home():
    return render_template('enroll.html')

if __name__ == "__main__":
    # Initialize the database
    connection = get_database_connection()
    initialize_database(connection)
    connection.close()

    # database globals ensures that the database is connected
    # flask prints to the std.error console
    app.run(debug=False, host='0.0.0.0', port=os.environ.get("PORT", 5000))  # run the flask server

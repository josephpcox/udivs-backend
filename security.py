import hashlib
import binascii
import psycopg2
import os
import sys
from test import test_users_table


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
        CONNECTION = test_users_table()
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
        print('Error while conntecting to the Postgres Database',
              error, file=sys.stderr)


def identity(payload):
    ''' Identity function is needed to generate json web token '''
    # custom processing. the same as authenticate. see example in flask docs
    try:
        CONNECTION = test_users_table()
        user_id = payload['identity']
        cursor = CONNECTION.cursor()
        cursor.execute(
            'SELECT users.id FROM users WHERE users.id == %d' % user_id)
        _id = cursor.fetchone()
        cursor.close()
        return _id
    except(Exception, psycopg2.Error) as error:
        print('Error while conntecting to the Postgres Database',
              error, file=sys.stderr)

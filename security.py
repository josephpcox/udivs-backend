import binascii
import hashlib
import os

'''
@author Joseph Cox
@author John Cameron 
'''

ALLOWED_EXTENSIONS = {'txt', 'csv'}


# TODO Use bcrypt
def hash_password(password):
    '''
        Hash a password for storing into the database.
    '''
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    '''
        Verify a stored password against one provided by user
    '''
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def allowed_file(filename):
    '''
        function for checking file names and making sure they are allowed to be stored int the 
        UDIVS system.
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

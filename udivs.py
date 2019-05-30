import os
import psycopg2 # for databse connection 
from flask import Flask,render_template,jsonify


# database globals 
try:
    DATABASE_URL = os.environ['DATABASE_URL']
    CONNECTION = psycopg2.connect(DATABASE_URL, sslmode='require')
    CURSOR = CONNECTION.cursor()
    print(CONNECTION.get_dsn_parameters(),"\n")

except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)


class user:
    def __init__(self):
        self.username = username # provided by the user 
        self.password = password # provided by the user
        self.accountID= accountID #this from the db table 
    
    

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('hello.html')



app.run(debug=False, host='0.0.0.0', port=os.environ.get("PORT", 5000))

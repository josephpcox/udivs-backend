from flask import Flask,render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('hello.html')



app.run(debug=True,port=5000)
from flask import Flask,render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('hello.html')

app.run(debug=False, host='0.0.0.0', port=environ.get("PORT", 5000))

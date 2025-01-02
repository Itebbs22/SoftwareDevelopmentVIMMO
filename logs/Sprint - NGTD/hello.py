from flask import flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World'
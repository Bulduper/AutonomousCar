from logging import debug
from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO

app=Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def home():
    return render_template('index2.html')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)

@socketio.on('slider')
def handle_message(data):
    print('slider: ' + data)

if __name__ == "__main__":
    socketio.run(app,host="0.0.0.0",debug=True)
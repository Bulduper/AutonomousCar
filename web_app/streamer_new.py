from sys import argv
from flask import Flask, render_template, Response, request, json
from flask_socketio import SocketIO
from flask_socketio import send, emit
import time
import threading
import base64
import cv2

class HttpStreamer:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, logger=True, engineio_logger=True)
    lock = threading.Lock()
    frame = None
    data_to_send = dict()

    @app.route('/', methods=['GET','POST'])
    def index(self):
        return render_template('index.html')

    @app.route('/video1')
    def video_feed_1(self):
        return Response(self.makeFrame(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def makeFrame(self):
        while True:
            with self.lock:
                if self.frame is None:
                    continue
                (flag, encodedImage) = cv2.imencode(".jpg", self.frame)

                if not flag:
                    continue

            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                bytearray(encodedImage) + b'\r\n')

    def setFrame(self,img,scale=0.5):
        self.frame = cv2.resize(img,(round(img.shape[1]*scale), round(img.shape[0]*scale)))
        #with lock?

    def run(self):
        self.socketio.run(self.app,host='0.0.0.0',debug=True)
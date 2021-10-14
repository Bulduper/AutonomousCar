
from flask import Flask, render_template, Response
from g_pipeline import gstreamer_pipeline
import cv2

#starts flask server and starts processing camera frames

app=Flask(__name__)
cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

@app.route('/')
def index():
    return render_template('index.html')

def gen_frame():
    while cap:
        ret_val, img = cap.read()
        if ret_val:
            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, (426, 320))
            convert = cv2.imencode('.jpg', img)[1].tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + convert + b'\r\n')
    cap.release()


@app.route('/video')
def video_feed():
    return Response(gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)

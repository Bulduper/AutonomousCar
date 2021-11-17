from cv2 import cubeRoot
import jetson.inference
import jetson.utils

global cur_img

##REMEMBER TO  ENSURE GOOD COLOR FORMAT (RGB/RGBA)!!!


def init():
    global net
    net = jetson.inference.detectNet(argv=["--model=./ssd-mobilenet.onnx", "--labels=./labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=0.2)

def detectSigns(cuda_img):
    global cur_img
    cur_img = cuda_img

def networkLoop():
    detections= net.Detect(cur_img)
    for detect in detections:
        ID = detect.ClassID
        item=net.GetClassDesc(ID)
        print(item)


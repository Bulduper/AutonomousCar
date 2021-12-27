import jetson.inference
import numpy as np

frameGPU_bgr_small_detection = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')

working = False

def init():
     global net
     net = jetson.inference.detectNet(argv=["--model=./networks/ssd-mobilenet.onnx", "--labels=./networks/labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=0.2)


def detectSigns(cuda_img):
    global net, working
    detections= net.Detect(cuda_img,cuda_img.width,cuda_img.height)
    jetson.utils.cudaConvertColor(cuda_img, frameGPU_bgr_small_detection)
    working = True
    for detect in detections:
        ID = detect.ClassID
        item=net.GetClassDesc(ID)
        print(item)

def getVisual():
    # if working:
    #     return jetson.utils.cudaToNumpy(frameGPU_bgr_small_detection)
    return np.zeros((480,640,3),dtype=np.uint8)
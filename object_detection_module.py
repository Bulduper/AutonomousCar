import jetson.inference
import numpy as np

# frameGPU_bgr_small_detection = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameGPU_bgr_small_detection = jetson.utils.cudaAllocMapped(width=int(1640*0.6), height=int(1232*0.2), format='bgr8')
# frameGPU_bgr_small_detection = jetson.utils.cudaAllocMapped(width=int(1640*1), height=int(1232*1), format='bgr8')
MODEL_PATH = './networks/signs_raw_v0_4.onnx'
# MODEL_PATH = './networks/model4_raw_only_2000s_ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.onnx'
THRESHOLD = 0.6

working = False

def init():
    global net,working
    net = jetson.inference.detectNet(argv=["--model={}".format(MODEL_PATH), "--labels=./networks/labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=THRESHOLD)
    working = True

def detectSigns(cuda_img):
    if not working:
        init()
    global net
    detections = net.Detect(cuda_img,cuda_img.width,cuda_img.height)
    jetson.utils.cudaConvertColor(cuda_img, frameGPU_bgr_small_detection)
    for detect in detections:
        ID = detect.ClassID
        item=getClassName(ID)
        print(item)
    return detections

def getClassName(classID:int):
    global net
    return net.GetClassDesc(classID)

def getVisual():
    if working:
        return jetson.utils.cudaToNumpy(frameGPU_bgr_small_detection)
    return np.zeros((480,640,3),dtype=np.uint8)

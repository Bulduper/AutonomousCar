import jetson.inference
import numpy as np
import time


frameGPU_small = jetson.utils.cudaAllocMapped(width=1640, height=616, format='rgb8')
MODEL_PATH = './networks/signs_raw_v0_4.onnx'
# MODEL_PATH = './networks/model4_raw_only_2000s_ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.onnx'
THRESHOLD = 0.6
REMOTE_DESKTOP = False

working = False

def init():
    global net,working
    net = jetson.inference.detectNet(argv=["--model={}".format(MODEL_PATH), "--labels=./networks/labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=THRESHOLD)
    working = True

def detectSigns(cuda_img):
    if not working:
        init()
    global net, frameGPU_small
    # jetson.utils.cudaResize(cuda_img,frameGPU_small)
    detections = net.Detect(cuda_img)
    # jetson.utils.cudaConvertColor(cuda_img, frameGPU_bgr_small_detection)
    for detection in detections:
        ID = detection.ClassID
        item=net.GetClassDesc(ID)
        print(item)
    return detections

#roi should be an array of relative (0;1) [x_min, y_min, x_max, y_max]
def crop(imgInput, roi: "tuple[float,float,float,float]"):

    # crop_roi = (int(imgInput.width * 0.2), int(imgInput.height * 0.5),int(imgInput.width * 0.8), int(imgInput.height*0.7) )
    abs_roi = (int(roi[0]*imgInput.width),int(roi[1]*imgInput.height),int(roi[2]*imgInput.width),int(roi[3]*imgInput.height))
    
    # allocate the output image, with the cropped size
    imgOutput = jetson.utils.cudaAllocMapped(width=int(imgInput.width * (roi[2]-roi[0])),
                                            height=int(imgInput.height*(roi[3]-roi[1])),
                                            format=imgInput.format)

    # crop the image to the ROI
    jetson.utils.cudaCrop(imgInput, imgOutput, abs_roi)

    return imgOutput

def getVisual():
    if working:
        return jetson.utils.cudaToNumpy(frameGPU_bgr_small_detection)
    return np.zeros((480,640,3),dtype=np.uint8)


#initiate camera&display using jetson.utils (alternatively openCV with proper GStreamer pipeline can be used)
def cameraInit():
    global camera
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                    "--framerate=5", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
    "display://0", argv=["--output-width=640 --output-height=480 "])  # 'my_video.mp4' for file
    return camera, display


#fps counter vars
start_time = time.time()
counter = 0
#count fps or loops per second and set it as dict var every T seconds
def fpsCount():
    global counter, start_time
    counter += 1
    #period for fps calculation [s]
    T=1
    if (time.time() - start_time) > T:
        fps = round(counter / (time.time() - start_time),1)
        print("FPS: ", fps)
        counter = 0
        start_time = time.time()


    #main loop
def videoLoop():
    global REMOTE_DESKTOP
    camera, display = cameraInit()
    init()
    # frameGPU = camera.Capture()
    while display.IsStreaming():
        #get CUDA img
        frameGPU = camera.Capture()
        #get cropped roi image
        frame_roi = crop(frameGPU,(0.2,0.5,0.8,0.7))

        detections = detectSigns(frame_roi)
        if detections: print('Detections: ',detections[0].Center)

        #if there is a display connected to Jetson, frames can be displayed on it 
        if REMOTE_DESKTOP:
            display.Render(frame_roi)
        fpsCount()

videoLoop()

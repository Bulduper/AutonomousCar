
###
#openCV must be imported before jetson.utils and jetson.inference
###

# from web_app.streamer_new import HttpStreamer 
import web_app.streamer_new_noclass as streamer
import jetson.utils
import jetson.inference
import time
import threading



REMOTE_DESKTOP = False

threads = []



# streamer = HttpStreamer()

frameGPU = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
frameGPU_bgr_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameGPU_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')

start_time = time.time()
counter = 0
#period for fps calc
T=1

def fpsCount():
    global counter, start_time
    counter += 1
    if (time.time() - start_time) > T:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

def getVideo():
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                  "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
        "display://0", argv=[])  # 'my_video.mp4' for file
    global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small
    while display.IsStreaming():
        frameGPU = camera.Capture()
        jetson.utils.cudaResize(frameGPU,frameGPU_small)
        jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
        jetson.utils.cudaDeviceSynchronize()
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_small)
        if REMOTE_DESKTOP:
            display.Render(frameGPU)
        fpsCount()
        streamer.setFrame(frameNp_small)
        
if __name__ == "__main__":
    video_thread = threading.Thread(target=getVideo, daemon=True)

    #streamer_thread = threading.Thread(target=streamer.run, daemon=True)

    threads.append(video_thread)
    #threads.append(streamer_thread)

    for thread in threads:
        thread.start()
    
    streamer.run()
    for thread in threads:
        thread.join()



def gstreamer_pipeline(
    sensor_mode=3,
    display_width=1024,#4:3 format
    display_height=768,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor_mode=%d ! "
        "video/x-raw(memory:NVMM), "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)I420 ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=1"
        % (
            sensor_mode,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )
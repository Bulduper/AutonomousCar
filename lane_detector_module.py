import cv2
import numpy as np
import utils


img_stack = [None,None,None]

def init():
    warpTrackBarValues = [.47, 0.61, 1.56, .88]
    utils.initWarpTrackbars(warpTrackBarValues)

    hsvTrackbarValues = [100,134,40,255,120,255]
    utils.initHSVTrackbars(hsvTrackbarValues)

def findLane(input_img):
    global img_stack
    img = input_img.copy()
    #specify ROI using some sliders
    #WARP IMAGE TO BIRD'S EYE VIEW
    warp_points = utils.getWarpSourcePoints()
    warped_img = utils.perspective_warp(img,warp_points)
    utils.drawCircle(img,warp_points)

    #HLS/HSV mask to find the lane lines
    blue_mask = utils.hsvThreshold(warped_img)
    img_stack = utils.stackImages(0.3,[img,warped_img,blue_mask])


    return img_stack
from tokenize import detect_encoding
import cv2
import numpy as np
from numpy.lib.function_base import histogram
import utils

left_line_x_avg = -1
right_line_x_avg = -1

def init():
    warpTrackBarValues = [.47, 0.61, 1.56, .86]
    utils.initWarpTrackbars(warpTrackBarValues)

    hsvTrackbarValues = [100,134,40,255,120,255]
    utils.initHSVTrackbars(hsvTrackbarValues)

def findLines(input_img):
    img = input_img.copy()
    #specify ROI using some sliders
    #WARP IMAGE TO BIRD'S EYE VIEW
    warp_points_rel = utils.getWarpSourcePoints()
    warped_img = utils.perspective_warp(img,warp_points_rel,dstSize=(img.shape[1],img.shape[0]))
    #from relative to absolute
    warp_points = np.empty_like(warp_points_rel)
    #size = np.flip(warped_img.shape[:2],1)
    # size = np.array([warped_img.shape[1],warped_img.shape[0]])
    # #print(size, warp_points_rel[1])
    # for i,pt_rel in enumerate(warp_points_rel):
    #     warp_points[i]=[a*b for a,b in zip(size,pt_rel)]
    # print(warp_points_rel,warp_points)
    utils.drawCircle(img,warp_points_rel)

    #HSV mask to find the lane lines
    blue_mask = utils.hsvThreshold(warped_img)

    #find curvature


    #img_stack = utils.stackImages(0.3,[img,warped_img,blue_mask])

    return [blue_mask,img,warped_img]

def findCurvature(input_img):
    global left_line_x_avg, right_line_x_avg
    if left_line_x_avg == -1:
        left_line_x_avg = 0
        right_line_x_avg = input_img.shape[1]
    img = input_img.copy()
    #window variables
    window_width = int(0.15 * img.shape[1])
    window_height = int(0.05 * img.shape[0])
    line_erase_width = int(0.1 * img.shape[1])
    #first histogram
    # first_row = img[(img.shape[0] - window_height):,:]
    # first_histogram = np.sum(first_row,axis=0)
    #blackman window that is similar to gaussian
    conv_win = np.blackman(window_width)
    # #do convolution, which reveals the peak in the middle of the line
    # conv_histogram = np.convolve(first_histogram,conv_win,mode='same').astype(int)
    

    left_line_pts = np.empty((0,2),dtype=int)
    right_line_pts = np.empty((0,2),dtype=int)
    rows = 16
    detection_threshold = 110000
    for i in range(rows):
        img_row = img[(img.shape[0] - (i+1)*window_height):(img.shape[0] - (i)*window_height),:]
        hist = np.sum(img_row,axis=0)
        #do convolution, which reveals the peak in the middle of the line
        conv_histogram = np.convolve(hist,conv_win,mode='same').astype(int)
        _conv_1_max = np.max(conv_histogram)
        center1, center2 = -1, -1
        if np.max(conv_histogram)>detection_threshold:
            center1 = np.argmax(conv_histogram)
            #cancel out the found center line from array
            conv_histogram[center1-int(line_erase_width/2):center1+int(line_erase_width/2)]=0
            if np.max(conv_histogram)>detection_threshold:
                center2 = np.argmax(conv_histogram)
        #print(i,_conv_1_max,np.max(conv_histogram))
        #if we found only ONE line segment
        if center1 != -1 and center2 == -1:
            if abs(center1-left_line_x_avg) < abs(center1-right_line_x_avg):
                left_line_pts = np.append(left_line_pts,[(center1,int(img.shape[0] - (i+0.5)*window_height))],axis=0)
            else:
                right_line_pts = np.append(right_line_pts,[(center1,int(img.shape[0] - (i+0.5)*window_height))],axis=0)    
        #if we found both lines 
        elif center1 != -1 and center2 != -1:
            #if the centers are swapped
            if center2<center1:
                center1, center2 = center2, center1
            #TU PROBLEM
            left_line_pts = np.append(left_line_pts,[(center1,int(img.shape[0] - (i+0.5)*window_height))],axis=0)
            right_line_pts = np.append(right_line_pts,[(center2,int(img.shape[0] - (i+0.5)*window_height))],axis=0)
    #print('END')
    if left_line_pts.any():
        left_line_x_avg  = np.mean(left_line_pts[:,0])
    if right_line_pts.any():
        right_line_x_avg  = np.mean(right_line_pts[:,0])
    #print(left_line_x_avg,right_line_x_avg)
    return left_line_pts, right_line_pts
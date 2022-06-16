import numpy as np
import utils
import cv2
import math

left_line_prev_pt = np.empty((0),dtype=int)
right_line_prev_pt = np.empty((0),dtype=int)
lane_width_avg = 300

warp_undistorted_values = [.47, 0.61, 1.39, .86]
warp_distorted_values = [0.51,0.61,1.21,.81]
hsvTrackbarValues = [100,134,80,255,100,255]

#IMAGES HALF-PRODUCT
global warped_img, hsv_mask, debug_img, undist_plot

def init():
    warpTrackBarValues = warp_undistorted_values
    utils.initWarpTrackbars(warpTrackBarValues)

    
    utils.initHSVTrackbars(hsvTrackbarValues)

def findLines(input_img):
    global warped_img, hsv_mask, debug_img, undist_plot
    img = input_img.copy()
    #specify ROI using some sliders
    #WARP IMAGE TO BIRD'S EYE VIEW
    warp_points_rel = utils.getWarpSourcePoints(default=[x*100.0 for x in warp_undistorted_values])
    #warp_points_rel = utils.getWarpSourcePoints()
    #warp_points_rel = [x*100.0 for x in warp_undistorted_values]
    warped_img = utils.perspective_warp(img,warp_points_rel,dstSize=(img.shape[1],img.shape[0]))
    #from relative to absolute
    warp_points = [[p[0]*img.shape[1],p[1]*img.shape[0]] for p in warp_points_rel]
    #swap points to draw trapezoid later
    warp_points[2], warp_points[3] = warp_points[3], warp_points[2]
    warp_points = np.array([warp_points])

    utils.drawPerimiter(img,warp_points)
    undist_plot = img.copy()

    #HSV mask to find the lane lines
    hsv_mask = utils.hsvThreshold(warped_img,defaultHSV=hsvTrackbarValues)

    return hsv_mask

def getLanePoints(input_img):
    global left_line_prev_pt, right_line_prev_pt, lane_width_avg, debug_img

    img_mask = findLines(input_img)

    if not left_line_prev_pt.any():
        left_line_prev_pt = np.array([-1,img_mask.shape[0]])
    if not right_line_prev_pt.any():
        right_line_prev_pt = np.array([img_mask.shape[1],img_mask.shape[0]])

    debug_img = warped_img.copy()
    img = img_mask.copy()
    #window variables
    #window will be used to perform convolution and specify the height of line segment
    window_width = int(0.15 * img.shape[1])
    window_height = int(0.05 * img.shape[0])
    line_erase_width = int(0.35 * img.shape[1])
    
    #blackman window that is similar to gaussian function
    conv_win = np.blackman(window_width/3)
    
    #line data
    left_line_pts = np.empty((0,2),dtype=int)
    right_line_pts = np.empty((0,2),dtype=int)
    center_line_pts = np.empty((0,2),dtype=int)
    weighted_curvature = np.empty((0,2),dtype=int)
    lane_widths = np.empty((0,1),dtype=int)
    
    #THERE IS A PROBLEM WITH TOO MANY ROWS -> at some point line can become horizontal and thus the whole algorithm stops working properly
    #rows * window_height is how far (in px) we look at the lane
    rows = 5
    #line detection threshold (empirically obtained) (dependent on blackman window width)
    detection_threshold = 20000
    #for each row
    for i in range(rows):
        #img cropped to row only
        img_row = img[(img.shape[0] - (i+1)*window_height):(img.shape[0] - (i)*window_height),:]
        window_y_center = int(img.shape[0] - (i+0.5)*window_height)
        hist = np.sum(img_row,axis=0)
        #do convolution, which reveals the peak in the middle of the line
        conv_histogram = np.convolve(hist,conv_win,mode='same').astype(int)
        _conv_1_max = np.max(conv_histogram)
        #line centers
        center1, center2 = -1, -1
        #if the peak is more than threshold we have a line
        if np.max(conv_histogram)>detection_threshold:
            center1 = np.argmax(conv_histogram)

            #DEBUG LINES
            #cv2.rectangle(dimg,(center1-int(window_width/2),dimg.shape[0]-int(i*window_height)),(center1+int(window_width/2),int(dimg.shape[0]-(i+1)*window_height)),(0,0,255),2)
            #cv2.putText(dimg,str(np.max(conv_histogram)),(center1+int(window_width/2),int(dimg.shape[0]-(i)*window_height)),cv2.FONT_HERSHEY_SIMPLEX,1,(209,80,0,255),2)
            #cancel out the found center line from array
            #conv_histogram[center1-int(line_erase_width/2):center1+int(line_erase_width/2)]=0
            conv_histogram[center1-int(line_erase_width/2) if center1>int(line_erase_width/2) else 0 :center1+int(line_erase_width/2)]=0


            #look for the second peak
            if np.max(conv_histogram)>detection_threshold:
                center2 = np.argmax(conv_histogram)
                
                #cv2.rectangle(dimg,(center2-int(window_width/2),dimg.shape[0]-int(i*window_height)),(center2+int(window_width/2),int(dimg.shape[0]-(i+1)*window_height)),(0,255,0),2)
                #cv2.putText(dimg,str(np.max(conv_histogram)),(center2+int(window_width/2),int(dimg.shape[0]-(i)*window_height)),cv2.FONT_HERSHEY_SIMPLEX,1,(209,80,0,255),2)
        #print(i,_conv_1_max,np.max(conv_histogram))

        # row rectangle
        # cv2.line(dimg,(0,int(dimg.shape[0] - (i+1)*window_height)),(dimg.shape[1],int(dimg.shape[0] - (i+1)*window_height)),(163, 163, 194),thickness=1)
        
        #if we found only ONE line segment
        if center1 != -1 and center2 == -1:
            #check if the line segment is closer to previously detected left line segments or right line segments
            #estimate lane middle using average lane width/2 (+-)
            #linalg.norm calculates distance between two points
            #cv2.line(dimg,(center1,window_y_center),left_line_prev_pt,(0, 0, 255),thickness=1)
            #cv2.line(dimg,(center1,window_y_center),right_line_prev_pt,(0, 255, 0),thickness=1)
            if np.linalg.norm([center1,window_y_center]-left_line_prev_pt) < np.linalg.norm([center1,window_y_center]-right_line_prev_pt):
            # if abs(center1-left_line_prev_pt) < abs(center1-right_line_prev_pt):
                left_line_pts = np.append(left_line_pts,[(center1,window_y_center)],axis=0)
                left_line_prev_pt = np.array([center1,window_y_center])
                center_line_pts = np.append(center_line_pts,[(int(center1+lane_width_avg/2),window_y_center)],axis=0)
            else:
                right_line_pts = np.append(right_line_pts,[(center1,window_y_center)],axis=0)
                right_line_prev_pt = np.array([center1,window_y_center])
                center_line_pts = np.append(center_line_pts,[(int(center1-lane_width_avg/2),window_y_center)],axis=0)
        #if we found BOTH lines 
        elif center1 != -1 and center2 != -1:
            #if the centers are swapped
            if center2<center1:
                center1, center2 = center2, center1
            #append left&right&central line data
            left_line_pts = np.append(left_line_pts,[(center1,window_y_center)],axis=0)
            left_line_prev_pt = np.array([center1,window_y_center])
            right_line_pts = np.append(right_line_pts,[(center2,window_y_center)],axis=0)
            right_line_prev_pt = np.array([center2,window_y_center])
            center_line_pts = np.append(center_line_pts,[(int((center1+center2)/2),window_y_center)],axis=0)
            lane_widths = np.append(lane_widths,[center2-center1])

    #if any left line was detected => set its first point as previous left line point 
    if left_line_pts.any():
        #left_line_prev_pt  = np.mean(left_line_pts[:,0])
        left_line_prev_pt = left_line_pts[0]
    #if not => let the left down corner be a previous point (that is where we expect the line to appear)
    else:
        left_line_prev_pt = np.array([-1,img.shape[0]])
    #respectively
    if right_line_pts.any():
        #right_line_prev_pt  = np.mean(right_line_pts[:,0])
        right_line_prev_pt = right_line_pts[0]
    else:
        right_line_prev_pt = np.array([img.shape[1],img.shape[0]])

    if lane_widths.any():
        lane_width_avg  = np.mean(lane_widths)


    return left_line_pts, center_line_pts, right_line_pts


def getCurveAngle(pts):
    angles = []
    for i in range(1, len(pts)):
        dx = pts[i][0]-pts[i-1][0]
        dy = pts[i][1]-pts[i-1][1]
        if dy == 0: continue
        angle = math.degrees(math.atan(dx/dy))
        angles.append(angle)
    if len(angles):
        avg_angle = sum(angles)/len(angles)
        return avg_angle 
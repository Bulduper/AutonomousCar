import numpy as np
import utils
import cv2

left_line_prev_pt = np.empty((0),dtype=int)
right_line_prev_pt = np.empty((0),dtype=int)
lane_width_avg = 300

warp_undistorted_values = [.47, 0.61, 1.56, .86]
warp_distorted_values = [0.51,0.61,1.21,.81]

def init():
    warpTrackBarValues = warp_distorted_values
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

    #find weighted_curvature

    return [blue_mask,img,warped_img]

def findCurvature(input_img, debug_img=None):
    global left_line_prev_pt, right_line_prev_pt, lane_width_avg
    if not left_line_prev_pt.any():
        left_line_prev_pt = np.array([-1,input_img.shape[0]])
    if not right_line_prev_pt.any():
        right_line_prev_pt = np.array([input_img.shape[1],input_img.shape[0]])
    
    if not debug_img is None: dimg = debug_img.copy()
    img = input_img.copy()
    #window variables
    #window will be used to perform convolution and specify the height of line segment
    window_width = int(0.15 * img.shape[1])
    window_height = int(0.05 * img.shape[0])
    line_erase_width = int(0.2 * img.shape[1])
    
    #blackman window that is similar to gaussian function
    conv_win = np.blackman(window_width)
    
    #line data
    left_line_pts = np.empty((0,2),dtype=int)
    right_line_pts = np.empty((0,2),dtype=int)
    center_line_pts = np.empty((0,2),dtype=int)
    weighted_curvature = np.empty((0,2),dtype=int)
    lane_widths = np.empty((0,1),dtype=int)
    #rows * window_height is how far (in px) we look at the lane
    rows = 8
    #line detection threshold (empirically obtained)
    detection_threshold = 80000
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
            #cancel out the found center line from array
            conv_histogram[center1-int(line_erase_width/2):center1+int(line_erase_width/2)]=0
            #look for the second peak
            if np.max(conv_histogram)>detection_threshold:
                center2 = np.argmax(conv_histogram)
        #print(i,_conv_1_max,np.max(conv_histogram))
        #if we found only ONE line segment
        if center1 != -1 and center2 == -1:
            #check if the line segment is closer to previously detected left line segments or right line segments
            #estimate lane middle using average lane width/2 (+-)
            #linalg.norm calculates distance between two points
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
            #if we already have two center line points
            if len(center_line_pts)>1:
                #calculate the y-axis increment Y2-Y1
                y_diff = int((center_line_pts[-1][1] - center_line_pts[-2][1])/window_height)
                #calculate weighted curvature and append it to array
                #curvature is dX/dROW
                #weighted curvature id curvature * (rows - row) => the closest line segments are most significant
                #weighted_curvature array element can be presented as a vector pointing from the first center_line point  => [weighted_curvature=(w*dX), Y1]
                weighted_curvature = np.append(weighted_curvature,[((rows-i)*((center_line_pts[-1][0] - center_line_pts[-2][0])/y_diff),int(img.shape[0] - (i-0.5)*window_height))],axis=0)
    #if any left line was detected => set its first point as previous left line point 
    if left_line_pts.any():
        #left_line_prev_pt  = np.mean(left_line_pts[:,0])
        left_line_prev_pt = left_line_pts[0]
    #if not => let the left down corner be a previous point (that is where we expect the line to appear)
    else:
        left_line_prev_pt = np.array([-1,input_img.shape[0]])
    #respectively
    if right_line_pts.any():
        #right_line_prev_pt  = np.mean(right_line_pts[:,0])
        right_line_prev_pt = right_line_pts[0]
    else:
        right_line_prev_pt = np.array([input_img.shape[1],input_img.shape[0]])
    
    if lane_widths.any():
        lane_width_avg  = np.mean(lane_widths)
    #print(left_line_prev_pt, right_line_prev_pt)
    # for i in range(len(center_line_pts)-1):
    #     weight = rows - center_line_pts[i][1]
    #     weighted_curvature = np.append(weighted_curvature,[weight*(center_line_pts[i+1][0] - center_line_pts[i][0],center_line_pts[i][1])],axis=0)
    #     print(i,weighted_curvature[i])
    #weights = range(rows,0)
    #calculate average curvature (single value) using weighted curvature
    weights_sum = (rows+1)/2*rows
    avg_curvature = np.sum(weighted_curvature,axis=0)[0]/weights_sum;
    #print(avg_curvature)

    return left_line_pts, right_line_pts, center_line_pts, avg_curvature, dimg
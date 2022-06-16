import numpy as np
import cv2
import glob
# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
CHECKERBOARD = (6,9)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
images = glob.glob('./img/*.jpg')

#find chessboard pattern and list it
def find_chessboard(img, draw = True, calibrate = False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    global shape
    shape = gray.shape[::-1]
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    if ret == True:
        print('CHESSBOARD FOUND')
        corners2 = cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
        if calibrate:
            objpoints.append(objp)
            imgpoints.append(corners)
        if draw:
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
            # cv2.putText(img,str(len(objpoints)),(shape[0]/2,shape[1]/2),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255))
    return img

#create calibration matrices and params according to collected data (export it to file optionally)
def calibrate(export=False):
    if len(objpoints)==0 or len(imgpoints)==0:
        print('No data to calibrate')
        return
    global ret, mtx, dist, rvecs, tvecs, shape
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,shape, None, None)
    # print(f'Ret = {ret}')
    # print(f'Mtx = {mtx}')
    # print(f'Dist = {dist}')
    # print(f'Rvecs = {rvecs}')
    # print(f'Tvecs = {tvecs}')
    if export:
        np.save(f'./calib_data/ret_{shape[0]}.npy',ret)
        np.save(f'./calib_data/mtx_{shape[0]}.npy',mtx)
        np.save(f'./calib_data/dist_{shape[0]}.npy',dist)
        np.save(f'./calib_data/rvecs_{shape[0]}.npy',rvecs)
        np.save(f'./calib_data/tvecs_{shape[0]}.npy',tvecs)
        print('CALIBRATION FILES EXPORTED')

#import calibration arrays (matrices) from ./calib_data folder
#for a specific img width (by deafult 640px)
def import_calib(img_width=640):
    global ret, mtx, dist, rvecs, tvecs, mapx, mapy
    ret = np.load(f'./calib_data/ret_{img_width}.npy')
    mtx = np.load(f'./calib_data/mtx_{img_width}.npy')
    dist = np.load(f'./calib_data/dist_{img_width}.npy')
    rvecs = np.load(f'./calib_data/rvecs_{img_width}.npy')
    tvecs = np.load(f'./calib_data/tvecs_{img_width}.npy')

    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, mtx, (img_width,480), 5)
    return ret, mtx, dist, rvecs, tvecs

#remove radial/tangential distortions
def undistort(img, alpha=1.0):
    global ret, mtx, dist, rvecs, tvecs, mapx, mapy
    h,  w = img.shape[:2]
    #newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (1640, 1232), 0, (w,h))
    
    #### cv2.undistort SIGNIFICANTLY LESS EFFICIENT
    # undist = cv2.undistort(img, mtx, dist, None)
    #### cv2.remap MORE EFFICIENT,  requires mapx, mapy = cv2.initUndistortRectifyMap() on init
    undist = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
    # undist = img

    #In case of different size image
    #newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (1640, 1232), alpha)
    #new = cv2.undistort(img, mtx, dist, None, newcameramtx)
    #x, y, w, h = roi
    #new = new[y:y + h, x:x + w]
    return undist
# if __name__ == '__main__':
#     t = threading.Thread(target=find_pattern)
#     t.daemon = True
#     t.start()
#     streamer.start_stream()
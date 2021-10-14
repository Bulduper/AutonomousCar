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
            cv2.drawChessboardCorners(img, (9,6), corners2, ret)
    return img

def calibrate(export=False):
    if len(objpoints)==0 or len(imgpoints)==0:
        print('No data to calibrate')
        return
    global ret, mtx, dist, rvecs, tvecs
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,shape, None, None)
    print(f'Ret = {ret}')
    print(f'Mtx = {mtx}')
    print(f'Dist = {dist}')
    print(f'Rvecs = {rvecs}')
    print(f'Tvecs = {tvecs}')
    if export:
        np.save('./calib_data/ret.npy',ret)
        np.save('./calib_data/mtx.npy',mtx)
        np.save('./calib_data/dist.npy',dist)
        np.save('./calib_data/rvecs.npy',rvecs)
        np.save('./calib_data/tvecs.npy',tvecs)

def import_calib():
    global ret, mtx, dist, rvecs, tvecs
    ret = np.load('./calib_data/ret.npy')
    mtx = np.load('./calib_data/mtx.npy')
    dist = np.load('./calib_data/dist.npy')
    rvecs = np.load('./calib_data/rvecs.npy')
    tvecs = np.load('./calib_data/tvecs.npy')
    return ret, mtx, dist, rvecs, tvecs


def undistort(img, alpha=1.0):
    global ret, mtx, dist, rvecs, tvecs
    h,  w = img.shape[:2]
    undist = cv2.undistort(img, mtx, dist, None)
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
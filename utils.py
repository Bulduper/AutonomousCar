import cv2
import numpy as np
import time
from TrackBarWindow import TrackBarWindow

warpingTrackbars = None
hsvTrackbars = None

def stackImages(scale,imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver

def initWarpTrackbars(initVals):
    initVals = [int(i * 100) for i in initVals]
    global warpingTrackbars
    warpingTrackbars = TrackBarWindow(
        [['wTop', initVals[0], 100], ['hTop', initVals[1], 100], ['wBtm', initVals[2], 200],
         ['hBtm', initVals[3], 100]])


def initHSVTrackbars(initVals):
    global hsvTrackbars
    hsvTrackbars = TrackBarWindow(
        [['Hmin', initVals[0], 255], ['Hmax', initVals[1], 255], ['Smin', initVals[2], 255], ['Smax', initVals[3], 255],
         ['Vmin', initVals[4], 255], ['Vmax', initVals[5], 255]])

def getWarpSourcePoints(default = None):
    global warpingTrackbars
    if warpingTrackbars is None:
        if default is None:
            print('No warping points source!')
            raise
        warpParams = default
    else:
        warpParams = warpingTrackbars.getValues()
    warpParams = [i / 100.0 for i in warpParams]
    srcPoints = np.float32([(0.5 - warpParams[0] / 2, warpParams[1]),
                            (0.5 + warpParams[0] / 2, warpParams[1]),
                            (0.5 - warpParams[2] / 2, warpParams[3]),
                            (0.5 + warpParams[2] / 2, warpParams[3])])
    return srcPoints


def hsvThreshold(img, defaultHSV = None):
    imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    if hsvTrackbars is None:
        if defaultHSV is None:
            print('No HSV values source!')
            raise
        hsvValues = defaultHSV
    else:
        hsvValues = hsvTrackbars.getValues()

    lower = np.array([hsvValues[0], hsvValues[2], hsvValues[4]])
    upper = np.array([hsvValues[1], hsvValues[3], hsvValues[5]])
    # lower=np.array([78,0,0])
    # upper=np.array([255,255,84])
    mask = cv2.inRange(imgHsv, lower, upper)
    return mask

def perspective_warp(img, srcPts, dstSize=(640, 480), dstPts=np.float32([(0, 0), (1, 0), (0, 1), (1, 1)])):
    srcSize = np.float32([(img.shape[1], img.shape[0])])
    srcPts = srcPts * srcSize

    dstPts = dstPts * np.float32(dstSize)

    matrix = cv2.getPerspectiveTransform(srcPts, dstPts)

    warpedImg = cv2.warpPerspective(img, matrix, dstSize, borderValue=(255, 255, 255))
    return warpedImg

def drawCircle(img, points):
    for p in points:
        cv2.circle(img, (int(p[0] * img.shape[1]), int(p[1] * img.shape[0])), 10, (0, 255, 0), cv2.FILLED)

def drawPerimiter(img,points):
    cv2.polylines(img,np.int32([points]),True,(204, 0, 102),thickness=2)

def rotateImg(img,degrees=180):
    center = (img.shape[1]//2, img.shape[0]//2)
    M = cv2.getRotationMatrix2D(center, degrees,scale=1.0)
    rotated = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    return rotated
# def drawCircle(img, points):
#     for p in points:
#         cv2.circle(img, (int(p[0]), int(p[1])), 10, (0, 255, 0), cv2.FILLED)

def drawLaneLine(img, points, color):
    for p in points:
        cv2.circle(img,p,5,color,cv2.FILLED)

def drawStraightLine(img,pt1,pt2,color):
    cv2.line(img,pt1,pt2,color,2)

def putText(img,string):
    cv2.putText(img,string,(300,50),cv2.FONT_HERSHEY_SIMPLEX,1.0,(255,255,255),1,cv2.LINE_AA)

def captureImg(img,filename='captured/captured'):
    print('Capturing img ./img/',filename)
    print(time.time())
    timestamp = int(time.time())
    cv2.imwrite('./img/{}_{}.jpg'.format(filename, timestamp), img)
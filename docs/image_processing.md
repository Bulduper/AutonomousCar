# Image processing for lane detection
![lane_detection_birdeye](/images/lane_detection_birdeye.jpg)
## Distortion correction (optional - time consuming)
| Distorted (raw) | Undistorted |
|-------------|----------------------|
| ![before_undistort](/images/before_undistort.jpg) | ![after_undistort](/images/after_undistort.jpg) |
| ![before_undistort_warp](/images/before_undistort_warp.jpg) | ![after_undistort_warp](/images/after_undistort_warp.jpg) |
| ![before_undistort_mask](/images/before_undistort_mask.jpg) | ![after_undistort_mask](/images/after_undistort_mask.jpg) |

As you can see in the pictures on the left, a wide angle camera gives you an effect which causes straight lines to bend, the more, the further they are from the center. Also lines that are horizonally further from the center seem to be thinner. The effect is accociated with the shape of the lense and allows regular camera sensors to "see more".

You can reverse the distortion using image processing algorithms. It might be beneficial if your further image processing algorithms will require accurate and even representation of the whole view.

A good example of distortion correction being useful is lane detection. The correction make the detected lane line to be of the same width regardless of the placement along x-axis. 

The lines (and lane) also shrink along the y-axis, but this issue can be handled by [perspective transformation](#perspective-transformation).

### Drawbacks
#### Time consuming 
I found the distortion correction algorithm to be quite time consuming. (some more info...)
#### Lost image regions
Implementing the algorithm results in loosing parts of image (that you earned by using wide-angle lense).



## Perspective transformation
In this step we get rid of the perspective effect, which makes lane lines converge in the camera view and complicate a path curvature computations. The goal is to achieve a bird eye view on the track in front of a vehicle.

The function `perspective_warp` in `utils.py` requires input image and a list of 4 points (tuples) and outputs a transformed image.

```python
def perspective_warp(img, srcPts, dstSize=(640, 480), dstPts=np.float32([(0, 0), (1, 0), (0, 1), (1, 1)])):
    srcSize = np.float32([(img.shape[1], img.shape[0])])
    srcPts = srcPts * srcSize

    dstPts = dstPts * np.float32(dstSize)

    matrix = cv2.getPerspectiveTransform(srcPts, dstPts)

    warpedImg = cv2.warpPerspective(img, matrix, dstSize, borderValue=(255, 255, 255))
    return warpedImg
```
`perspective_warp` maps source points to destination points and stretches the input image.
It can be visualized by drawing a trapezoid obtained by conntecting the source points. The trapezoid then gets stretched to the shape of input image. The source points should be adjusted to reflect the region of interest for where the lane is.
|    |  |   |
| ----- | ---- | ------ |
| ![undistorted_plot](/images/undistorted_plot.jpg) | => | ![undistorted_warp](/images/undistorted_warp.jpg) |

## HSV thresholding
There are at least three ways of extracting lane lines from an image. You can do it using machine learning, color gradient or color range. In this case the latter technique is used. 

A very good model to represent color ranges in varying lighting conditions is [HSV](https://en.wikipedia.org/wiki/HSL_and_HSV) (hue, saturation, value). For each of these 3 parameters we need to pick a minimum and maximum which mark the range. For example, with my camera, usual lighting conditions and the tape color, the following ranges work well:
|   | min | max |
|---|-----|-----|
| H | 100 | 134 |
| S | 80  | 255 |
| V | 100 | 255 |

The next step is thresholding, which maps every pixel within the given range to 1 (white) and the rest to 0 (black).

At the end we are left with a black and white image of our lane lines:

|    |  |   |
| ----- | ---- | ------ |
| ![undistorted_warp](/images/undistorted_warp.jpg) | => | ![undistorted_mask](/images/undistorted_mask.jpg) |

## Lane detection
Although for humans it's trivial to tell the direction and curvature of a lane when given an image obtained in the previous step, it still requires some more work for the computer to find that information. The technique I use is similar to [sliding window](https://www.youtube.com/watch?v=X8QN-qY7uIo).

The main steps include:
- Rows isolation
- Histogram
- Blackman window convolution
- Find maximum

![Lane detection algorithm](/images/lane_detection.drawio.png)

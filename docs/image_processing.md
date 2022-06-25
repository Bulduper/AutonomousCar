# Image processing for lane detection
![lane_detection_birdeye](/images/lane_detection_birdeye.jpg)
## Distortion correction (optional - time consuming)
| Distorted (raw) | Undistorted |
|-------------|----------------------|
| ![before_undistort](/images/before_undistort.jpg) | ![after_undistort](/images/after_undistort.jpg) |
|  | ![after_undistort_mask](/images/after_undistort_mask.png) |

As you can see in the picture on the left, a wide angle camera gives you an effect which causes straight lines to bend, the more, the further they are from the center. The effect is accociated with the shape of the lense and allows the regular camera sensor to "see more".

You can reverse the distortion using image processing algorithms. It might be beneficial if your further image processing algorithms will require accurate and even representation of the whole view.

A good example of distortion correction being useful is lane detection. The correction make the detected lane line to be of the same width regardless of the placement along x-axis. 

The lines (and lane) also shrink along the y-axis, but this issue can be handled by [perspective transformation](#perspective-transformation).

### Drawbacks
#### Time consuming 
I found the distortion correction algorithm to be quite time consuming. (some more info...)
#### Lost image regions
Implementing the algorithm results in loosing parts of image (that you earned by using wide-angle lense).



## Perspective transformation

## HSV thresholding

## Lane detection
### Rows isolation
### Histogram
### Blackman window convolution
### Find maximum

# Autonomous Car Platform
## Overview
Welcome to the repository of an educational platform designed as an autonomous toy car. The whole project consists of mechanical design, electronics board and lots of code. The main goal was to design a platform for students who want to experience building a prototype and learn technologies like Machine Learning or Computer Vision with it.

## Features
- Remote dashboard 
- Object detection (road signs)
- Lane following based on camera view
- 
## Main components
1. Nvidia Jetson Nano (2 or 4 GB version)
2. STM32 BlackPill
3. Wide-angle CSI camera
4. Wifi dongle (unless WiFi natively supported by your board)

## Pre-requisites
### Ubuntu Image for Nvidia Jetson Nano
Make sure that you have done the initial setup for Nvidia Jetson Nano. Download the newest OS image and write it to microSD card. [Click here to see the official instructions from Nvidia](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#prepare).


### WiFi connection
The platform is mobile, so WiFi connection is used to allow for remote control and telemetry.
Connect to your local WiFi network and check your Nano's IP address using `ifconfig`.


### SSH - headless mode
In order to take control over your Jetson Nano board and work in headless mode (recommended due to mobility) the SSH protocol is used. On your PC run cmd and execute `ssh <nano's ip address>`. You will be asked for the password to Jetson Nano user. You should now be able to run bash commands on your Jetson Nano remotely.

If you wish to skip password prompt everytime you connect via ssh, follow these steps:
- generate key pair (public-private) on your local machine `ssh keygen`
- copy the public key to `/home/{user}/.ssh` on the remote host

### Test your camera
Make sure you have the CSI camera connected. Try taking a picture:
```
cd
nvgstcapture-1.0
```
Then press `j` on your keyboard. Press `q` to quit.

#### Copy the photo to your local machine
```
scp <remote host ip>:<path/sourceFilename.jpg> <path to destination folder>
```
If your photo has an ugly pink tint and looks like this:

Follow the instructions that lead to [UPDATING THE ISP PROFILE](https://jonathantse.medium.com/fix-pink-tint-on-jetson-nano-wide-angle-camera-a8ce5fbd797f).

### Jetson Inference

### External libraries
```
sudo apt-get upgrade
pip3 install --upgrade setuptools
sudo apt-get install redis-server
pip3 install pyserial redis python-engineio flask-socketio

```
## Installation
###

## Develop
vscode ssh
## Optimise
### Disable GUI
### Disable redis-server autostart
## Common problems
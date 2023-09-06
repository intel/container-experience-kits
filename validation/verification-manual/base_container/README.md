# Base Container

## Motivation
Base container mechanism aims to provide a set of containers with the foundation features based on user selection. Then users, workload or service developers, can derive their final containers from those base containers.  Users can focus more on their own libraries or applications, reduce their effort to integrate those foundation features to their container and maintain version upgrade.

## Foundation Features
Current base container includes below foundation features

* Intel GPU user mode drivers and runtimes, including :
  * Graphics acceleration : OpenGL，OpenGL ES, Vulkan 
  * Media acceleration : VAAPI, VPL, MSDK
  * Compute acceleration : OpenCL,  Level Zero
* OpenVINO
* DLStreamer
* FFMPEG
* OpenCV

## Pre-defined Base Containers  
Currently base container is only enabled in on_prem_aibox profile, will be extended to more profiles in feature. 
* on_prem_aibox profile base contaienrs
  * aibox-base (from ubuntu 22.04)
    * GPU user mode drivers and runtimes
    * OpenVINO runtime
  * aibox-base-dev (from aibox-base)
    * OpenVINO developer tools
  * aibox-dlstreamer (from aibox-base)
    * DLStreamer
  * aibox-opencv-ffmpeg (from aibox-base)
    * OpenCV
    * FFMPEG

> **_NOTE:_** User can customize role/intel_base_container to define the base container set he wants.

## Build and Test Base Containers  
After profile deployment, base container related docker files and scripts will be generated to below location
```
    /opt/intel/base_container/
        dockerfile/         # Base container Dockerfiles and build scripts
        test/               # Test container Dockerfiles, build scripts and test scripts
```
You can use the dockerfile/build_\*.sh scripts to build those base containers, and then use test/test_\*.sh scripts to test them. 

### Example
Below is an example to build and test dlstreamer base container.
The test is to use dlstreamer to do car detection in an input video.
```
    cd /opt/intel/base_container/dockerfile
        ./build_base.sh
        ./build_dlstreamer.sh
    
    cd /opt/intel/base_container/test
        ./test_dlstreamer
```
After exectution completion, the result will be generated to 
```
    ~/nep_validator_data/
```
You can open test result files to check whether the test is success.
```
    cd ~/nep_validator_data/
    cat test_dlstreamer_result
```
If success, you should see "PASSED" in the test result file.

Open below output video with a media player
```
    ~/nep_validator_data/videos/output_person-vehicle-bike-detection-2004.mp4
```
If success, you should see the cars in the video are marked with rectangles and labels.


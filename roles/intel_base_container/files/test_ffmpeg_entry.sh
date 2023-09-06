#!/bin/bash

ffmpeg -decoders | grep -Ei "qsv|vaapi"
ffmpeg -encoders | grep -Ei "qsv|vaapi"

if [[ -d /home/aibox/data/videos/ffmpeg ]]
then
    rm -rf /home/aibox/data/videos/ffmpeg
fi
mkdir -p /home/aibox/data/videos/ffmpeg
DATA_PATH=/home/aibox/data/videos/ffmpeg

input_mp4_md5="e919de1193da5ceb8b0fd3cd998c2694"
output_yuv_md5="8dccdfb5226e94732d83343cbaf25e8c"
count=0
while [[ ${count} -le 5 ]]
do
    if [[ -f ${DATA_PATH}/input_car-detection.mp4 ]] && [[ $(md5sum ${DATA_PATH}/input_car-detection.mp4 | awk '{print $1}') == "${input_mp4_md5}" ]]
    then
        break
    fi
    if [[ ${count} == 5 ]]
    then
        echo ""
        echo "[Warning] !!!The mp4 file download failed, please rerun the case."
        exit 1
    fi
    curl -L https://storage.openvinotoolkit.org/test_data/videos/car-detection.mp4 --output ${DATA_PATH}/input_car-detection.mp4
    (( count+=1 )) || true
done

ffmpeg -v verbose -hwaccel qsv -init_hw_device qsv=qsv,child_device=/dev/dri/renderD128 -hwaccel_output_format nv12 \
       -hwaccel_flags allow_profile_mismatch -c:v h264_qsv -i ${DATA_PATH}/input_car-detection.mp4 -lavfi 'null' -c:v rawvideo -pix_fmt yuv420p \
       -fps_mode passthrough -autoscale 0 -y ${DATA_PATH}/ffmpeg_decode_output_car-detection.yuv

ffmpeg -v verbose -hwaccel qsv -init_hw_device qsv=qsv,child_device=/dev/dri/renderD128 -hwaccel_output_format qsv \
       -f rawvideo -pix_fmt yuv420p -s:v 768x432  -r:v 30 -i ${DATA_PATH}/ffmpeg_decode_output_car-detection.yuv \
       -vf 'format=nv12,hwupload=extra_hw_frames=120' -an -c:v h264_qsv  -profile:v main -g 30 -slices 1 -b:v 2000k -maxrate 2000k -y ${DATA_PATH}/ffmpeg_encode_output_car-detection.264

ffmpeg_path="/home/aibox/data/videos/ffmpeg"
result="Failed"

cd ${ffmpeg_path} || exit
current_yuv_md5=$(md5sum -- *yuv | awk '{print $1}')
current_264_size=$(du ./*264 | awk '{print $1}' )
echo "***Current files md5:"
md5sum -- *yuv
echo "***Current files:"
ls -l
if [[ "${current_yuv_md5}" == "${output_yuv_md5}" ]] && [[ ${current_264_size} -gt 2500 ]]
then
    result="Passed"
fi
echo ${result} | tee /home/aibox/data/test_ffmpeg_result

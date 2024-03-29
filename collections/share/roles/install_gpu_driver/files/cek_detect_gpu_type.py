
import os
import sys
import re

intel_dgpu_types = {
    "56c0" : "Flex",
    "56c1" : "Flex",

    "5690" : "Arc",
    "5691" : "Arc",
    "5692" : "Arc",
    "5693" : "Arc",
    "5694" : "Arc",
    "5695" : "Arc",
    "5696" : "Arc",
    "5697" : "Arc",

    "56a0" : "Arc",
    "56a1" : "Arc",
    "56a2" : "Arc",
    "56a3" : "Arc",
    "56a4" : "Arc",
    "56a5" : "Arc",
    "56a6" : "Arc",

    "56b0" : "Arc",
    "56b1" : "Arc",
    "56b2" : "Arc",
    "56b3" : "Arc",
}


def detect_gpu_type():
    cmd = 'lspci -mmnn | grep -i -E "Display|VGA" | grep Intel'
    result = os.popen(cmd)
    info_list = result.read()
    lines = info_list.splitlines()
    line_count = len(lines)
    if line_count > 0 :
        line = lines[0]
        device = re.findall(r'\"(.*?)\"', line)[2]
        chip_id = (device.split("["))[1].split("]")[0]

        if chip_id in intel_dgpu_types :
            gpu_type = intel_dgpu_types[chip_id]
        else :
            gpu_type = "iGPU"
    else:
        gpu_type = "Unknown"
        chip_id = "Unknown"

    print(gpu_type)
    print(chip_id)

detect_gpu_type()
sys.exit(0)

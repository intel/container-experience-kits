#!/bin/bash

echo "cek config NPU service starts"
chown root:render /dev/accel/accel*
chmod 660 /dev/accel/accel*
echo "cek config NPU service exists"

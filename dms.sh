sudo modprobe can
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ifconfig can0 up

python ./main/main.py

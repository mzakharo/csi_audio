ifconfig wlan0 up
nexutil -Iwlan0 -s500 -b -l34 -v m+IBEQGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==
iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
#tcpdump -i wlan0 dst port 5500


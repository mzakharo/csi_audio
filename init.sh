#!/bin/bash
set -exuo pipefail
IFS=$'\n\t'

ifconfig wlan0 up

#157/80
nexutil -Iwlan0 -s500 -b -l34 -v m+IBEQGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==

#36/80
#nexutil -Iwlan0 -s500 -b -l34 -vKuABEQGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==

iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
#tcpdump -i wlan0 dst port 5500


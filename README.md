Audio Server

-  initialization script and server for CSI audio streaming.

- On Raspberry Pi (Server)

1. ssh pi@nexmon.local. password: raspberry

2. Prep WiFi driver and firmware
```
sudo su
cd /home/pi/nexmon
source setup_env.sh
cd nexmon/patches/bcm43455c0/7_45_189/nexmon_csi
make install-firmware
```
3.  init.sh -> run once to initialize the CSI on Radio

4. python3 csi_proxy.py -> local server to serve CSI over pynng.


- On client PC

- python3 main.py nexmon.local

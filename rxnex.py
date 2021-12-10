import socket
import struct
import pynng
import time

UDP_IP = "0.0.0.0"
UDP_PORT = 5500
SO_TIMESTAMPNS = 35
SOF_TIMESTAMPING_RX_SOFTWARE = (1 << 3)

address = f'tcp://*:6970'
class RX():
    def __init__(self, log=None, poll=None):
        self.r = None
        self.pub = pynng.Pub0(listen=address, send_buffer_size=50, send_timeout=1000)
        
        r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        r.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, SOF_TIMESTAMPING_RX_SOFTWARE)
        r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #r.settimeout(0)
        self.r = r
        r.bind((UDP_IP, UDP_PORT))
        self.fd = r.fileno()

    def recv(self):
        cnt = 0
        last = time.time()
        while True:
            try:
                data, ancdata, _, _ = self.r.recvmsg(4096, 128)
            except socket.timeout:
                continue
            if len(data) < 18:
                print("rx: packet too small")
                continue
            #we got a new frame, but there was a frame pending
            s, us = struct.unpack('LL', ancdata[0][2])
            ts = s * 10**3 + us // 10**6
            self.publish(data, ts, 0)
            cnt +=1
            if time.time() - last > 1:
                print('cnt', cnt)
                cnt = 0
                last = time.time()

    def publish(self, data, ts, frame_cnt):
        hdr = struct.pack('<BQHb', 3, ts, len(data), frame_cnt)
        self.pub.send(b''.join((hdr, data)))


    def close(self):
        self.r.close()


if __name__ == '__main__':
    rx = RX()
    rx.recv()

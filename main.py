from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import pyqtgraph as pg
import time, os, sys
import argparse
import pynng
import numpy as np
import scipy
import warnings
import struct
warnings.filterwarnings('ignore')


#sys.path.append(os.path.join(dir_path, '../csi_magic/'))
#import snr_engine

#fix ctrl+c
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


from scipy.signal import find_peaks
import pyaudio

def norm(h):
    h = h / np.max(h, axis=-1)[:, np.newaxis]
    h[~np.isfinite(h)] = 0
    return h



class Main(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.graph = pg.PlotWidget()
        self.graph.setYRange(0,1)
        self.plot = self.graph.plot()
        self.layout.addWidget(self.graph,0,0)
        self.graph2 = pg.PlotWidget()
        self.graph2.setYRange(0,0.25)
        self.plot2 = self.graph2.plot()
        self.layout.addWidget(self.graph2,1,0)

        self.show()

    def make_connection(self, data_object):
        data_object.signal.connect(self.grab_data)

    @pyqtSlot(object)
    def grab_data(self, data):
        h_amp, th_amp = data
        self.plot.setData(h_amp)
        self.plot2.setData(th_amp)

def P2R(radii, angles):
    return radii * np.exp(1j*angles)


fx256 = np.ones(256, dtype=bool)
fx256[:6] = False
fx256[64*4-5:] = False
fx256[32] = False
fx256[96] = False
fx256[160] = False
fx256[224] = False
for i in range(1,4):
    fx256[64*i-5:64*i+6] = False

class Worker(QThread):
    signal = pyqtSignal(object)

    def __init__(self, args):
        super().__init__()
        self.args = args
        #self.magic = snr_engine.Snr()

        p = pyaudio.PyAudio()
        self.stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=8000,
                        output=True,
                        )
                        #stream_callback=self.callback)
        #self.stream.start()

        dial = 'tcp://%s:%d' %(self.args.host, int(self.args.port))
        print(dial)
        self.sub = pynng.Sub0(dial=dial)
        self.sub.subscribe(b'')

    def callback(self, in_data, frame_count, time_info, status):
        print('callback')

    def run(self):
        cnt = 0
        last = time.time()
        peaks = []

        collect = 30
        vault = []
        sec = 0
        while True:
            cnt += 1
            raw = self.sub.recv(block=True)

            self.ver, mask, rssi, fc, mac, _seq, conf, chanspec, chip = struct.unpack('<BBbB6sHHHH',raw[:18])
            seq = _seq >> 4
            mac_str = mac.hex(':')
            count = (len(raw) - 18) // 2
            data = np.frombuffer(raw, dtype='<h', count=count, offset=18).astype(np.float32).view(np.complex64)
            assert len(data) == 256, f"Data of {len(data)} is not expected"
            pl = data[fx256]

            ######simple filter for broken chunks
            x = pl.reshape((4,-1))
            mn = np.mean(np.abs(x), axis=-1)
            msk = np.zeros(mn.shape, dtype=bool)
            msk[np.argmax(mn)] = True
            pl  = x[msk]
            pl = pl.ravel()
            ######################

            pl = np.abs(pl)
            pl = np.expand_dims(pl, axis=0)
            h_amp = norm(pl)[0]
            #h = csi.data
            #np.save('h', h, allow_pickle=False)
            #sys.exit(1)
            #normed_h = P2R(h_amp, np.angle(h))
            #mid = csi.mid if hasattr(csi, 'mid') else 0
            #nh, snrs, th = self.magic.snr_rec_theta(normed_h, mid)
            #th_mag = np.abs(th[:, :8])

            #peaks2, _ = find_peaks(h_amp, prominence=0.05)      # BEST!
            #if len(peaks2) == 0 or  np.max(peaks2) >=52: #something went seriously wrong
            #    print('WARNING', peaks2)
            #    continue

            th_mag = np.abs(np.fft.ifft(h_amp))[1:9]
            peaks.append(th_mag[0])

            #th_mag = np.zeros(52)
            #th_mag[peaks2] = 1

            if cnt & 0xf == 0: # 1KHz -> 60FPS
                self.signal.emit((h_amp, th_mag))

                # start the stream (4)
                '''
                note = np.array(peaks) * 1000
                audio = note * (2**15 - 1) / np.max(np.abs(note))


                frequency = 400 # Our played note will be 440 Hz
                fs = 8000 # 
                seconds = 1  # Note duration of 3 seconds

                # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
                t = np.linspace(0, seconds, seconds * len(peaks), False)

                # Generate a 440 Hz sine wave
                note = np.sin(frequency * t * 2 * np.pi)

                # Ensure that highest value is in 16-bit range
                audio = note * (2**15 - 1) / np.max(np.abs(note))
                audio = audio.astype(np.int16)

                res_audio = scipy.signal.resample(audio, fs)
                # Convert to 16-bit data

                print(len(audio), len(res_audio))
                self.stream.write(res_audio)

                frequency = np.mean(peaks) * 100  # Our played note will be 440 Hz
                print('freq', frequency)
                fs = 8000 # 
                seconds = 1  # Note duration of 1 seconds

                # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
                t = np.linspace(0, seconds, seconds * fs, False)

                # Generate a 440 Hz sine wave
                note = np.sin(frequency * t * 2 * np.pi)

                # Ensure that highest value is in 16-bit range
                audio = note * (2**15 - 1) / np.max(np.abs(note))
                # Convert to 16-bit data
                audio = audio.astype(np.int16)

                # Start playback
                play_obj = sa.play_buffer(audio, 1, 2, fs)
                peaks.clear()
                '''



if __name__ == "__main__": 

    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument("port", nargs='?', default='6970')
    args = parser.parse_args()


    app = QApplication(sys.argv)
    widget = Main()
    worker = Worker(args)
    widget.make_connection(worker)
    worker.start()

    sys.exit(app.exec_())

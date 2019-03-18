import os
import signal
import subprocess
import sys
import time

UPDATE_TIME = 1


def main():
    dwn = subprocess.Popen([sys.executable, 'downloader.py'])
    time.sleep(1)
    cnv = subprocess.Popen([sys.executable, 'converter.py'])
    time.sleep(1)
    msc = subprocess.Popen([sys.executable, 'mosaic.py'])
    time.sleep(1)
    sw = subprocess.Popen([sys.executable, 'show.py'])
    try:
        while True:
            try:
                if dwn.poll() is not None:
                    dwn = subprocess.Popen([sys.executable, 'downloader.py'])
                if cnv.poll() is not None:
                    cnv = subprocess.Popen([sys.executable, 'converter.py'])
                if msc.poll() is not None:
                    msc = subprocess.Popen([sys.executable, 'mosaic.py'])
                if sw.poll() is not None:
                    sw = subprocess.Popen([sys.executable, 'show.py'])
                time.sleep(UPDATE_TIME)
            except Exception as ex:
                print('Exception', str(ex))
    except KeyboardInterrupt:
        # try:
        #     dwn.send_signal(signal.CTRL_C_EVENT)
        #     time.sleep(2)
        #     dwn.terminate()
        # except KeyboardInterrupt:
        #     pass
        # try:
        #     cnv.send_signal(signal.CTRL_C_EVENT)
        #     time.sleep(2)
        #     cnv.terminate()
        # except KeyboardInterrupt:
        #     pass
        # try:
        #     msc.send_signal(signal.CTRL_C_EVENT)
        #     time.sleep(2)
        #     msc.terminate()
        # except KeyboardInterrupt:
        #     pass
        # try:
        #     sw.send_signal(signal.CTRL_C_EVENT)
        #     time.sleep(2)
        #     sw.terminate()
        # except KeyboardInterrupt:
        #     pass
        pass


if __name__ == "__main__":
    main()

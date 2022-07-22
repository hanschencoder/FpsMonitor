#!/usr/bin/env python

from optparse import OptionParser
import re
import subprocess
import time
import signal

def query_surfaceflinger_frame_count():
    parcel = subprocess.Popen("adb shell service call SurfaceFlinger 1013",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not parcel:
        raise Exception("FAILED: adb shell service call SurfaceFlinger 1013")

    framecount = re.search("Result: Parcel\\(([a-f0-9]+) ", parcel)
    if not framecount:
        raise Exception("Unexpected result from SurfaceFlinger: " + parcel)

    return int(framecount.group(1), 16)


def handler(signum, frame):
    print("handle signal")


def main(interval):
    startframe = query_surfaceflinger_frame_count()
    starttime = time.time()
    try:
        while True:
            time.sleep(interval)

            endframe = query_surfaceflinger_frame_count()
            endtime = time.time()
            fps = (endframe - startframe) / (endtime - starttime)
            print("%.2f" % fps)
            print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

            startframe = endframe
            starttime = endtime
    except:
        exit()


if __name__ == '__main__':
    # signal.signal(signal.SIGINT, handler)
    # signal.signal(signal.SIGTERM, handler)
    parser = OptionParser()
    parser.add_option("-i", "--interval", type="int", default="500", help="Interval of milliseconds to count frames")
    (options, args) = parser.parse_args()
    main(options.interval / 1000.0)

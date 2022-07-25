#!/usr/bin/env python

from optparse import OptionParser
import re
import subprocess
import time
import matplotlib.pyplot as plt
import sys
import os
from matplotlib import _pylab_helpers

sample_time = []
sample_fps = []


def query_surfaceflinger_frame_count():
    parcel = subprocess.Popen("adb shell service call SurfaceFlinger 1013",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not parcel:
        raise Exception("FAILED: adb shell service call SurfaceFlinger 1013")

    framecount = re.search("Result: Parcel\\(([a-f0-9]+) ", parcel.decode())
    if not framecount:
        raise Exception("Unexpected result from SurfaceFlinger: " + parcel.decode())

    return int(framecount.group(1), 16)


def main(interval):
    startframe = query_surfaceflinger_frame_count()
    starttime = time.time()
    begintime = starttime

    plt.ion()
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True, which='both', linestyle='--')

    try:
        while True:
            time.sleep(interval)
            manager = _pylab_helpers.Gcf.get_active()
            if manager is None:
                break

            endframe = query_surfaceflinger_frame_count()
            endtime = time.time()
            fps = (endframe - startframe) / (endtime - starttime)
            sample_time.append(endtime - begintime)
            sample_fps.append(fps)
            print("%.3f" % fps)

            ax.set_title('FPS Monitor')
            ax.set_xlabel('Time')
            ax.set_ylabel('Frame Per Second')
            ax.plot(sample_time, sample_fps, 'b-')
            fig.canvas.draw()
            plt.pause(0.001)

            startframe = endframe
            starttime = endtime
    except:
        pass

    saveData()
    plt.close()
    sys.exit()


def saveData():
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title('FPS Monitor')
    ax.set_xlabel('Time')
    ax.set_ylabel('Frame Per Second')
    ax.plot(sample_time, sample_fps, 'b-')
    plt.savefig(os.getcwd() + '/savefig.png')



if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--interval", type="int", default="500", help="Interval of milliseconds to count frames")
    (options, args) = parser.parse_args()
    main(options.interval / 1000.0)

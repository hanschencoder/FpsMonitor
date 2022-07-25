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
sample_gpu_loader = []
sample_cpu0_frequencies = []
sample_cpu4_frequencies = []
sample_cpu7_frequencies = []


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


def gete_gpu_busy():
    result = subprocess.Popen("adb shell cat /sys/class/kgsl/kgsl-3d0/gpubusy",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not result:
        raise Exception("FAILED: adb shell cat /sys/class/kgsl/kgsl-3d0/gpubusy")

    split_str = result.decode().split()
    if split_str[1] == '0':
        return 0.0
    return float(split_str[0]) / float(split_str[1]) * 100


def gete_cpu_frequencies():
    result = subprocess.Popen('''adb shell "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq && \
                                            cat /sys/devices/system/cpu/cpu4/cpufreq/scaling_cur_freq && \
                                            cat /sys/devices/system/cpu/cpu7/cpufreq/scaling_cur_freq"''',
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not result:
        raise Exception("FAILED: adb shell cat /sys/devices/system/cpu/cpu/cpufreq/scaling_cur_freq")

    return result.decode().split()


def main(interval):
    startframe = query_surfaceflinger_frame_count()
    starttime = time.time()
    begintime = starttime

    plt.ion()
    fig = plt.figure(figsize=(12, 6))
    fps_ax = fig.add_subplot(2, 2, 1)
    fps_ax.grid(True, which='both', linestyle='--')
    gpu_busy_ax = fig.add_subplot(2, 2, 3)
    gpu_busy_ax.grid(True, which='both', linestyle='--')
    cpu_frequencies_ax = fig.add_subplot(2, 2, 2)
    cpu_frequencies_ax.grid(True, which='both', linestyle='--')

    try:
        while True:
            time.sleep(interval)
            manager = _pylab_helpers.Gcf.get_active()
            if manager is None:
                break

            sample_gpu_loader.append(gete_gpu_busy())
            frequencies = gete_cpu_frequencies()
            sample_cpu0_frequencies.append(frequencies[0])
            sample_cpu4_frequencies.append(frequencies[1])
            sample_cpu7_frequencies.append(frequencies[2])

            endframe = query_surfaceflinger_frame_count()
            endtime = time.time()
            fps = (endframe - startframe) / (endtime - starttime)
            sample_time.append(endtime - begintime)
            sample_fps.append(fps)
            print("%.3f" % fps)

            fps_ax.set_title('FPS Monitor')
            fps_ax.set_ylabel('Frame Per Second')
            fps_ax.plot(sample_time, sample_fps, 'b-')

            gpu_busy_ax.set_title('GPU Busy')
            gpu_busy_ax.set_ylabel('GPU Load(%)')
            gpu_busy_ax.plot(sample_time, sample_gpu_loader, 'b-')

            cpu_frequencies_ax.set_title('CPU Frequencies')
            cpu_frequencies_ax.set_ylabel('CPU Frequencies')
            cpu_frequencies_ax.plot(sample_time, sample_cpu0_frequencies, 'r-')
            cpu_frequencies_ax.plot(sample_time, sample_cpu4_frequencies, 'g-')
            cpu_frequencies_ax.plot(sample_time, sample_cpu7_frequencies, 'b-')
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

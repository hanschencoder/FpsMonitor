#!/usr/bin/env python

from optparse import OptionParser
import re
import subprocess
import time
import matplotlib.pyplot as plt
import sys
import os
from matplotlib import _pylab_helpers
import matplotlib.animation as animation
from threading import Thread

sample_time = []
sample_fps = []
sample_gpu_load = []
sample_cpu0_frequencies = []
sample_cpu4_frequencies = []
sample_cpu7_frequencies = []
sample_memory_free = []
sample_memory_available = []

startframe = 0
starttime = 0
begintime = 0


def get_surfaceflinger_frame_count():
    parcel = subprocess.Popen("adb shell service call SurfaceFlinger 1013",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not parcel:
        print('FAILED: adb shell service call SurfaceFlinger 1013')
        return 0

    framecount = re.search("Result: Parcel\\(([a-f0-9]+) ", parcel.decode())
    if not framecount:
        print("Unexpected result from SurfaceFlinger: " + parcel.decode())
        return 0

    return int(framecount.group(1), 16)


def get_gpu_busy():
    result = subprocess.Popen("adb shell cat /sys/class/kgsl/kgsl-3d0/gpubusy",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not result:
        print('FAILED: adb shell cat /sys/class/kgsl/kgsl-3d0/gpubusy')
        return 0.0

    split_str = result.decode().split()
    if split_str[1] == '0':
        return 0.0
    return float(split_str[0]) / float(split_str[1]) * 100


def get_cpu_frequencies():
    result = subprocess.Popen('''adb shell "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq && \
                                            cat /sys/devices/system/cpu/cpu4/cpufreq/scaling_cur_freq && \
                                            cat /sys/devices/system/cpu/cpu7/cpufreq/scaling_cur_freq"''',
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not result:
        print('FAILED: adb shell cat /sys/devices/system/cpu/cpu/cpufreq/scaling_cur_freq')
        return [0, 0, 0]

    return result.decode().split()


def get_memory_info():
    result = subprocess.Popen('adb shell cat /proc/meminfo', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              shell=True).communicate()[0]
    if not result:
        raise Exception("FAILED: adb shell cat /proc/meminfo")
    return dict((i.split()[0].rstrip(':'), int(i.split()[1]) / 1024) for i in result.decode().strip().split('\n'))


def update(frame, fps_ax, gpu_busy_ax, cpu_frequencies_ax, memory_ax):

    global startframe
    global starttime

    sample_gpu_load.append(get_gpu_busy())
    frequencies = get_cpu_frequencies()
    sample_cpu0_frequencies.append(int(frequencies[0]))
    sample_cpu4_frequencies.append(int(frequencies[1]))
    sample_cpu7_frequencies.append(int(frequencies[2]))

    mem_info = get_memory_info()
    sample_memory_available.append(mem_info['MemAvailable'])
    sample_memory_free.append(mem_info['MemFree'])

    endframe = get_surfaceflinger_frame_count()
    endtime = time.time()
    fps = (endframe - startframe) / (endtime - starttime)
    startframe = endframe
    starttime = endtime

    sample_time.append(endtime - begintime)
    sample_fps.append(fps)

    display_point = -50
    time_data = sample_time[display_point:]

    fps_ax.clear()
    gpu_busy_ax.clear()
    cpu_frequencies_ax.clear()
    memory_ax.clear()

    fps_ax.grid(True, which='both', linestyle='--')
    fps_ax.set_title('Frame Per Second')
    fps_ax.set_ylim(-5, 150)
    fps_ax.plot(time_data,
                sample_fps[display_point:],
                color='b',
                marker='.',
                linestyle='solid',
                linewidth=1,
                markersize=4)

    gpu_busy_ax.grid(True, which='both', linestyle='--')
    gpu_busy_ax.set_title('GPU Load(%)')
    gpu_busy_ax.set_ylim(-5, 100)
    gpu_busy_ax.plot(time_data,
                     sample_gpu_load[display_point:],
                     color='b',
                     marker='.',
                     linestyle='solid',
                     linewidth=1,
                     markersize=4)

    cpu_frequencies_ax.grid(True, which='both', linestyle='--')
    cpu_frequencies_ax.set_title('CPU Frequencies')
    cpu_frequencies_ax.set_ylim(-100, 3000000)
    cpu_frequencies_ax.plot(time_data,
                            sample_cpu0_frequencies[display_point:],
                            label='little',
                            color='r',
                            marker='.',
                            linestyle='solid',
                            linewidth=1,
                            markersize=4)
    cpu_frequencies_ax.plot(time_data,
                            sample_cpu4_frequencies[display_point:],
                            label='big',
                            color='g',
                            marker='.',
                            linestyle='solid',
                            linewidth=1,
                            markersize=4)
    cpu_frequencies_ax.plot(time_data,
                            sample_cpu7_frequencies[display_point:],
                            label='prime',
                            color='b',
                            marker='.',
                            linestyle='solid',
                            linewidth=1,
                            markersize=4)
    cpu_frequencies_ax.legend()

    memory_ax.grid(True, which='both', linestyle='--')
    memory_ax.set_title('Memory(MB)')
    # memory_ax.set_ylim(-100, 1024 * 16)
    memory_ax.plot(time_data,
                   sample_memory_available[display_point:],
                   label='available',
                   color='r',
                   marker='.',
                   linestyle='solid',
                   linewidth=1,
                   markersize=4)
    memory_ax.plot(time_data,
                   sample_memory_free[display_point:],
                   label='free',
                   color='b',
                   marker='.',
                   linestyle='solid',
                   linewidth=1,
                   markersize=4)
    memory_ax.legend()


def startAnimation(interval):

    global startframe
    global starttime
    global begintime
    startframe = get_surfaceflinger_frame_count()
    starttime = time.time()
    begintime = starttime

    fig = plt.figure(figsize=(12, 6), facecolor=None, frameon=True, edgecolor='green')
    fps_ax = fig.add_subplot(2, 2, 1)
    gpu_busy_ax = fig.add_subplot(2, 2, 3)
    cpu_frequencies_ax = fig.add_subplot(2, 2, 2)
    memory_ax = fig.add_subplot(2, 2, 4)

    ani = animation.FuncAnimation(fig,
                                  update,
                                  interval=interval,
                                  fargs=(fps_ax, gpu_busy_ax, cpu_frequencies_ax, memory_ax))
    plt.show()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--interval", type="int", default="50", help="Interval of milliseconds to count frames")
    (options, args) = parser.parse_args()
    startAnimation(options.interval)

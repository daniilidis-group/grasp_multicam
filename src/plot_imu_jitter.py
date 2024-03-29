#!/usr/bin/env python
#------------------------------------------------------------------------------
# plot IMU time stamp jitter

import sys, rosbag, rospy, numpy as np
import tf2_msgs
import tf.transformations
import argparse
import math
import matplotlib.pyplot as plt


def read_bag(bagfile, topic):
    x = []
    with rosbag.Bag(bagfile, 'r') as bag:
        iterator = bag.read_messages(topics=[topic])
        for (topic, msg, t) in iterator:
            x.append(([msg.header.stamp.to_sec()]))
    return np.asarray(x)

def plot_ts(x):
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 36}

    plt.rc('font', **font)
    plt.plot(x[:-1,0]-x[0,0],x[1:,0] - x[:-1,0],'.')
    plt.gca().set_xlabel('time [s]')
    plt.gca().set_ylabel('inter time stamp difference [s]')
    plt.gca().set_title('Falcam time stamp fluctuations')
    plt.show() 


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='plot_odom.')
    parser.add_argument('--topic', '-t', action='store', required=True,
                        help='ROS odom topic')

    parser.add_argument('bagfile')
    
    args = parser.parse_args()

    x_arr = read_bag(args.bagfile, args.topic);
    plot_ts(x_arr)

#!/usr/bin/env python
#------------------------------------------------------------------------------
# removes static transforms 
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import copy
import yaml
import re
import numpy as np
import geometry_msgs
import sensor_msgs
import tf2_msgs
import time
import make_caminfo_msg

from rosbag import Bag

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='replace or add static transform in bag')
    parser.add_argument(
        '--start', '-s', action='store', default=0.0, type=float,
        help='Rostime (bag time, large number!) representing start time.')
    parser.add_argument(
        '--end', '-e', action='store', default=1e60, type=float,
        help='Rostime (bag time, large number!) representing stop time.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    rospy.init_node('remove_static_tf')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            last_percent = 0
            t0 = time.time()
            start_time = max([inbag.get_start_time(), args.start])
            end_time   = min([inbag.get_end_time(), args.end])
            total_time = end_time - start_time
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages(
                    start_time=rospy.Time(args.start),
                    end_time=rospy.Time(args.end)):
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) / percent_done
                    print "done: %5.0f%%, expected time remaining: %5.0fs" % (
                        percent_done, time_left)
                if not topic == '/tf_static':
                    outbag.write(topic, msg, t)
                if rospy.is_shutdown():
                    break

        outbag.close()
                    

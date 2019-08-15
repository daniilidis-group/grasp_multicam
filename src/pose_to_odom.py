#!/usr/bin/env python
#------------------------------------------------------------------------------
# converts pose to odometry messages
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import yaml
import numpy as np
import geometry_msgs
import sensor_msgs
import nav_msgs.msg
import tf2_msgs
import time

from rosbag import Bag

def pose_to_odom(p, parent_frame, child_frame):
    m = nav_msgs.msg.Odometry()
    m.header = p.header
    m.header.frame_id= parent_frame
    m.child_frame_id = child_frame
    m.pose.pose     = p.pose
    return m

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='convert pose to odometry messages')
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
    parser.add_argument(
        '--pose_topic',  action='store', default=None, required=True,
        help='name of pose topic.')
    parser.add_argument(
        '--odom_topic',  action='store', default=None, required=True,
        help='name of odom topic.')
    parser.add_argument(
        '--child_frame',  action='store', default=None, required=True,
        help='frame id of child frame.')
    parser.add_argument(
        '--parent_frame',  action='store', default=None, required=True,
        help='frame id of parent frame.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    rospy.init_node('pose_to_odometry_message')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            last_percent = 0
            t0 = time.time()
            start_time = max([inbag.get_start_time(), args.start])
            end_time   = min([inbag.get_end_time(), args.end])
            total_time = end_time - start_time
            first_time = True
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages(
                    topics=(args.pose_topic),
                    start_time=rospy.Time(args.start),
                    end_time=rospy.Time(args.end)):
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) / percent_done
                    print "done: %5.0f%%, expected time remaining: %5.0fs" % (
                        percent_done, time_left)

                odom_msg = pose_to_odom(msg, args.parent_frame,
                                        args.child_frame)
                outbag.write(args.odom_topic, odom_msg, t)
                if rospy.is_shutdown():
                    break

        outbag.close()
                    

#!/usr/bin/env python
#
# This code was lifted and hacked. The original is from:
#
# https://github.com/OSUrobotics/bag2video
#

from __future__ import division
import rosbag, rospy, numpy as np
import sys, os, cv2, glob
import argparse
from cv_bridge import CvBridge

def get_info(bag, topic=None, start_time=rospy.Time(0),
             stop_time=rospy.Time(sys.maxint)):
    bridge = CvBridge()
    # read the first message to get the image size
    print 'topic: ', topic
    it = bag.read_messages(topics=[topic]).next()
 
    if it == None:
        raise 'no images in bag for topic: ', topic

    msg = it[1]
    size = (msg.width, msg.height)


    # now read the rest of the messages for the rate
    iterator = bag.read_messages(topics=[topic],
                                 start_time=start_time, end_time=stop_time)
    times = []
    for _, msg, _ in iterator:
        time = msg.header.stamp
        times.append(time.to_sec())
    tick = 1000
    fps = round(len(times)*tick/(max(times)-min(times)))/tick
    print 'number of frames: ', len(times)
    return fps, size

def write_frames(bag, writer, topic=None,
                 start_time=rospy.Time(0), stop_time=rospy.Time(sys.maxint)):
    iterator = bag.read_messages(topics=[topic],
                                 start_time=start_time, end_time=stop_time)
    for (topic, msg, time) in iterator:
        img = bridge.imgmsg_to_cv2(msg, 'bgr8')
        writer.write(img)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='maket video from bag files.')
    parser.add_argument('--outfile', '-o', action='store', default=None,
                        help='Destination of the video file.')
    parser.add_argument('--start', '-s', action='store',
                        default=rospy.Time(0), type=rospy.Time,
                        help='Rostime representing where to start in the bag.')
    parser.add_argument(
        '--end', '-e', action='store', default=rospy.Time(sys.maxint),
        type=rospy.Time, help='Rostime representing where to stop in the bag.')
    parser.add_argument(
        '--topic', '-t', action='store', default=None, required=True,
        help='ROS image topic')

    parser.add_argument('bagfile')

    args = parser.parse_args()

    bridge = CvBridge()

    for bagfile in glob.glob(args.bagfile):
        print "working on %s" % bagfile
        outfile = args.outfile
        if not outfile:
            outfile = os.path.join(*os.path.split(bagfile)[-1].split('.')[:-1]) + '.mp4'
        bag = rosbag.Bag(bagfile, 'r')
        print 'calculating video properties'
        fps, size = get_info(
            bag, args.topic, start_time=args.start, stop_time=args.end)
        print 'writing video to file %s with rate %.10f/sec, size: %s' % (
            outfile, fps, str(size))
        
        writer = cv2.VideoWriter(
            outfile, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

        write_frames(bag, writer, topic=args.topic,
                     start_time=args.start, stop_time=args.end)
        writer.release()

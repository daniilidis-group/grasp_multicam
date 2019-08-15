#!/usr/bin/env python
#------------------------------------------------------------------------------
# compute odometry statistics from bag
#
# For the path length, anything less than 2cm is considered noise and
# ignored
#

import sys, rosbag, rospy, numpy as np
import tf2_msgs
import tf.transformations
import argparse
import math
import matplotlib.pyplot as plt


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

def pose_to_matrix(pose):
    p = pose.position
    q = pose.orientation
    T = tf.transformations.quaternion_matrix(np.asarray([q.x, q.y, q.z, q.w]))
    T[0:3,3] = np.asarray([p.x, p.y, p.z])
    return T

def write_frames(bag, writer, topic=None,
                 start_time=rospy.Time(0), stop_time=rospy.Time(sys.maxint)):
    for (topic, msg, time) in iterator:
        img = bridge.imgmsg_to_cv2(msg, 'bgr8')
        writer.write(img)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='compute statistics for odom.')
    parser.add_argument('--start', '-s', action='store',
                        default=rospy.Time(0), type=rospy.Time,
                        help='Rostime representing where to start in the bag.')
    parser.add_argument('--end', '-e', action='store',
                        default=rospy.Time(sys.maxint),
                        type=rospy.Time,
                        help='Rostime representing where to stop in the bag.')
    parser.add_argument('--threshold', '-x', action='store', default=0.02, type=float,
                        help='threshold for detecting movement.')
    parser.add_argument('--topic', '-t', action='store', required=True,
                        help='ROS odom topic')

    parser.add_argument('bagfile')
    
    args = parser.parse_args()

    dist = 0
    num_points = 0
    with rosbag.Bag(args.bagfile, 'r') as bag:
        t0, last_time, last_pose = None, None, None
        iterator = bag.read_messages(topics=[args.topic],start_time=args.start,
                                     end_time=args.end)
        d_list = []
        for (topic, msg, t) in iterator:
            T = pose_to_matrix(msg.pose.pose)
            if not last_time:
                t0 = t
                last_time = t
                last_pose = T
                continue
            delta_pose = np.matmul(
                tf.transformations.inverse_matrix(last_pose), T)
            d = np.linalg.norm(delta_pose[0:3,3])
            if d > args.threshold:
                d_list.append(d)
                dist = dist + np.linalg.norm(delta_pose[0:3,3])
                num_points = num_points + 1
                last_time = t
                last_pose = T
        print 'noise threshold: ', args.threshold
        print 'total number of points: ', num_points
        print 'total path length: ', dist
        d_arr = np.asarray(d_list)
        print 'noise avg: ', np.mean(d_arr)
        print 'noise stdv: ', np.std(d_arr)
        np.histogram(d_arr, 100)
        plt.hist(d_arr, bins='auto')
        plt.title('frame-to-frame traveled distance [m]')
        plt.show()

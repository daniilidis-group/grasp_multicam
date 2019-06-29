#!/usr/bin/env python
#------------------------------------------------------------------------------
# compute odometry statistics from bag
#
#

import sys, rosbag, rospy, numpy as np
import tf2_msgs
import tf.transformations
import argparse



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
    parser.add_argument('--topic', '-t', action='store', required=True,
                        help='ROS odom topic')

    parser.add_argument('bagfile')
    
    args = parser.parse_args()

    dist = 0
    with rosbag.Bag(args.bagfile, 'r') as bag:
        t0, last_time, last_pose = None, None, None
        iterator = bag.read_messages(topics=[args.topic],start_time=args.start,
                                     end_time=args.end)
        for (topic, msg, t) in iterator:
            T = pose_to_matrix(msg.pose.pose)
            if not last_time:
                t0 = t
                last_time = t
                last_pose = T
                continue
            delta_pose = np.matmul(
                T, tf.transformations.inverse_matrix(last_pose))
            last_pose = T
            dist = dist + np.linalg.norm(delta_pose[0:3,3])
            #np.linalg.norm(delta_pose[0:3,3]), 
            print msg.header.stamp, T[0:3,3],np.linalg.norm(delta_pose[0:3,3]) #delta_pose[0:3,3], np.linalg.norm(delta_pose[0:3,3])
#            delta_pose[0:3,3]
    print 'total path length: ', dist
    

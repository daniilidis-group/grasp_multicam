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


def pose_to_matrix(pose):
    p = pose.position
    q = pose.orientation
    T = tf.transformations.quaternion_matrix(np.asarray([q.x, q.y, q.z, q.w]))
    T[0:3,3] = np.asarray([p.x, p.y, p.z])
    return T

def read_bag(bagfile, topic, start, stop):
    x = []
    with rosbag.Bag(bagfile, 'r') as bag:
        last_time, last_pose = None, None
        iterator = bag.read_messages(topics=[topic],start_time=start,
                                     end_time=stop)
        for (topic, msg, t) in iterator:
            T = pose_to_matrix(msg.pose.pose)
            p = T[0:3,3]
            if not last_time:
                t0 = t
                last_time = msg.header.stamp
                last_pose = T
                continue
            d = p - last_pose[0:3, 3]
            delta_pose = np.matmul(
                tf.transformations.inverse_matrix(last_pose), T)
            ang, direc, pt = tf.transformations.rotation_from_matrix(
                delta_pose)
            da = ang * direc
            dt = (msg.header.stamp - last_time).to_sec()
            last_time = msg.header.stamp
            last_pose = T
            x.append(([msg.header.stamp.to_sec()] + p.tolist()
                      + d.tolist() + da.tolist()))
    return np.asarray(x)

def get_speed_stats(x, dt):
    t_tot = x[-1,0] - x[0,0]
    print 'total time: ', t_tot
    n = x.shape[0]/int(t_tot/dt)
    print 'num intervals: ', n
    # take difference over interfal
    x_diff = x[n:,:] - x[:-n,:]
    # angle already has diffs, must sum
    x_diff[:,6:9] = np.cumsum(x_diff[:,6:9],axis=0)
    # divide by time difference to get velocities
    v = x_diff/np.expand_dims(x_diff[:,0], 1)
    # linear velocity
    v_abs = np.abs(np.linalg.norm(v[:,1:4],axis=1))
    v_max = np.max(v_abs)
    # angular velocity
    w_abs = np.abs(np.linalg.norm(v[:,6:9],axis=1))
    w_max = np.max(w_abs)
    # time diff
    dt_avg = np.mean(x_diff[:,0])
    # traveled distance (binned!)
    dist_smoothed = np.sum(v_abs * x_diff[:,0] / float(n))
    # z range
    z_range = np.ptp(x[:,3]) # peak-to-peak
    #    plt.hist(v_abs, bins = 50)
    #    plt.hist(x_diff[0,:], bins = 100)
    font = {'family' : 'DejaVu Sans',
            'weight' : 'bold',
            'size'   : 36}

    plt.rc('font', **font)
    plt.plot(x[:-1,0]-x[0,0],x[1:,0] - x[:-1,0],'.')
    plt.gca().set_xlabel('time [s]')
    plt.gca().set_ylabel('inter time stamp difference [s]')
    plt.gca().set_title('OVC time stamp fluctuations')
    plt.show() 
    return t_tot, dt_avg, v_max, w_max, np.median(v_abs), np.median(w_abs), \
        z_range, dist_smoothed
    
def print_formatted(t_tot, dist_smoothed, z_range, v_median, v_max, w_median, w_max):
    print '<tr><td>duration: %.0fs</td></tr>' % t_tot
    print '<tr><td>approx path length: %.0fm</td><td>altitude difference: %.2fm</td></tr>' \
        % (dist_smoothed, z_range)
    print '<tr>\n<td>median/maximum velocity: %.2f / %.2f m/s</td>' % (v_median, v_max)
    print '<td>median/maximum angular velocity: %.2f / %.2f rad/s</td>\n</tr>' %(w_median, w_max)

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
    parser.add_argument('--time_avg', '-a', action='store',
                        default=1.0, type=float,
                        help='time avg delta_time for velocities.')
    parser.add_argument('--topic', '-t', action='store', required=True,
                        help='ROS odom topic')

    parser.add_argument('bagfile')
    
    args = parser.parse_args()

    x_arr = read_bag(args.bagfile, args.topic, args.start, args.end);
    t_tot, dt_avg, v_max, w_max, v_median, w_median, z_range, dist_smoothed \
        = get_speed_stats(x_arr, args.time_avg)
    
    print 'total number of points: ', x_arr.shape[0]
    print 'total path length: ', dist_smoothed
    print 'altitude: ', z_range
    print 'median velocity:  ', v_median, 'm/s'
    print 'max velocity:     ', v_max, 'm/s'
    print 'median ang velocity:  ', w_median, 'rad/s'
    print 'max ang velocity:     ', w_max, 'rad/s'
    print 'time averaging length: ', dt_avg, 's'

    print_formatted(t_tot, dist_smoothed, z_range, v_median, v_max, w_median, w_max)

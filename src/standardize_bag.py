#!/usr/bin/env python
#

#
# process bags such that they are in standard form
#

import rospy
import argparse
import copy
from fnmatch import fnmatchcase
from rosbag import Bag


topic_map = {
    '/fla/monstar/camera_info':        {'name': '/monstar/camera_info'},
    '/fla/monstar/image_depth':        {'name': '/monstar/image_depth'},
    '/fla/monstar/image_depth':        {'name': '/monstar/image_depth'},
    '/fla/monstar/image_mono16':       {'name': '/monstar/image_mono16'},
    '/fla/monstar/image_mono8':        {'name': '/monstar/image_mono8'},
    '/fla/monstar/image_noise':        {'name': '/monstar/image_noise'},
    '/fla/monstar/points':             {'name': '/monstar/points'},
    '/fla/ovc_node/imu':               {'name': '/ovc/imu'},
    '/fla/ovc_node/image_metadata':    {'name': '/ovc/image_metadata'},
    '/fla/ovc_node/left/camera_info':  {'name': '/ovc/cam_0/camera_info'},
    '/fla/ovc_node/left/image_raw':    {'name': '/ovc/cam_0/image_raw'},
    '/fla/ovc_node/right/camera_info': {'name': '/ovc/cam_1/camera_info'},
    '/fla/ovc_node/right/image_raw':   {'name': '/ovc/cam_1/image_raw'},
    '/fla/vio/odom':                   {'name': '/ovc/vio/odom'},
    '/tf':                             {'name': '/tf'},
    '/tf_static':                      {'name': '/tf_static'}
}


#
# static transforms:
#
# imu -> cam_0 -> cam_1 -> monstar
# ovc/vio_map -> ovc/vio_vision  [90 degree yaw rotation]
#
# non-static transforms:
#
# ovc onboard vio:  ovc/vio_map -> base_link
# offline     vio:  vio_map     -> base_link
#
# odometry:
#
# ovc odom:   vio_vision -> ovc/vio_odom
#
#
# The ovc/vio_odom and ovc/imu frames are identical:
#
#     ovc/vio_odom comes from the vio odometry message
#     ovc/imu      comes from the vio tf which establishes base_link
#
#

frame_id_map = {
    'fla/left_cam':  'ovc/cam_0',
    'fla/right_cam': 'ovc/cam_1',
    'fla/front_imu': 'ovc/imu',
    'fla/rgbd':      'monstar',
    'map':           'map',
    'odom':          'online/vio_odom',
    'vision':        'vision',
}

empty_frame_id_map = {
    '/fla/ovc_node/imu': 'ovc/imu'
}


                                                                                              
                                                                                            
mapped_topics = topic_map.keys()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Turn bag into standard form.')
    parser.add_argument('--start', '-s', action='store', default=0.0, type=float,
                        help='Rostime (bag time, large number!) representing where to start in the bag.')
    parser.add_argument('--end', '-e', action='store', default=1e60, type=float,
                        help='Rostime (bag time, large number!) representing where to stop in the bag.')
    parser.add_argument('--freq', '-f', action='store', default=20, type=float,
                        help='frequency in hz of camera messages.')
    parser.add_argument('--outbag', '-o', action='store', default=None, required=True,
                        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()


    dt_expected  = 1.0/args.freq
    dt_ratio_max = 0.0
    tlast = None
    last_percent = 0
    
    rospy.init_node('standardize_bag')
    with Bag(args.outbag, 'w') as outbag:
        with Bag(args.bagfile, 'r') as inbag:
            t0 = rospy.get_rostime()
            start_time = max([inbag.get_start_time(), args.start])
            end_time   = min([inbag.get_end_time(), args.end])
            total_time = end_time - start_time
            static_tf_time, static_tf_msg = 0, None # only one static transform allowed
            
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages(start_time=rospy.Time(args.start), end_time=rospy.Time(args.end)):
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = rospy.get_rostime()
                    time_left = (100 - percent_done) * (t1-t0).to_sec() / percent_done
                    print "percent done: %5.0f, expected time remaining: %5.0fs" % (percent_done, time_left)
                #
                # test for bad time stamps
                #
                if (fnmatchcase(topic, '/fla/ovc_node/left/image_raw')):
                    if tlast:
                        dt = msg.header.stamp - tlast
                        dt_ratio = (dt.to_sec() - dt_expected)/dt_expected
                        if (dt_ratio > dt_ratio_max):
                            print "new max dt at time t=", t, " dt = %.4f frames" % dt_ratio
                            dt_ratio_max = dt_ratio
                    tlast = msg.header.stamp
                #
                # now remap topics
                #
                if topic not in mapped_topics:
                    continue
                t_mapped = topic_map[topic]['name']

                #
                # deal with transforms
                #
                if topic == '/tf':
                    continue # drop all transforms
                    for tf in msg.transforms:
                        if tf.child_frame_id in frame_id_map and tf.header.frame_id in frame_id_map:
                            tf.child_frame_id  = frame_id_map[tf.child_frame_id]
                            tf.header.frame_id = frame_id_map[tf.header.frame_id]
#                            print "DROPPING TRANSFORM: "
#                            print tf
                elif topic == '/tf_static':
#                    print "got static tf: "
#                    print msg
                    if not static_tf_msg:
                        static_tf_time = t
                        static_tf_msg = copy.deepcopy(msg)
                        static_tf_msg.transforms = []
                        
                    for tf in msg.transforms:
                        if tf.child_frame_id in frame_id_map and tf.header.frame_id in frame_id_map:
                            tf.child_frame_id  = frame_id_map[tf.child_frame_id]
                            tf.header.frame_id = frame_id_map[tf.header.frame_id]
                            static_tf_msg.transforms.append(tf)
                        else:
                            print "DROPPING STATIC TRANSFORM: "
                            print tf
                    continue
                elif topic == '/fla/vio/odom':
#                    pass
                    continue # drop all odom
                else:
                    if hasattr(msg, 'header'):
                        if msg.header.frame_id == '':
                            msg.header.frame_id = empty_frame_id_map[topic]
                        elif msg.header.frame_id in frame_id_map:
                            msg.header.frame_id = frame_id_map[msg.header.frame_id]
                        else:
                            print "DROPPING MESSAGE:"
                            print msg
                            continue
                        if topic == '/fla/monstar/points':
                            msg.header.stamp = msg.header.stamp
                            # t = t - rospy.Duration(0.15)
                            # print (msg.header.stamp - t).to_sec()
                    else:
                        print "DROPPING MESSAGE WITH NO HEADER: "
                        print msg
                        continue
                outbag.write(t_mapped, msg, t)
            if static_tf_msg:
                outbag.write('/tf_static', static_tf_msg, rospy.Time(inbag.get_start_time()))
            print "wrote static msg: ", static_tf_time
            print static_tf_msg

        outbag.close()
                    

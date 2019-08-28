#!/usr/bin/env python
#------------------------------------------------------------------------------
# adjust point cloud to match camerainfo
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import time
import read_calib


from rosbag import Bag
from collections import defaultdict
from point_cloud_adjuster import PointCloudAdjuster


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='adjust pointcloud to match calibration.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument(
        '--calib',  action='store', default=None, required=True,
        help='name of calibration file')
    parser.add_argument(
        '--id_map',  action='store', default=None, required=True,
        help='name of topic_to_id yaml file')
    parser.add_argument(
        '--depth_sensor',  action='store', default='/monstar',
        help='ros name of depth sensor, e.g. /monstar')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    points_cinfo_topic = args.depth_sensor + '/image_mono8'
    
    topic_to_id_map = read_calib.read_yaml(args.id_map)
    static_transforms, camera_infos = read_calib.read_calib(
        args.calib, topic_to_id_map)
    adjuster = PointCloudAdjuster(camera_infos[args.depth_sensor + '/camera_info'])
    
    rospy.init_node('adjust_pointcloud')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            time_to_data = defaultdict(dict)
            last_percent = 0
            t0 = time.time()
            start_time = inbag.get_start_time()
            end_time   = inbag.get_end_time()
            total_time = end_time - start_time
            first_time = True
            depth_topic  = args.depth_sensor + '/image_depth'
            points_topic = args.depth_sensor + '/points'
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages():
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) / percent_done
                    print "done: %5.0f%%, expected time remaining: %5.0fs" % (
                        percent_done, time_left)
                if topic == depth_topic:
                    time_to_data[msg.header.stamp][topic] = msg
                    outbag.write(topic, msg, t) # can write immediately
                elif topic == points_topic:
                    time_to_data[msg.header.stamp][topic] = msg
                    # don't write, need to wait for depth image and point cloud
                else:
                    outbag.write(topic, msg, t)
                #
                # write adjusted point cloud to bag
                #
                if hasattr(msg, 'header') and len(
                        time_to_data[msg.header.stamp]) == 2:
                    msg = adjuster.adjust(
                        time_to_data[msg.header.stamp][depth_topic],
                        time_to_data[msg.header.stamp][points_topic])
                    # write adjusted points
                    outbag.write(points_topic, msg, t)
                    time_to_data.pop(msg.header.stamp)
                if rospy.is_shutdown():
                    break

        outbag.close()
                    

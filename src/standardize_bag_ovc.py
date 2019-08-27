#!/usr/bin/env python
#------------------------------------------------------------------------------
# process bags such that they are in standard form
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import copy
import time
import numpy as np
from fnmatch import fnmatchcase
from rosbag import Bag
from collections import defaultdict

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
}



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
    '/fla/ovc_node/imu': 'ovc/imu',
    '/fla/ovc_node/left/camera_info': 'ovc/cam_0',
    '/fla/ovc_node/right/camera_info': 'ovc/cam_1',
    '/fla/monstar/camera_info': 'monstar'
}


def is_image_with_bad_timestamp(topic, msg, bad_ts):
    if (not fnmatchcase(topic, '/fla/ovc_node/left/image_raw') and
        not fnmatchcase(topic, '/fla/ovc_node/right/image_raw')):
        return False
    t = msg.header.stamp
    if t in bad_ts:
        print "WARN: dropping bad frame: ", t.to_sec(), ' topic: ', topic
        return True
    return False


def analyze_time_stamps(bag_name, freq):
    print 'finding adjust time and bad time stamps ...'
    ts = defaultdict(list)

    with Bag(bag_name, 'r') as inbag:
        min_time_diff = rospy.Duration(1e10)
        t0 = time.time()
        start_time = inbag.get_start_time()
        end_time   = inbag.get_end_time()
        total_time = end_time - start_time
        last_percent = 0
        print "total time span to be processed: %.2fs" % total_time
        for topic, msg, t in inbag.read_messages():
            percent_done = (t.to_sec() - start_time)/total_time * 100
            if (percent_done - last_percent > 5.0):
                last_percent = percent_done
                t1 = time.time()
                time_left = (100 - percent_done) * (t1-t0) / percent_done
                print ("percent done: %5.0f, expected time " + \
                       "remaining: %5.0fs") % (percent_done, time_left)
            if hasattr(msg, 'header'):
                ts[topic].append(msg.header.stamp)
                dt = t - msg.header.stamp
                if dt < min_time_diff:
                    min_time_diff = dt
                    print 'min time diff: ', min_time_diff.to_sec()
            if rospy.is_shutdown():
                break
    print 'time shift: ', min_time_diff.to_sec()
    bad_stamps = []; bad_diffs = []
    for tp in ('/fla/ovc_node/left/image_raw',
               '/fla/ovc_node/right/image_raw'):
        tss = np.asarray(ts[tp])
        tsd = np.diff(tss)
        idx = np.where((tsd > rospy.Duration(1.5 * 1.0/freq)) |
                       (tsd < rospy.Duration(0.1 * 1.0/freq)))
        # add 1 to index to skip *subsequent* frame
        idxp   = [i + 1 for i in idx]
        bad_stamps = bad_stamps + (tss[idxp]).tolist()
        bad_diffs = bad_diffs + (tsd[idx]).tolist()

    for i in range(0, len(bad_stamps)):
        print 'bad time stamp: %f   dt = %f' % (
            bad_stamps[i].to_sec(), bad_diffs[i].to_sec())
            
    return min_time_diff, sorted(bad_stamps)

def is_duplicate_imu_timestamp(topic, msg, imu_ts):
    if not topic == '/fla/ovc_node/imu':
        return False
    t = msg.header.stamp
    if t in imu_ts:
        print 'WARN: duplicate IMU time stamp: ', t.to_sec()
        return True
    imu_ts.add(t)
    return False
        




mapped_topics = topic_map.keys()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert bag to standard form.')
    parser.add_argument(
        '--start', '-s', action='store', default=0.0, type=float, help=
        'ros time (bag time, large number!) where to start in the bag.')
    parser.add_argument(
        '--end', '-e', action='store', default=1e60, type=float, help=
        'ros time (bag time, large number!) where to stop in the bag.')
    parser.add_argument('--freq', '-f', action='store', default=20, type=float,
                        help='frequency in hz of camera messages.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument(
        '--adjust_time', '-a', action='store', type=bool, default=False,
        required=False, help='if time should be adjusted.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    
    rospy.init_node('standardize_bag')

    adjust_time, bad_ts = analyze_time_stamps(args.bagfile, args.freq)

    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            t0 = time.time()
            start_time = max([inbag.get_start_time(), args.start])
            end_time   = min([inbag.get_end_time(), args.end])
            total_time = end_time - start_time
            last_percent = 0
            imu_ts=set()
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages(
                    start_time=rospy.Time(args.start),
                    end_time=rospy.Time(args.end)):
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) / percent_done
                    print ("percent done: %5.0f, expected time " + \
                        "remaining: %5.0fs") % (percent_done, time_left)
                t_adj = (t - adjust_time) if args.adjust_time else t
                #
                # test for bad time stamps
                #
                if is_image_with_bad_timestamp(topic, msg, bad_ts):
                    print 'dropped msg with bad time stamp: ', \
                        topic, msg.header.stamp.to_sec()
                    continue
                if is_duplicate_imu_timestamp(topic, msg, imu_ts):
                    print 'dropped duplicate imu time stamp: ', \
                        topic, msg.header.stamp.to_sec()
                    continue
                #
                # now remap topics
                #
                if topic not in mapped_topics:
                    continue
                tp_mapped = topic_map[topic]['name']
                #
                # remap frame ids
                #
                if hasattr(msg, 'header'):
                    if msg.header.frame_id == '':
                        msg.header.frame_id = empty_frame_id_map[topic]
                    elif msg.header.frame_id in frame_id_map:
                        msg.header.frame_id = frame_id_map[msg.header.frame_id]
                    else:
                        print "DROPPING MESSAGE:"
                        print msg
                        continue
                else:
                    print "DROPPING MESSAGE WITH NO HEADER: "
                    print msg
                    continue
                outbag.write(tp_mapped, msg, t - adjust_time)

                if rospy.is_shutdown():
                    break

        outbag.close()
                    

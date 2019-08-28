#!/usr/bin/env python
#------------------------------------------------------------------------------
# add or replace camerainfo with calibration data
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import time
import re
from rosbag import Bag

import make_caminfo_msg
import read_calib


rep={"image_raw": "camera_info",
     "image_depth": "camera_info",
     "image_noise": "camera_info",
     "image_mono8": "camera_info",
     "image_raw": "camera_info"}
rep = dict((re.escape(k), v) for k, v in rep.iteritems())
pattern = re.compile("|".join(rep.keys()))

def replace_camera_info(topic, msg, camera_infos):
    caminfo_topic = pattern.sub(lambda m: rep[re.escape(m.group(0))], topic)
    mmsg = camera_infos[caminfo_topic]
    mmsg.header = msg.header
    
    return caminfo_topic, mmsg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='add or replace camerainfo with calibration file.')
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
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()
    topic_to_id_map = read_calib.read_yaml(args.id_map)
    static_transforms, camera_infos = read_calib.read_calib(
        args.calib, topic_to_id_map)

    rospy.init_node('replace_camerainfo')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
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
                    print "done: %5.0f%%, expected time remaining: %5.0fs" % (
                        percent_done, time_left)
                if hasattr(msg, 'roi'): # must be camerainfo, drop
                    continue
                if hasattr(msg, 'encoding'): # must be image, add camerainfo
                    caminfo_topic, caminfo_msg = replace_camera_info(
                        topic, msg, camera_infos)
                    outbag.write(caminfo_topic, caminfo_msg, t)
                
                outbag.write(topic, msg, t)
                if rospy.is_shutdown():
                    break

        outbag.close()
                    

#!/usr/bin/env python
#
# merge two bags into one (and bump the chunk size along with it)
#

import rospy
import argparse
from rosbag import Bag

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge two bags.')
    parser.add_argument('--outbag', '-o', action='store', default=None,
                        required=True, help='name of output bag.')
    parser.add_argument('--chunk_size', '-c', action='store', type=int,
                        default=10000000, required=False,
                        help='chunk size of output bag.')
    parser.add_argument('bagfile1')
    parser.add_argument('bagfile2')

    args = parser.parse_args(rospy.myargv()[1:])


    with Bag(args.outbag, 'w', chunk_threshold=args.chunk_size) as outbag:
        with Bag(args.bagfile1, 'r') as inbag1:
            for topic, msg, t in inbag1.read_messages():
                outbag.write(topic, msg, t)
            inbag1.close()
        with Bag(args.bagfile2, 'r') as inbag2:
            for topic, msg, t in inbag2.read_messages():
                outbag.write(topic, msg, t)
            inbag2.close()
        outbag.close()
                    

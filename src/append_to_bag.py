#!/usr/bin/env python
#------------------------------------------------------------------------------
#
# append one bag to another one. This is faster than merge, but riskier
#

import rospy
import argparse
from rosbag import Bag

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='append bag2 to bag1.')
    parser.add_argument('bagfile1')
    parser.add_argument('bagfile2')

    args = parser.parse_args(rospy.myargv()[1:])


    with Bag(args.bagfile1, 'a') as inbag1:
        with Bag(args.bagfile2, 'r') as inbag2:
            for topic, msg, t in inbag2.read_messages():
                inbag1.write(topic, msg, t)
            inbag2.close()
        inbag1.close()
                    

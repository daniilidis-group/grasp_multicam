---
date: 2016-03-09T00:11:02+01:00
title: How to use
weight: 10
---

# Installation

Grab the repo from github and clone it into the "src" directory of
your ROS/catkin workspace:
    
	cd ~/catkin_ws/src
    git clone https://github.com/daniilidis-group/grasp_multicam.git

Build it:

    catkin config -DCMAKE_BUILD_TYPE=Release
	catkin build

Source it:

    source ../devel/setup.bash


# Merging bags

For 3D reconstruction, you will want to merge the odometry data with
the raw bag. Here is an example of how to do this:


    rosrun grasp_multicam merge_bags.py --outbag merged.bag 2018-11-09-11-00-28_raw_data.bag 2018-11-09-11-00-28_odom.bag


This will create a new bag ``merged.bag`` that has the combined topics.

# Visualizing the point cloud

To play the merged bag and visualize it with rviz:

    rosparam set use_sim_time true
	rviz -d `rospack find grasp_multicam`/config/grasp_multicam.rviz
	roslaunch grasp_multicam transform_point_cloud.launch
	rosbag play --clock merged.bag

Running the ``transform_point_cloud`` node is necessary to get
accurate reconstruction. This is for two reasons:

- the processing in the depth sensor driver (the "libroyal"
  propriertary part) causes a delay of the depth sensor data with
  respect to the IMU/camera data.
- Rviz seems to use arrival time rather than message time (aka
  header.stamp) when rendering point clouds.


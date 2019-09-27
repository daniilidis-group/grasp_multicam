---
title: GRASP MultiCam
type: index
weight: 0
---
![header](media/landing_page.jpg)
## The GRASP MultiCam Data Set

The GRASP MultiCam data set combines recorded images from a
synchronized stereo monochrome camera and IMU  with those from a depth
sensor. The stereo camera / IMU device allows for accurate
Visual-Inertial Odometry (VIO), which can then be used to recover 3D
structure from the depth sensor point clouds.

The data covers indoor and outdoor scenes. The recording devices are
always carried by hand. All data is in ROS bag format.

<table>
<tr>
<td align="center">Falcam Rig</td><td align="center">Falcan 250 Quadrotor</td>
</tr>
<tr>
<td>
For the earlier datasets, a
<a href="https://github.com/osrf/ovc/tree/master/hardware/ovc0/HarleyTandem">
Falcam (ovc version 0)</a>
synchronized stereo camera/IMU is used, combined with
a <a href="https://pmdtec.com/picofamily/">
Monstar Time-Of-Flight (TOF) sensor</a>
and an unsynchronized  PointGrey/FLIR color camera. It
is cobbled together with zip ties and double sided tape into a rig.<br/>
<img src="media/falcam_rig.jpg" height="300"/>
</td>
<td>
An aerial robot is carried around that has all
the sensors connected to it. Again the synchronized stereo camera/IMU is a custom device made
by the <a href="https://www.openrobotics.org/">Open Source Robotics Foundation</a>, but
this time it is an <a href="https://github.com/osrf/ovc">Open Vision Computer OVC 1</a>.
No color camera is present, but either a
<a href="https://pmdtec.com/picofamily/">Monstar Time-Of-Flight (TOF) sensor</a>
or an <a href="https://orbbec3d.com/product-astra-pro/">Astra RGBD sensor</a><br/>
<img src="media/falcon_250.jpg" height="300"/>
</td>
</tr>
</table>

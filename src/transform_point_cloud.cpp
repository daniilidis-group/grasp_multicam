/* -*-c++-*--------------------------------------------------------------------
 * 2019 Bernd Pfrommer bernd.pfrommer@gmail.com
 */

#include <ros/ros.h>
#include <nodelet/nodelet.h>
#include <sensor_msgs/PointCloud2.h>
#include <tf/transform_listener.h>
#include <pcl_ros/point_cloud.h>
#include <pcl_ros/transforms.h>


namespace grasp_multicam {
  using PointCloud2ConstPtr = sensor_msgs::PointCloud2ConstPtr;
  class TransformPointCloud : public nodelet::Nodelet {
  public:
    void onInit() {
      nh_ = getPrivateNodeHandle();
      sub_ = nh_.subscribe("points", 10,
                           &TransformPointCloud::pointCloudCallback, this);
      pub_ = nh_.advertise<sensor_msgs::PointCloud2>("transformed_points", 10);
      nh_.param<std::string>("fixed_frame", fixedFrame_, "map");
      double delay;
      nh_.param<double>("transform_time_delay", delay, 0);
      transformTimeDelay_ = ros::Duration(delay);
    }

    void pointCloudCallback(const PointCloud2ConstPtr &cloud) {
      tf::StampedTransform T_f_c_stamped; // cloud to fixed
      try {
        transformListener_.lookupTransform(
          fixedFrame_, cloud->header.frame_id,
          cloud->header.stamp + transformTimeDelay_, T_f_c_stamped);
      }  catch (const tf::TransformException &e) {
        ROS_ERROR_STREAM("tf error: " << e.what());
        ros::Duration(0.1).sleep();
        return;
      }
      // allocated new, transformed cloud
      sensor_msgs::PointCloud2::Ptr tfCloud(new sensor_msgs::PointCloud2());

      Eigen::Matrix4f T_f_c;
      pcl_ros::transformAsMatrix(T_f_c_stamped, T_f_c);
      pcl_ros::transformPointCloud(T_f_c, *cloud, *tfCloud);

      tfCloud->header.frame_id = fixedFrame_;
      tfCloud->header.stamp    = cloud->header.stamp;
      pub_.publish(tfCloud);
    }
  private:
    ros::NodeHandle       nh_;
    tf::TransformListener transformListener_;
    ros::Subscriber       sub_;
    ros::Publisher        pub_;
    std::string           fixedFrame_;
    ros::Duration         transformTimeDelay_;
  }; // end of class

} // end of namespace

#include <pluginlib/class_list_macros.h>
PLUGINLIB_EXPORT_CLASS(grasp_multicam::TransformPointCloud, nodelet::Nodelet)

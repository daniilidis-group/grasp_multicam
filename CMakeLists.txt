cmake_minimum_required(VERSION 2.8)
project(grasp_multicam)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_EXTENSIONS OFF)
add_compile_options(-Wall -g)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  sensor_msgs
  tf
  nodelet
  pcl_ros
  pcl_conversions
)

catkin_package(
	CATKIN_DEPENDS roscpp sensor_msgs tf nodelet pcl_ros pcl_conversions
	)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

add_library(transform_point_cloud src/transform_point_cloud.cpp)
target_link_libraries(transform_point_cloud ${catkin_LIBRARIES})
add_dependencies(transform_point_cloud ${catkin_EXPORTED_TARGETS})

install(FILES nodelet_plugins.xml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

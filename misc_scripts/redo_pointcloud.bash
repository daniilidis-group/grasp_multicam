#!/bin/bash

# falcam

base_dir=../data/falcam

sub_dirs="2018-01-16/14-41-13 2018-01-16/15-39-11 2018-01-16/16-18-11 2018-01-16/16-44-05 2018-01-16/16-49-56 2018-01-16/16-55-22 2018-01-23/18-12-42 2018-01-23/18-49-29 2018-01-29/14-49-52 2018-01-29/15-16-31 2018-01-29/15-57-26 2018-01-29/16-05-01 2018-01-29/16-10-40 2018-01-29/16-15-55 2018-02-28/19-01-38 2018-02-28/20-04-10 2018-03-02/08-06-10 2018-03-02/08-15-06 2018-03-02/08-58-21"

# ovc
#base_dir=../data/ovc
#sub_dirs="2018-10-24/17-34-45 2018-10-24/17-25-45 2018-05-23/19-07-42 2018-05-23/18-58-52 2018-05-23/19-05-15 2018-04-26/16-39-21 2018-04-26/16-48-15 2018-04-26/16-41-39 2018-04-26/16-13-29 2018-11-08/13-33-05 2018-11-08/13-10-31 2018-11-09/11-34-55 2018-11-09/11-00-28 2018-10-25/18-11-30"

# ovc with astra
#sub_dirs="2018-04-26/16-39-21 2018-04-26/16-48-15 2018-04-26/16-41-39 2018-04-26/16-13-29"

for d in $sub_dirs; do
  fd=$base_dir/$d
  bag=${d/\//\-}
  echo 'adjusting calibration for ' $fd/${bag}.bag
  rosrun grasp_multicam add_camerainfo.py -c 10000000 --outbag $fd/${bag}_fc.bag --calib $fd/calib.yaml --id_map $fd/topic_to_frame_id.yaml $fd/${bag}.bag
  rosrun grasp_multicam adjust_pointcloud.py -c 10000000 --outbag $fd/${bag}_adj.bag --calib $fd/calib.yaml --id_map $fd/topic_to_frame_id.yaml $fd/${bag}_fc.bag
done

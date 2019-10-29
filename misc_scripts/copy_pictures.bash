#!/bin/bash

# falcam

base_dir=../data

sub_dirs="falcam/2018-01-16/14-41-13 falcam/2018-01-16/15-39-11 falcam/2018-01-16/16-18-11 falcam/2018-01-16/16-44-05 falcam/2018-01-16/16-49-56 falcam/2018-01-16/16-55-22 falcam/2018-01-23/18-12-42 falcam/2018-01-23/18-49-29 falcam/2018-01-29/14-49-52 falcam/2018-01-29/15-16-31 falcam/2018-01-29/15-57-26 falcam/2018-01-29/16-05-01 falcam/2018-01-29/16-10-40 falcam/2018-01-29/16-15-55 falcam/2018-02-28/19-01-38 falcam/2018-02-28/20-04-10 falcam/2018-03-02/08-06-10 falcam/2018-03-02/08-15-06 falcam/2018-03-02/08-58-21 ovc/2018-10-24/17-34-45 ovc/2018-10-24/17-25-45 ovc/2018-05-23/19-07-42 ovc/2018-05-23/18-58-52 ovc/2018-05-23/19-05-15 ovc/2018-04-26/16-39-21 ovc/2018-04-26/16-48-15 ovc/2018-04-26/16-41-39 ovc/2018-04-26/16-13-29 ovc/2018-11-08/13-33-05 ovc/2018-11-08/13-10-31 ovc/2018-11-09/11-34-55 ovc/2018-11-09/11-00-28 ovc/2018-10-25/18-11-30"

# ovc with astra
#sub_dirs="2018-04-26/16-39-21 2018-04-26/16-48-15 2018-04-26/16-41-39 2018-04-26/16-13-29"

for d in $sub_dirs; do
    fd=$base_dir/$d
  dev_dir=`echo $d | cut -d'/' -f 1`
  day_dir=`echo $d | cut -d'/' -f 2`
  seq=${d/falcam\//}
  seq=${seq/ovc\//}
  seq=${seq/\//\-}
  pushd $fd
  cp ${seq}_video.jpg ${seq}_*.png ~/Documents/grasp_multicam/src/grasp_multicam/content/sequences/$dev_dir/$day_dir/

  popd
done

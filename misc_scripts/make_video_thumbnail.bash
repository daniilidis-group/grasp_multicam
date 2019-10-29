seq=$1

ffmpeg -i ${seq}.mp4 -ss 00:00:01.000 -vframes 1 thumb.jpg

composite -geometry +550+200 `rospack find grasp_multicam`/content/sequences/play_video.png thumb.jpg ${seq}_video.jpg

rm thumb.jpg
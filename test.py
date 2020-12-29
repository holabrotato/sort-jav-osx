from mutagen.mp4 import MP4
f  = '/Volumes/WD/JAV/CAWD/CAWD-136.mp4'
mp4_video_tags = MP4(f)
mp4_video_tags["\xa9nam"] = "testing 2"
mp4_video_tags.save()

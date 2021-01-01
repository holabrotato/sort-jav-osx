# app.py

import os


dirName = '/Volumes/WD/JAV'
listOfFiles = list()
for (dirpath, dirnames, filenames) in os.walk(dirName):
    listOfFiles += [os.path.join(dirpath, file) for file in filenames]
for elem in listOfFiles:
    f_name, f_ext = os.path.splitext(elem)
    if (f_ext != "jpg" and f_ext != "srt" and f_ext !="txt"):
        print(f_name)
import os
import json
import requests
import time
import base64
from bs4 import BeautifulSoup


def strip_multi(s):
    s = s.replace("_A","").replace("_B","").replace("_C","").replace("_D","").replace("_E","")
    return s

# my user id : 840bdeb4a79f444d9686e9d9e92957e5
#http://localhost:8096/emby/Users/Public

path_list = [
    # '/Volumes/WD/JAV/',

    # JAV SUB FOLDER
    # '/Volumes/WD/JAV/Chijo_Heaven',
    # '/Volumes/WD/JAV/Das',
    # '/Volumes/WD/JAV/E-BODY',
    # '/Volumes/WD/JAV/Faleno',
    # '/Volumes/WD/JAV/Fitch',
    # '/Volumes/WD/JAV/kawaii',
    # '/Volumes/WD/JAV/Hajime_Kikaku',
    # '/Volumes/WD/JAV/Hon_Naka',
    # '/Volumes/WD/JAV/Idea_Pocket',
    # '/Volumes/WD/JAV/Leo',
    # '/Volumes/WD/JAV/MADONNA',
    # '/Volumes/WD/JAV/MOODYZ',
    # '/Volumes/WD/JAV/MUTEKI',
    # '/Volumes/WD/JAV/Maxing',
    # '/Volumes/WD/JAV/Momotaro_Eizo',
    # '/Volumes/WD/JAV/Ms_Video_Group',
    # '/Volumes/WD/JAV/Nagae_Style',
    # '/Volumes/WD/JAV/OPPAI',
    # '/Volumes/WD/JAV/PREMIUM',
    # '/Volumes/WD/JAV/Prestige',
    # '/Volumes/WD/JAV/Pussy_Bank',
    # '/Volumes/WD/JAV/ROCKET',
    '/Volumes/WD/JAV/S1_NO1_STYLE',
    '/Volumes/WD/JAV/SEX_Agent_Daydreamers',
    '/Volumes/WD/JAV/SODCreate',
    # '/Volumes/WD/JAV/STAR_PARADISE',
    # '/Volumes/WD/JAV/Tameike_Goro',
    # '/Volumes/WD/JAV/VnR_PRODUCE',
    # '/Volumes/WD/JAV/WANZ',
    # '/Volumes/WD/JAV/WANZ-Endure',
    # '/Volumes/WD/JAV/Misc'
]

crawlpath = '/Volumes/WD/JAV/MADONNA'
for crawlpath in path_list:
    os.chdir(crawlpath)

    ls_f = None
    for file in os.listdir(crawlpath):
        filename,file_extension = os.path.splitext(file)
        if(file_extension != ".mp4"):
            continue


        emby = "http://localhost:8096/emby/Items?Recursive=true&NameStartsWith="+strip_multi(filename)+"&api_key=f3da2238d43740a294abb02ea858e536" 
        headers = {
            'content-type' : 'application/json'
        }
        try:
            response = requests.get(emby, headers=headers)
            video_json = json.loads(response.content)
            video_name = filename
            video_id = video_json["Items"][0]["Id"]
        except:
            continue

        print(json.dumps(video_json, indent=4, sort_keys = True))

        for a_file in os.listdir(crawlpath):
            a,b = os.path.splitext(a_file)
            if video_name in a_file and b == ".jpg":
                # print(a_file)
                f = open(a_file,'rb')
                ls_f = base64.b64encode(f.read())
                f.close()
                url = "http://localhost:8096/emby/Items/" + video_id + "/Images/Primary/?&api_key=f3da2238d43740a294abb02ea858e536"
                header = {"Content-Type" : "image/jpeg"}
                response = requests.post(url=url, data=ls_f, headers=header)
                print(response.text)

#if video_name in filename and file_extension==".jpg":
 #       print(filename)
        # f = open(file,'rb')
        # ls_f = base64.b64encode(f.read())
        # f.close()
        # url = "http://localhost:8096/emby/Items/" + video_id + "/Images/Primary/?&api_key=f3da2238d43740a294abb02ea858e536"
        # header = {"Content-Type" : "image/jpeg"}
        # response = requests.post(url=url, data=ls_f, headers=header)
        # print(response.text)



    # if(file_extension == ".nfo"):
    #     video_id = file.split(".")[0]
    #     video_nfo = os.getcwd() + "/" + file
        
        

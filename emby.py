import os
import json
import requests
import urllib.request
import time
import re
import base64
from bs4 import BeautifulSoup

# looks on local disk for covers and uploads to emby
upload_covers = True

# makes a request to emby for all actors, then queries r18 and fetches to disk
fetch_actress_images = False

# looks at disk cache of actress images, and uplaods to emby
upload_actress_images = False


emby_api_key = 'f3da2238d43740a294abb02ea858e536'
r18_actress_base = 'https://pics.r18.com/mono/actjpgs/'
cache_path = "/Volumes/WD/Cache/actress/"

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
    '/Volumes/WD/JAV/MADONNA',
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
    # '/Volumes/WD/JAV/S1_NO1_STYLE',
    # '/Volumes/WD/JAV/SEX_Agent_Daydreamers',
    # '/Volumes/WD/JAV/SODCreate',
    # '/Volumes/WD/JAV/STAR_PARADISE',
    # '/Volumes/WD/JAV/Tameike_Goro',
    # '/Volumes/WD/JAV/VnR_PRODUCE',
    # '/Volumes/WD/JAV/WANZ',
    # '/Volumes/WD/JAV/WANZ-Endure',
    '/Volumes/WD/JAV/Misc'
]

def save_image_from_url_to_path(path, url):
    """save an image denoted by the url to the path denoted by path
    with the given name"""

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')]
    urllib.request.install_opener(opener)
    print("url: " + url + " >>> " + path + ".jpg")
    urllib.request.urlretrieve(url, path + ".jpg")

    try:
        drive = path.split(os.sep)[0]
        temp_location = drive + os.sep + path + '.jpg'
        os.rename(path + ".jpg", temp_location)
        os.rename(temp_location, path + ".jpg")
        return temp_location + ".jpg"
    except:
        pass

#
#  Upload Covers
#    from local disk to Emby
#
if (upload_covers):
    crawlpath = '/Volumes/WD/JAV/MADONNA'
    for crawlpath in path_list:
        os.chdir(crawlpath)

        ls_f = None
        for file in os.listdir(crawlpath):
            filename,file_extension = os.path.splitext(file)
            if(file_extension != ".mp4"):
                continue


            emby_movie_info = "http://localhost:8096/emby/Items?Recursive=true&NameStartsWith="+strip_multi(filename)+"&api_key=" + emby_api_key
            headers = {
                'content-type' : 'application/json'
            }
            try:
                response = requests.get(emby_movie_info, headers=headers)
                video_json = json.loads(response.content)
                video_name = filename
                video_id = video_json["Items"][0]["Id"]
            except:
                continue

            print(json.dumps(video_json, indent=4, sort_keys = True))

            for a_file in os.listdir(crawlpath):
                a,b = os.path.splitext(a_file)
                if video_name in a_file and b == ".jpg":
                    f = open(a_file,'rb')
                    ls_f = base64.b64encode(f.read())
                    f.close()
                    url = "http://localhost:8096/emby/Items/" + video_id + "/Images/Primary/?&api_key=" + emby_api_key
                    header = {"Content-Type" : "image/jpeg"}
                    response = requests.post(url=url, data=ls_f, headers=header)
                    print(response.text)

            print("done uploading jpgs")


if(fetch_actress_images):
    # first let's get a list of every actress in our database
    emby_all_actress = 'http://localhost:8096/emby/Persons?Filters=IsNotFolder&EnableImages=true&NameStartsWithOrGreater=1&api_key=' + emby_api_key

    response = requests.get(emby_all_actress)
    actress_map = json.loads(response.content)
    actress_list = actress_map["Items"]

    actress_lookup = {
        "aika" : "aika3",
        'shinoda_yu' : 'sinoda_yuu',
        'erika' : 'erika2',
        'hashimoto_arina' : 'hasimoto_arina',
        'kimijima_mio':'kimizima_mio'
    }


    count = 0
    for a in actress_list:

        name = a["Name"]
        id = a["Id"]
        # remove parenthesis
        start = name.find( '(' )
        end = name.find( ')' )
        if start != -1 and end != -1:
            name = name[start+1:end]

        name_array = name.split()
        count_name = len(name_array)

        # massage actress names
        if( count_name == 2):
            actress = name_array[1] + "_" + name_array[0]
        elif (count_name == 1):
            actress = name_array[0]
        else:
            continue
        
        actress = actress.lower()

        # replace outdated names
        if actress in actress_lookup:
            actress = actress_lookup[actress]
            
    
        if(fetch_actress_images):
            try:
                save_image_from_url_to_path(cache_path + actress ,r18_actress_base + actress + ".jpg")
            except:
                continue

        if(upload_actress_images):
            actress_filename = cache_path+"/found/" + actress+".jpg"
            if(os.path.isfile(actress_filename)):
                print(id + ":" + actress)
                f = open(actress_filename,'rb')
                ls_f = base64.b64encode(f.read())
                f.close()
                url = "http://localhost:8096/emby/Items/" + id + "/Images/Primary/?&api_key=" + emby_api_key
                header = {"Content-Type" : "image/jpeg"}
                response = requests.post(url=url, data=ls_f, headers=header)
                print(response.text)
                count = count + 1

        
    # print(count + " set ")

        

 
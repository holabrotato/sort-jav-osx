import os
import urllib.request
import re
import touch
import html
import shutil
import base64
import string
from mutagen.mp4 import MP4
from datetime import datetime
import sys  # just so we can test exiting
from osxmetadata import OSXMetaData, Tag, FINDER_COLOR_GREEN
from bs4 import BeautifulSoup
import requests
import time
from xml.dom import minidom 
import shutil
import pathlib

startTime = time.time()

class JAVMovie:
    actresses = []
    genres = []
    studio = ""
    label = ""
    release_date = ""
    cover_url = ""
    series = ""
    runtime = 0
    
    def __init__(self, code):
        self.code = code

    def actress_tags(self):
        actress_string = ""
        for actress in self.actresses:
            actress_string += actress + "#"
        return actress_string

    def genre_tags(self):
        genre_string = ""
        for genre in self.genres:
            genre_string += genre + "#"
        return genre_string


# Global object, I know it's ugly
_movie = JAVMovie(code="")

#
#  This array is used when sorting the staging section into the respective studios
#
sort_map = {
    "Prestige" : ["ABP", "ABW", "MBM"],
    "Premium" : ["PRTD", "PRED"],
    "kawaii" : ["CAWD"],
    'Das' : ["DASD"],
    "Faleno" : ["FSDSS", "FCDSS"],
    "Fitch" : ["JUFE", "JUFD"],
    "E-BODY" : ["EBOD"],
    "Tameike_Goro" : ["MEYD"],
    "Hon_Naka" : ["HND", "HNDS"],
    "MADONNA" : ["JUL", "JUY"],
    "MOODYZ" : ["MIAA", "MIDE"],
    "Momotaro_Eizo" : ["YMDD"],
    "Idea_Pocket" : ["IPX", "IPZ", "IPIT"],
    'S1_NO1_STYLE' : ["SSNI","OFJE", "SNIS"],
    "Misc" : ["DANDY", "VEC", "MXGS","MVSD", "NACR","SUKE", "NSPS", "MMND", "FONE", "MDTD"]
}

# this is where temporary downloads go, sort jav will parse this
staging_path = "/Volumes/WD/Staging/"
jav_root = "/Volumes/WD/JAV/"


# path array:  list of directories for sort_jav to clean, fetch metatags.
path_list = [
    # '/Volumes/WD/JAV/',

    # '/Volumes/WD/JAV/Chijo_Heaven', 
    # '/Volumes/WD/JAV/Das',
    # '/Volumes/WD/JAV/E-BODY',
    # '/Volumes/WD/JAV/Faleno',
    # '/Volumes/WD/JAV/Fitch',
    # '/Volumes/WD/JAV/Hajime_Kikaku',
    # '/Volumes/WD/JAV/Hon_Naka',
    # '/Volumes/WD/JAV/Idea_Pocket',
    # '/Volumes/WD/JAV/Leo',
    # '/Volumes/WD/JAV/MADONNA',
    # '/Volumes/WD/JAV/MOODYZ',
    # '/Volumes/WD/JAV/MUTEKI',
    # '/Volumes/WD/JAV/Maxing',
    # '/Volumes/WD/JAV/Momotaro_Eizo',
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
    # '/Volumes/WD/JAV/Misc',

    # '/Volumes/WD/VR/AJVR',
    # '/Volumes/WD/VR/EBVR',
    # '/Volumes/WD/VR/KAVR',
    # '/Volumes/WD/VR/KBVR',
    # '/Volumes/WD/VR/CBIKMV',
    # '/Volumes/WD/VR/PRVR',
    # '/Volumes/WD/VR/SAVR',
    # '/Volumes/WD/VR/HNVR',
    # '/Volumes/WD/VR/IPVR',
    # '/Volumes/WD/VR/MDVR',
    # '/Volumes/WD/VR/KIWVR',
    # '/Volumes/WD/VR/SIVR',
    # '/Volumes/WD/VR/VRKM',
    # '/Volumes/WD/VR/WAVR'
]

def read_file(path):
    """Return a dictionary containing a map of name of setting -> value"""

    d = {}
    # so we can strip invalid characters for filenames
    translator = str.maketrans({key: None for key in '<>/\\|*:?'})
    with open(path, 'r') as content_file:
        for line in content_file.readlines():
            line = line.strip('\n')
            if not line.startswith('path'):
                line = line.translate(translator)
            if line and not line.startswith('#'):
                split = line.split('=')
                d[split[0]] = split[1]
                if split[1].lower() == 'true':
                    d[split[0]] = True
                elif split[1].lower() == 'false':
                    d[split[0]] = False
    return d


def strip_id_from_video(path, s):
    """get the id of the video from a video's path"""

    partial_split = path.split(os.sep)[-1].rsplit(".")[0]
    delimiter = s['delimiter-between-multiple-videos']
    if delimiter in partial_split:
        partial_split = partial_split.split(delimiter)[0]

    partial_split = strip_definition_from_video(partial_split)
    return partial_split


def strip_definition_from_video(vid_id):
    """Strip any sort of HD tag from the video"""

    hd = ['[HD]', '[FHD]', '[SD]', '(SD)', '(HD)', '(FHD)']
    for item in hd:
        vid_id = vid_id.replace(item, '')
    return vid_id


def check_vid_id_has_dash(vid_id):
    """Check if the video id has a dash and return one with it if it doesn't"""
    if '-' not in vid_id:
        for i in range(len(vid_id)):
            if vid_id[i] in '0123456789':
                vid_id = vid_id[:i] + '-' + vid_id[i:]
                break
    return vid_id


def getNumExtension(vid_id):
    """Given a video return the number extension"""
    # assume the video id is already fixed to cheat checking and return the fixed set
    return str(vid_id.split('-')[1])


def strip_video_number_from_video(path, vid_id, s):
    """Return the portion that specifies the video number, or none if none exists"""
    delimiter = s['delimiter-between-multiple-videos']
    qualified = path.split(os.sep)[-1]
    split = qualified.split(delimiter)
    if len(split) == 1:
        # check for videos of the form XXX-123A.HD.mp4, XXX-123B.HD.mp4
        # they won't match the delimiter but still need to be caught
        nums = getNumExtension(vid_id)
        chars = 'ABCDEFGHIJ'
        index = qualified.find(nums)
        if index > -1:  # found a match
            c = qualified[index + len(nums)].upper()
            if c in chars:
                return str(chars.find(c) + 1)
        return None
    else:
        ret = split[1].rsplit('.')[0]
        if len(ret) > 2:  # this way we catch straggling names
            return None
        else:
            return ret

def get_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response.content



def get_r18_url(vid_id):
    vid_id = check_vid_id_has_dash(vid_id.upper())
    search_url = "https://www.r18.com/common/search/searchword=" + vid_id + "/"
    search_html = get_page(search_url)

    # now we have the search_url, let's grab the actual video html for meta-data
    soup_search = BeautifulSoup(search_html, 'html.parser')
    
    try:
        search_url = soup_search.find(class_="cmn-list-product01").find("li").find("a")["href"]
        print("         (https) fetching r18 page...")
        product_html = get_page(search_url)
    except:
        return None

    return product_html


def download_subtitles(_movie, path):
    path = "/".join(path.split('/')[0:-1])
    
    print("      (Subtitles) Searching subtitlecat..")

    # Do we already have this subtitle on disk?
    # First check our local disk to see if we already have this sub in our disk cache
    # Or check our Sub directory for manually downloaded subs
    if(os.path.isfile(path + "/" + _movie.code + ".default.en.srt")):
        print("      (Skipping) We already have this subtitle")
        return True
    elif os.path.isfile("/Volumes/WD/Sub/" + _movie.code + ".srt"):
        my_file = pathlib.Path("/Volumes/WD/Sub/" + _movie.code + "-en.srt")
        to_file = pathlib.Path(path + "/" + _movie.code + ".en.default.srt")
        shutil.copyfile(my_file, to_file)
        return True

    # Check subtitle cat
    code = _movie.code
    subtitlecat_html = get_page("https://www.subtitlecat.com/index.php?search=" + code)
    soup = BeautifulSoup(subtitlecat_html, "html.parser")
    subtitle_table = soup.find("table").find("tbody").find_all("tr")
    for row in subtitle_table:
        subtitle_url = row.find("a")["href"]
        if(code.upper() in subtitle_url.upper()):
            
            srt_download_link = subtitle_url.split(".")[0] + "-en.srt"
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')]
            urllib.request.install_opener(opener)
            srt_download_link = "https://www.subtitlecat.com/" + srt_download_link
            base = strip_partial_path_from_file(path)
            fname = strip_definition_from_video(code)
            fullpath = os.path.join(base, fname)
            
            try:
                print("         Downloading subtitle: " + srt_download_link)
                urllib.request.urlretrieve(srt_download_link, path + "/" + _movie.code + "-en.srt")
                return True
            except Exception as E:
                print("---- (ERROR) An error occurred downloading subtitles! ")
                print(E)

            break

    return False




def parse_r18_page(html, vid_id):
    jav_video = JAVMovie(code=vid_id)
    soup = BeautifulSoup(html, "html.parser")

    # video title
    jav_video.title = soup.find('cite',itemprop='name').get_text().strip()

    # release date
    datetime_str = soup.find(itemprop='dateCreated').get_text().strip().replace("Sept", "Sep").replace("June", "Jun.").replace("July","Jul.").replace("May", "May.")
    datetime_object = datetime.strptime(datetime_str, '%b. %d, %Y')

    jav_video.release_date = datetime_object.strftime('%Y-%m-%d')
    # series 
    jav_video.series = soup.find(class_="product-details").find_all("dl")[1].find_all("dd")[3].get_text().strip()

    # studio
    jav_video.studio = soup.find(itemprop='productionCompany').get_text().strip()
    
    # genre
    genres_list = []
    genres_tags = soup.find_all(itemprop='genre')
    for tag in genres_tags:
        genre = tag.text.strip()
        genres_list.append(genre)
    jav_video.genres = genres_list

    # actress
    actress_list = []
    actress_tags = soup.find(itemprop='actors').find_all(itemprop='name')
    for actress_tag in actress_tags:
        actress_list.append(fix_actress_name(actress_tag.text.strip()))
    jav_video.actresses = actress_list

    # get cover image url
    jav_video.cover_url = soup.find(class_='detail-single-picture').find("img")["src"]


    #runtime 
    jav_video.duration = soup.find(itemprop='duration').text.strip().replace("min.", "")
    return jav_video



def rename_file(path, _movie, s, vid_id):

    """Rename the file per our settings
    Returns the name of the file regardless of whether it has been renamed"""
    actress_string = get_actress_string(_movie, s)

    if s['include-actress-in-video-name']:
        base = strip_partial_path_from_file(path)
        if s['video-number']:
            if s['actress-before-video-number']:
                new_fname = vid_id + s['delimiter-between-video-name-actress'] \
                            + actress_string + s['delimiter-between-multiple-videos'] \
                            + s['video-number'] + '.' + path.rsplit('.')[-1]
                new_path = os.path.join(base, new_fname)
            else:  # actress after
                new_fname = vid_id + s['delimiter-between-multiple-videos'] \
                            + s['video-number'] + s['delimiter-between-video-name-actress'] \
                            + actress_string + '.' + path.rsplit('.')[-1]
                new_path = os.path.join(base, new_fname)
        else:
            new_fname = vid_id + s['delimiter-between-video-name-actress'] \
                        + actress_string + '.' + path.rsplit('.')[-1]
            new_path = os.path.join(base, new_fname)
        try:
            os.rename(path, new_path)
            return new_path
        # this happens on dupe or some other failure
        # suce as invalid filname (shouldn't happen), drive full, or filename too long
        except:
            return path
    elif strip_file_name(path) != vid_id:
        base = strip_partial_path_from_file(path)
        if s['video-number']:
            new_fname = vid_id + s['delimiter-between-multiple-videos'] \
                        + s['video-number'] + '.' + path.rsplit('.')[-1]
            new_path = os.path.join(base, new_fname)
        else:
            new_fname = vid_id + '.' + path.rsplit('.')[-1]
            new_path = os.path.join(base, new_fname)
        try:
            os.rename(path, new_path)
            return new_path
        except:
            return path

    else:
        # easier to always return the file name so we can treat both cases the same
        # because when we move it (potentially) we don't care if it has been renamed
        return path


def get_actress_string(_movie, s):
    """Return the string of the actress names as per the naming convention specified
    Takes in the html contents to filter out the actress names"""
    a_list = get_actress_from_html(_movie, s)

    actress_string = ''
    # if javlibrary returns no actresses then we'll just say whatever we specified
    if len(a_list) == 0:
        return s['name-for-actress-if-blank']
    for actress in a_list:
        actress_string += actress + s['delimiter-between-multiple-actresses']
    # strip the last delimiter, we don't want it
    actress_string = actress_string[0:-1]
    return actress_string


def fix_actress_name(name):
    """Returns the updated name for any actress based on our replacement scheme"""

    """ if you want to ad any additional ways to fix names, simply add another elif line below
    elif name == 'name returned from javlibrary'
        return 'different name'
    """

    if name == 'Kitagawa Eria':
        return 'Kitagawa Erika'
    elif name == 'Oshikawa Yuuri':
        return 'Oshikawa Yuri'
    elif name == 'Shion Utsonomiya':
        return 'Anzai Rara'
    elif name == 'Rion':
        return "Rara Anzai"
    return name

def get_actress_from_html(_movie, s):
    """Return a list of actresses from the html
    actresses are strings that are formatted the way we can put them straight in the name"""

    fixed_names = []
    for fname in _movie.actresses:
        # format this correctly
        if fname.count(' ') == 1:
            last = fname.split(' ')[0]
            first = fname.split(' ')[1]
            if s['name-order'].lower() == 'first':
                new_name = first + s['delimiter-between-actress-names'] + last
                fixed_names.append(new_name)
            elif s['name-order'].lower() == 'last':
                new_name = last + s['delimiter-between-actress-names'] + first
                fixed_names.append(new_name)
        else:
            fixed_names.append(fname)

    return fixed_names


def create_and_move_video_into_folder(path, s, vid_id, _movie):
    """Create a folder and then move the given video into it
    Path is the fullpath of the video
    Returns the new path of the video
    Returns the old path if there's an unknown error"""

    folder_name = strip_definition_from_video(vid_id)
    if s['include-actress-name-in-folder']:
        folder_name += s['delimiter-between-video-name-actress'] + get_actress_string(_movie, s)

    fullpath = os.path.join(strip_partial_path_from_file(path), folder_name)
    if os.path.isdir(fullpath):  # folder already exists so just try moving us there
        try:
            vid_path_portion = path.split(os.sep)[-1]
            new_path = os.path.join(fullpath, vid_path_portion)
            os.rename(path, new_path)
            return new_path
        except FileExistsError as e:
            print('File already exists, could not sort. This might be a multiple file issue')
            return path
    try:
        os.makedirs(fullpath)
    except:
        # this can occur if the folder already exists, name is too long, drive is full
        # since we still want to move files if the folder exists then we'll keep going if that's the case
        if os.path.isdir(fullpath):
            pass
        elif len(fullpath) > 255:
            try:
                print("Path was too long so did not move " + vid_id)
            except:
                print("Path was too long so did not move one file with unknown characters")
        return path
    vid_path_portion = path.split(os.sep)[-1]
    new_path = os.path.join(fullpath, vid_path_portion)
    if os.path.exists(new_path):
        print('Path exists')
    try:
        os.rename(path, new_path)
        return new_path
    except:  # this only happens if it exists or there's a catastrophic failure
        if len(new_path) > 255:
            try:
                print("Path was too long so did not move " + vid_id)
            except:
                print("Path was too long so did not move one file with unknown characters")
        return path
    return path


def strip_partial_path_from_file(path):
    """given a file, strip the path from the file name
    This is the essentially the path to the file's directory
    Returns the stripped path or none if it does not exist"""

    partial_path = _strip_partial_path_helper(path, os.sep)
    if (os.path.exists(partial_path)):
        return partial_path
    return None


def _strip_partial_path_helper(path, delimiter):
    stripped_path = path.split(delimiter)
    partial_path = stripped_path[0] + os.sep + stripped_path[1]
    for part in stripped_path[2:-1]:
        partial_path = os.path.join(partial_path, part)
    return partial_path


def download_cover(path, _movie, s ):
    vid_id = _movie.code
    """Get the cover for the video denoted by path from the specified html"""
    # path needs to be stripped but otherwise we can use it to store the video
    # html should have the cover there we can take
    img_link = _movie.cover_url
    # TODO:
    # create the path name based on the settings file
    base = strip_partial_path_from_file(path)
    fname = strip_definition_from_video(vid_id)
    if (s['include-actress-name-in-cover']):
        fname += s['delimiter-between-video-name-actress']
        actress_string = get_actress_string(_movie, s)
        fname += actress_string

    fullpath = os.path.join(base, fname)
    if os.path.isfile(fullpath+".jpg"):
        return fullpath + ".jpg"
    else:
        print ("        (Fetching) downloading cover image")
        return save_image_from_url_to_path(fullpath, img_link)



def save_image_from_url_to_path(path, url):
    """save an image denoted by the url to the path denoted by path
    with the given name"""

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, path + ".jpg")

    try:
        drive = path.split(os.sep)[0]
        temp_location = drive + os.sep + path + '.jpg'
        os.rename(path + ".jpg", temp_location)
        os.rename(temp_location, path + ".jpg")
        return temp_location + ".jpg"
    except:
        pass


def get_image_url_from_html(html,s):
    global _movie
    """get the url of the image from the supplied html for the page"""
    return _movie.cover_url
    

def rename_start_quotation(path):
    """Rename files that start with quotations right away just because it'll work easier this way"""
    fname = path.split(os.sep)[-1]
    fname.replace("'", '')  # replace ' with nothing
    new_path = os.sep.join(path.split(os.sep)[:-2])
    try:
        os.rename(path, new_path)
    except:
        pass


def find_id(s):
    """Given a string s, try to find an id within it and return it"""
    regex = "[a-zA-Z]{2,8}[-]?[0-9]{2,5}"
    match = re.search(regex, s)
    if match:
        return correct_vid_id(match.group())
    else:
        return None

def correct_vid_id(vid_id):
    """Check if the video id has a dash and return it with one if it doesn't have it
    also fixes anything that has a digit first"""

    if vid_id[0] in '0123456789':
        findex = None
        for i in range(len(vid_id)):
            if vid_id[i] not in '0123456789':
                findex = i
                break
        for i in range(findex, len(vid_id)):
            if vid_id[i] in '0123456789' and findex:
                if '-' not in vid_id:
                    return vid_id[findex:i] + '-' + vid_id[:findex] + vid_id[i:]
                else:
                    return vid_id[findex:i] + vid_id[:findex] + vid_id[i:]

    if '-' not in vid_id:
        if 'R18' in vid_id or 'T28' in vid_id:
            return vid_id[0:3] + '-' + vid_id[3:]
        else:
            for i in range(len(vid_id)):
                if vid_id[i] in '0123456789':
                    return vid_id[:i] + '-' + vid_id[i:]
    return vid_id


def strip_file_name(path):
    """Given a filepath, strip the name of the file from it"""
    return path.split(os.sep)[-1].rpartition('.')[0]


def strip_full_file_name(path):
    """Given a filepath, return the full name with the filetype"""
    return path.split(os.sep)[-1]


def strip_bad_data(path):
    """Remove any data from the path that might conflict"""
    bad = ['hjd2048.com', 'h264', 'play999', 'h265', 'hhd800.com','fbfb.me@','dhd1080.com@']

    for str_to_remove in bad:
        if path.find(str_to_remove) != -1:
            path = path.replace(str_to_remove, '')

    return path

# Adds an OSX tag to a file    
def add_tag(tag, file):
    tag_results = os.system("tag --add \"" + tag + "\" " + file)

def sort_jav(a_path, s):
    global _movie
    """Sort all our unsorted jav as per the specified settings"""

    # store all the files to rename in a list so we don't mess with looping over the files
    temp = []
    count = 0

    print(" ")
    print("  Analyzing Directory : " + a_path)
    for f in os.listdir(a_path):
        fullpath = os.path.join(a_path, f)
        file_name, file_extension = os.path.splitext(fullpath)
  
        # only consider video files
        if not os.path.isdir(fullpath): # ignore DS Store and folders
            if f == '.DS_Store' or file_extension == ".jpg" or file_extension == ".srt" or file_extension == ".nfo":
                continue

            else:
                meta = OSXMetaData(fullpath)
                already_processed = False

                # We can check if a video has already been processed by the finder comment meta data
                # This only works on OSX
                if meta.findercomment:
                    already_processed = "jdc" in meta.findercomment
                    if already_processed and s['skip-processed']:
                        continue
                temp.append(fullpath)

    for path in temp:
        count += 1
        try:
            vid_id = correct_vid_id(find_id(strip_bad_data(strip_file_name(path))))
        except:
            # to prevent crashing on r18/t28 files
            vid_id = strip_file_name(path)
        print("    {0}: {1} of {2}".format(vid_id.upper(), count, len(temp)))
        try:
            s['video-number'] = strip_video_number_from_video(path, vid_id, s)
            if s['make-video-id-all-uppercase']:
                vid_id = vid_id.upper()
        except Exception as e:
            print("    ...Skipping {} , could not find JAV ID ".format(vid_id))
            continue
        
        try:
            # 
            #  Check if we've seen this video before in our cache of html files 
            #
            cache_path = './cache/' + vid_id + ".html"
            javfile = open(cache_path, "r")
            r18_html = javfile.read()
            r18_html = r18_html.replace("\n","")
            if os.stat(cache_path).st_size == 0:
                raise Exception("found empty html file")
            javfile.close()
            print("      (Loading Cache) Loading " + cache_path)
        except Exception as e:
            #
            #  Download the R18 page, cache it locally
            #
            r18_html = get_r18_url(vid_id)    
            if (r18_html == None):
                print("    ...Skipping: Could not find video on R18.")
                continue

            print("      (Writing Cache) Caching ./" + vid_id +".html")
            cache_html = open("./cache/" + vid_id+".html", 'wb')
            cache_html.write((r18_html))       

        
        if(r18_html == None):
                print("    ...Skipping: Could not find video on R18 Library" + vid_id)
                continue
        
        # now let's parse the website and fetch all the meta-data
        _movie = parse_r18_page(r18_html,vid_id)

        # rename the file according to our convention
        new_fname = rename_file(path, _movie, s, vid_id)
        meta = OSXMetaData(new_fname)

        if s['add-osx-tags']:
            
            print("         (Metadata) Code:   " + _movie.code)
            print("         (Metadata) Title:  " + _movie.title[0:60])
            print("         (Metadata) Studio: " + _movie.studio[0:50])
            print("         (Metadata) Series: " + _movie.series[0:50])
            print("         (Metadata) Actress:" + ", ".join(_movie.actresses))

            actress_string = ""
            for actress in _movie.actresses:
                add_tag(actress, new_fname)
                actress_string += actress + "#"
            
            genre_string = ""
            for genre in _movie.genres:
                add_tag(genre,new_fname)
                genre_string += genre + "#"

            add_tag(_movie.label, new_fname)
            add_tag(_movie.studio, new_fname)

            # set description
            meta.description = "Released  " + _movie.release_date
            if _movie.series == "----":
                movie_series_string = ""
            else:
                movie_series_string = "("+_movie.series+")"
            meta.findercomment =  _movie.release_date + " " + movie_series_string + _movie.title + " jdc"

        if s['add-vlc-tags']:
            # Set MP4 metadata for VLC
            try:
                mp4_video_tags = MP4(new_fname)
                mp4_video_tags['\xa9nam'] = _movie.code + " - " + _movie.actress_tags()
                mp4_video_tags['\xa9gen'] = _movie.genre_tags()
                mp4_video_tags['\xa9ART'] = _movie.studio
                mp4_video_tags["desc"] = _movie.title
                mp4_video_tags['\xa9alb'] = _movie.series
                mp4_video_tags['purd'] = "Today"
                mp4_video_tags.save()
            except:
                print("      (ERROR)  Could not add VLC metadata: " + _movie.code )
        if s['include-cover']:
            _movie.local_cover_path = download_cover(path, _movie, s)

        if s['add-emby-nfo']:
            #Define document
            xmlFile = minidom.Document() 

            #Create base element
            baseElement = xmlFile.createElement("movie")
            xmlFile.appendChild(baseElement)

            # title
            titleElement = xmlFile.createElement("title")
            titleElement.appendChild(xmlFile.createTextNode(_movie.code))
            baseElement.appendChild(titleElement)

            # sort title
            studioElement = xmlFile.createElement("sorttitle")
            studioElement.appendChild(xmlFile.createTextNode(_movie.code))
            baseElement.appendChild(studioElement)

            # studio
            studioElement = xmlFile.createElement("studio")
            studioElement.appendChild(xmlFile.createTextNode(_movie.studio))
            baseElement.appendChild(studioElement)

            # plot
            studioElement = xmlFile.createElement("plot")
            studioElement.appendChild(xmlFile.createTextNode( _movie.title ))
            baseElement.appendChild(studioElement)

            # runtime
            runtimeElement = xmlFile.createElement("runtime")
            runtimeElement.appendChild(xmlFile.createTextNode(str(_movie.runtime)))
            baseElement.appendChild(runtimeElement)

            # premiered
            taglineElement = xmlFile.createElement("tagline")
            taglineElement.appendChild(xmlFile.createTextNode(_movie.series))
            baseElement.appendChild(taglineElement)
                        
            # premiered
            dateElement = xmlFile.createElement("premiered")
            dateElement.appendChild(xmlFile.createTextNode(_movie.release_date))
            baseElement.appendChild(dateElement)
                        

            for actress in _movie.actresses:
                actorElement = xmlFile.createElement("actor")
                nameElement = xmlFile.createElement("name")
                textElement = xmlFile.createTextNode(actress)
                nameElement.appendChild(textElement)
                actorElement.appendChild(nameElement)
                baseElement.appendChild(actorElement)

            for genre in _movie.genres:
                genreElement = xmlFile.createElement("genre")
                textElement = xmlFile.createTextNode(genre)
                genreElement.appendChild(textElement)
                baseElement.appendChild(genreElement)
                genreElement = xmlFile.createElement("tag")
                textElement = xmlFile.createTextNode(genre)
                genreElement.appendChild(textElement)
                baseElement.appendChild(genreElement)
                
            nfo_str = minidom.parseString(xmlFile.toxml(encoding='utf-8')).toprettyxml(indent="    ")
            nfo_filename = str(os.path.splitext(path)[0]).upper() + '.nfo'
            with open(nfo_filename, 'w') as fid:
                fid.write(nfo_str)




        if s['download-subs']:
            try:
                found_subs = download_subtitles(_movie,path)
                if found_subs:
                    print("             Found subtitles!")
                    add_tag("Sub", new_fname)
            except Exception as e:
                print(e)
        

        # move the file into a folder (if we say to)
        if s['move-video-to-new-folder']:
            path = create_and_move_video_into_folder(new_fname, s, vid_id, _movie)
        # get the cover (if we say to)


if __name__ == '__main__':
    print("--- sort_jav.py: Beginning sort, please wait ---")
    settings = read_file('settings_sort_jav.ini')

    if(len(path_list)==0):
        for f in os.listdir(staging_path):     
            fullpath = os.path.join(staging_path, f)
            file_name, file_extension = os.path.splitext(fullpath)
            if(file_extension == ".mp4" or file_extension == ".mkv"):
                vid_id = find_id(strip_bad_data(strip_file_name(fullpath)))
                if(vid_id != None):
                    vid_id = correct_vid_id(vid_id)
                    studio_code = vid_id.split("-")[0]
                    # now we sort and put in the correct directory

                    for studio,series in sort_map.items():
                        if(studio_code in series):
                            a_new_path = jav_root + studio
                            print("Moving " + fullpath + " to " + a_new_path)
                            try:
                                dest = shutil.move(fullpath, a_new_path) 
                                print("Moved " + dest)
                            except Exception as E:
                                print(E)


                            if(a_new_path not in path_list):
                                path_list.append(a_new_path)
                                print(path_list)


                 
    for a_path in path_list:
        try:
            sort_jav(a_path, settings)
        except Exception as E:
            print("        (ERROR) Something went wrong processing : " + a_path)
            print(E)
            continue

    executionTime = (time.time() - startTime)
    print("   ")
    print("--- Sorting completed in "+ str(executionTime) +" seconds. ---")
    print("   ")

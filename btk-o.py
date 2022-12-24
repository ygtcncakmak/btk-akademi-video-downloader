import os
import re
import sys
import time
import m3u8
import math
import requests
import argparse
import tinytag as tnt
from command_runner import command_runner

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", required=True, help="Download file path.")
args, unknown = parser.parse_known_args()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def download(course, duration, url, path):
    try:
        video_id = url.split("/")[-1]
        json_file = requests.get(f"https://cinema8.com/api/v1/uscene/rawvideo/flavor/{video_id}").json()
        f_name = json_file["name"]
        f_hlsUrl = json_file["hlsUrl"]
        f_path = path + f_name
        f_max_res_url = max(m3u8.load(f_hlsUrl).playlists, key=lambda lm:lm.stream_info.bandwidth).absolute_uri

        if not already_downloaded(f_path, duration):
            if not os.path.exists(path): os.makedirs(path)
            print("{} ...".format(f_name))

            params = resource_path("ffmpeg.exe") + ' -y -headers \"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) ' + \
                'Gecko/20100101 Firefox/108.0 Host: www.btkakademi.gov.tr Accept: */* Accept-Language: en-US,en;q=0.8,tr-TR;q=0.5,tr;q=0.3 ' + \
                'Accept-Encoding: gzip, deflate, br DNT: 1 Connection: keep-alive Referer: ' + course + \
                ' Cookie: locale=tr; Sec-Fetch-Dest: script Sec-Fetch-Mode: no-cors Sec-Fetch-Site: same-origin\" -i ' + f_max_res_url + \
                ' -bsf:a aac_adtstoasc -vcodec copy -c copy ' + '\"' + f_path + '\"'
            
            err_code, stdout, stderr = command_runner(params, timeout=90, encoding='utf-8', method='monitor', \
                                                        live_output=False, stdout=False, stderr=False, split_streams=True)

            if       err_code ==    0 and already_downloaded(f_path, duration): return
            else:
                if   err_code ==    0: print("Corrupted, downloading again... [error: {}]".format(err_code))
                elif err_code ==    1: print("FFmpeg occured error... [error: {}]"        .format(err_code))
                elif err_code == -254: print("Process timeout... [error: {}]"             .format(err_code))
                elif err_code == -252: print("Keyboard interrupt... [error: {}]"          .format(err_code))
                else:                  print("Invalid error... [error: {}]"               .format(err_code))
                time.sleep(1)
                download(course, duration, url, path)
                return
                
        else:print("{} +".format(f_name))

    except:
        print("Reconnecting in 3 sec...")
        time.sleep(3)
        download(course, duration, url, path)
        return

def m_download(course, urls, paths):
    urls_count = sum(len(u) for u in urls)
    for i in range(len(urls)):
        for j in range(len(urls[i])):
            downloaded = sum(len(u) for u in urls[:i])
            print(downloaded+j+1, "/", urls_count, paths[i].split("\\")[-1], end = ': ')
            duration = urls[i][j].split('|')[0]
            url = urls[i][j].split('|')[1]
            download(course, duration, url, paths[i])
    print("Bitti!")

def get_url(urls):
    formatted = []
    for l in urls:
        url = "https://cinema8.com/api/v1/uscene/rawvideo/flavor/"
        duration = l.split("|")[0].strip()
        code = l.split("/")[-1].split("?")[0]
        if l.split("/")[3] == "raw-video":
            formatted.append(get_duration(duration).__str__() + "|" + url + code)
    return formatted

def already_downloaded(f_path, duration):
    return  os.path.exists(f_path) and \
            tnt.TinyTag.get(f_path).duration != None and \
            abs(int(duration) - math.trunc(tnt.TinyTag.get(f_path).duration)) <= 3

def get_duration(t):
    durations = t.split(' ')[::-1]
    total = 0
    for i in range(0, len(durations)):
        total += int(re.findall(r'\d+', durations[i].strip())[0]) * pow(60, i)
    return total

def correct_string(string):
    corrected = ""
    for c in string:
        if c not in "\/:*?<>|": corrected += c
        else: corrected += "-"
    return corrected;

def get_url_and_path(main_folder_path, txt):
    file_id = 1
    with open(txt, 'r', encoding="utf-8") as f:
        urls = []
        paths = []
        prgs = f.read().split("\n\n")
        course = prgs[0]
        for prg in prgs[1:]:
            line = prg.split("\n")
            paths.append(main_folder_path + file_id.__str__() + ". " + correct_string(line[0]) + "\\")
            urls.append(get_url(line[1:]))
            file_id += 1
    return course, urls, paths

def start(main_path):
    course, urls, paths = get_url_and_path(main_path, main_path + "\\url.txt")
    print("\n__________________ Indirme Islemi Basladi __________________\n")
    m_download(course, urls, paths)
    print("\n_____________________ Kontrol Ediliyor _____________________\n")
    m_download(course, urls, paths)

if args.output != None:
    if args.output[-1] != "\\":
        args.output += "\\"
    os.system('mode 60,40')
    os.system('color 8E')
    print("\n  || BTK Video Downloader ||  \n  ")
    start(args.output)

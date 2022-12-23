import requests
import subprocess
import os
import time
import m3u8
import re
import tinytag as tnt
import math
import threading
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", required=True, help="Download file path.")
args, unknown = parser.parse_known_args()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

p_ctrl=[0]

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
            params = 'ffmpeg -y -headers \"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) ' + \
                'Gecko/20100101 Firefox/108.0 Host: www.btkakademi.gov.tr Accept: */* Accept-Language: en-US,en;q=0.8,tr-TR;q=0.5,tr;q=0.3 ' + \
                'Accept-Encoding: gzip, deflate, br DNT: 1 Connection: keep-alive Referer: ' + course + \
                ' Cookie: locale=tr; Sec-Fetch-Dest: script Sec-Fetch-Mode: no-cors Sec-Fetch-Site: same-origin\" -i ' + f_max_res_url + \
                ' -bsf:a aac_adtstoasc -vcodec copy -c copy ' + '\"' + f_path + '\"'
            
            process = subprocess.Popen(params, encoding='UTF-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            d_thread = threading.Thread(target=start_process, args=(process,))
            d_thread.start()

            p_ctrl[0],temp,t_out = 0,-1,0
            while True:
                #print(p_ctrl[0])
                if p_ctrl[0] == -1: 
                    process.kill()
                    download(course, duration, url, path)
                    return
                if p_ctrl[0] == temp: 
                    t_out += 1
                    if t_out >= 20:
                        print("Timeout gerceklesti...")
                        process.kill()
                        download(course, duration, url, path)
                        return
                else: t_out = 0
                if p_ctrl[0] == -2:
                    if already_downloaded(f_path, duration):
                        return
                    else:
                        download(course, duration, url, path)
                        return
                temp = p_ctrl[0]
                time.sleep(1)
                
        else:print("{} +".format(f_name))

    except:
        print("Tekrar baglaniliyor...")
        time.sleep(3)
        download(course, duration, url, path)
        return

def start_process(process):
    while not process.poll(): # process not terminated
        if process.stdout: # process running and prompting
            std_out = process.stdout.readline()
            if std_out: # process running and prompting
                p_ctrl[0] += 1
                if 'error' in std_out: # process running but prompted error
                    p_ctrl[0] = -1
                    return
            else: # process finished with or without error
                p_ctrl[0] = -2
                return
        time.sleep(0.1)

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

def connection():
    try: return requests.get('http://google.com', timeout=5)
    except: return False

def already_downloaded(f_path, duration):
    return  os.path.exists(f_path) and \
            tnt.TinyTag.get(f_path).duration != None and \
            int(duration) == math.trunc(tnt.TinyTag.get(f_path).duration)

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

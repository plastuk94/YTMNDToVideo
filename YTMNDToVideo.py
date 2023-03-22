import urllib.request
import os
import json


def download_url(url, filename, mode="text"):
    with urllib.request.urlopen(url) as f:
        if mode == "text":
            html = f.read().decode('utf-8')
            file_mode = "w"
        else:
            html = f.read()
            file_mode = "wb"
    with open(filename, file_mode) as out:
        out.write(html)


def get_info_json(html_filename):
    with open(html_filename, "r") as html_file:
        lines = html_file.readlines()
        for line in lines:
            if "ytmnd.site_data_url" in line:
                return "/info/" + line.split("/")[2] + "/json"


def main():
    html_filename = "page.html"
    json_filename = "info.json"
    url = input("Enter a YTMND URL: ")
    download_url(url, html_filename)
    info_json_string = get_info_json(html_filename)
    download_url(url + info_json_string, json_filename)

    with open("info.json", "r") as json_file:
        info_json = json.load(json_file)

    image_url = info_json["site"]["foreground"]["url"]
    sound_url = info_json["site"]["sound"]["url"]
    image_ext = image_url.split(".")[-1]
    sound_ext = sound_url.split(".")[-1]
    image_url_file = "image." + image_ext
    sound_url_file = "sound." + sound_ext

    download_url(image_url, image_url_file, "binary")
    download_url(sound_url, sound_url_file, "binary")

    os.system(
        "ffmpeg -i " + image_url_file + " -movflags faststart -pix_fmt yuv420p -vf \"scale = trunc(iw / 2) * 2:trunc("
                                        "ih / 2) * 2\" -y video.mp4")
    os.system(
        "ffmpeg -stream_loop -1 -i video.mp4 -i " + sound_url_file + " -c copy -map 0:v:0 -map 1:a:0 -shortest -y "
                                                                     "\"output.mp4\"")

    for file in [image_url_file, sound_url_file, html_filename, json_filename, "video.mp4"]:
        os.remove(file)


main()

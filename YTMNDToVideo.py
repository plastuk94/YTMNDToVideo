import json
import mmap
import os
import subprocess
import sys
import urllib.request


def duration_check(filename):
    duration = subprocess.check_output(f"ffprobe -i {filename} -show_entries format=duration -v quiet -of csv=\"p=0\"")
    return float(duration)


def loop_check(gif_filename):
    with open(gif_filename, 'rb') as gif:
        with mmap.mmap(gif.fileno(), 0, access=mmap.ACCESS_READ) as mf:
            # Locate GIF application extension to see how many times to loop
            offset = mf.find(b'NETSCAPE2.0')
            mf.seek(offset + 13)
            loop_bytes = mf.read(2)
            return int.from_bytes(loop_bytes, byteorder=sys.byteorder)
    return 0


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

    loop = loop_check(image_url_file)

    # Run non-animated images as long as the audio.
    if image_ext != "gif":
        audio_duration = duration_check(sound_url_file)
        os.system(
            f"ffmpeg -i {image_url_file} -movflags faststart -pix_fmt yuv420p -vf \"tpad=stop_mode=clone:stop_duration="
            f"{audio_duration}, scale = trunc(iw / 2) * 2:trunc(ih / 2) * 2\" -y video.mp4")
        os.system(
            f"ffmpeg -i video.mp4 -i {sound_url_file} -c:a aac -b:a 128k -y "
            "\"output.mp4\"")

    # Run non-looping GIFs as long as the audio, but have to explicitly give duration.
    elif loop == 0:
        audio_duration = duration_check(sound_url_file)
        os.system(
            f"ffmpeg -i {image_url_file} -movflags faststart -pix_fmt yuv420p -vf \"tpad=stop_mode=clone:stop_duration="
            f"{audio_duration}, scale = trunc(iw / 2) * 2:trunc(ih / 2) * 2\" -y video.mp4")
        os.system(
            f"ffmpeg -i video.mp4 -i {sound_url_file} -c:a aac -b:a 128k -shortest -y "
            "\"output.mp4\"")
    # Run only as long as it needs to loop for the audio.
    else:
        os.system(
            f"ffmpeg -i {image_url_file} -movflags faststart -pix_fmt yuv420p -vf \"scale = trunc(iw / 2) * 2:trunc("
            "ih / 2) * 2\" -y video.mp4")
        os.system(
            f"ffmpeg -stream_loop {str(loop)} -i video.mp4 -i {sound_url_file} -c:a aac -b:a 128k -shortest -y "
            "\"output.mp4\"")

    for file in [image_url_file, sound_url_file, html_filename, json_filename, "video.mp4"]:
        os.remove(file)


main()

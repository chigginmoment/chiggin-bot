# This file will download Instagram embeds.

import os
import shutil
import typing
import instaloader
import re
import discord
import ffmpeg
import requests
from instaloader import Post

L = instaloader.Instaloader()

# L.load_session_from_file("reelwatcher31")

target_filename = "compressed_"


def download(post_short):
    """
    Downloads an Instagram post for a given link.
    """
    try:
        # post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", link).group(1).strip()
        print("Getting post (updated).")

        L = instaloader.Instaloader()

        post = Post.from_shortcode(L.context, post_short)
        url = post.video_url
        response = requests.get(url, stream=True)
        filename = f"{post_short}.mp4"
        print("Downloading file.")
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

            return filename
        else:
            print("Error in response code:", response.status_code)
    except Exception as e:
        print(e)
        return None

def compress(post_short, filename):
    print("Compressing.")
    original_filename = filename
    output_filename = f"{target_filename}{filename}"
    compress_video(original_filename, output_filename, 8 * 1000)
    return output_filename

def download_and_compress(post_short):
    """
    Downloads an Instagram post for a given link. Compresses the Instagram post if
    it exceeds the designated size.
    """

    # post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", message).group(1).strip()
    print("Getting post.")
    post = instaloader.Post.from_shortcode(L.context, post_short)

    L.download_post(post, target=post_short)

    for file in os.listdir(f"{post_short}"):
            if file.endswith(".mp4"):
                original_filename = f"{post_short}/{file}"
                reel_size = os.path.getsize(original_filename)
                if reel_size > 8388608:
                    print("Compressing.")
                    output_filename = f"{post_short}/{target_filename}{file}"
                    compress_video(original_filename, output_filename, 8 * 1000)
                    return output_filename
                else:
                    print("Compression not necessary.")
                    return original_filename


# Credit to https://gist.github.com/ESWZY/a420a308d3118f21274a0bc3a6feb1ff 
def compress_video(video_full_path, output_file_name, target_size):
    # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000

    probe = ffmpeg.probe(video_full_path)
    # Video duration, in s.
    duration = float(probe['format']['duration'])
    # Audio bitrate, in bps.
    audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
    # Target total bitrate, in bps.
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    # Target audio bitrate, in bps
    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate
    # Target video bitrate, in bps.
    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, os.devnull,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                  ).overwrite_output().run()
    ffmpeg.output(i, output_file_name,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                  ).overwrite_output().run()

# Compress input.mp4 to 50MB and save as output.mp4
# compress_video('input.mp4', 'output.mp4', 8 * 1000)
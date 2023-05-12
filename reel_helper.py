# This file will download Instagram embeds.

import os
import shutil
import typing
import instaloader
import re
import discord
import ffmpeg

L = instaloader.Instaloader()

# L.load_session_from_file("reelwatcher31")

target_file_name = "chiggin_"


def download(link):
    """
    Downloads an Instagram post for a given link.
    """
    try:
        print("Attempting reel download.")
        post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", link).group(1).strip()

        print("Post short: ", post_short)

        post = instaloader.Post.from_shortcode(L.context, post_short)
        print("Got post")

        L.download_post(post, target=post_short)
        print("Downloaded post")

        return post_short
    except Exception as e:
        print(e)

def download_and_compress(message, target_size):
    """
    Downloads an Instagram post for a given link. Compresses the Instagram post if
    it exceeds the designated size.
    """

    post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", message).group(1).strip()

    post = instaloader.Post.from_shortcode(L.context, post_short)

    L.download_post(post, target=post_short)

    for file in os.listdir(f"{post_short}"):
            if file.endswith(".mp4"):
                reel_size = os.path.getsize(f"{post_short}/{file}")
                if reel_size > target_size:
                    print("Compressing.")
                else:
                    print("Compression not necessary.")
                    return f"{post_short}/{file}"
                # try:
                #     reel_size = os.path.getsize(f"{post_short}/{file}")
                #     print("Reel size:", reel_size)
                #     if  reel_size > target_size:
                #         pass
                #     else:
                #         return post_short
                # except Exception as e:
                #     # await message.reply("Reel embed failed: "+ e)
                #     print("Uploading reel failed: "+ e)
                # break
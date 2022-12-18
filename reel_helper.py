# This file will download Instagram embeds.

import os
import shutil
import typing
import instaloader
import re
import discord

L = instaloader.Instaloader()

L.load_session_from_file("project9658")


def download(link):
    """
    Downloads an Instagram post for a given link.
    """
    print("Begin download.")
    post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", link).group(1).strip()

    print("Post short: ", post_short)

    post = instaloader.Post.from_shortcode(L.context, post_short)

    L.download_post(post, target=post_short)

    return post_short

def post_reel(message):
    """Posts the reel found in <message>."""
    print("Detected post")
    post_id = download(message.content).strip()
    print("Downloaded Instagram post: ", post_id)
    for file in os.listdir(f"{post_id}"):
        if file.endswith(".mp4"):
            print(f"{post_id}/{file}")
            try:
                # await message.reply(file=discord.File(f"{post_id}/{file}"), mention_author=False)
                print("Uploaded reel")
                return(f"{post_id}/{file}")
            except Exception as e:
                # await message.reply("Reel embed failed: "+ e)
                print("Uploading reel failed: "+ e)
                return -1
            break
    
    try:
        shutil.rmtree(post_id)
        print("Successfully removed Instagram post")
    except OSError as e:
        print("Error: ", e)
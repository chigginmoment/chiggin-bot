# This file will download Instagram embeds.

import os
import typing
import instaloader
import re

L = instaloader.Instaloader()

L.load_session_from_file("project9658")

def download(link):
    """
    Downloads an Instagram post for a given link.
    """
    post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/", link).group(1).strip()

    post = instaloader.Post.from_shortcode(L.context, post_short)

    L.download_post(post, target=post_short)

    return post_short

        
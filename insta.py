# This file will download Instagram Reels videos.


from instascrape import Reel
import time
 
# session id
SESSIONID = "3312752481%3AkoU7sojpWCHwro%3A11"
 
# Header with session id
headers = {
    "cookie": f'sessionid={SESSIONID};'
}
 
# Passing Instagram reel link as argument in Reel Module
insta_reel = Reel(
    'https://www.instagram.com/reel/CKWDdesgv2l/?utm_source=ig_web_copy_link')
 
# Using  scrape function and passing the headers
insta_reel.scrape(headers=headers)
 
# Giving path where we want to download reel to the
# download function
insta_reel.download(fp=f".\\Desktop\\reel{int(time.time())}.mp4")
 
# printing success Message
print('Downloaded Successfully.')
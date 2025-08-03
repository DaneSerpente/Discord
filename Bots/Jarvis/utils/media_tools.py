
import urllib.request
import re
from urllib.parse import quote

def youtube_trailer(title, year=None):
    search_url = html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + quote(title + ' ' + str(year) + ' ' + 'official trailer'))
    video_ids = re.findall(r"watch\?v=(\S{11})", search_url.read().decode())
    youtube_url = 'https://www.youtube.com/watch?v=' + video_ids[0]
    return youtube_url
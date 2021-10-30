from __future__ import unicode_literals
import argparse
import sys

import youtube_dl


if __name__ == "__main__":
    print("downloading", sys.argv[1])
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([sys.argv[1]])

import re
import glob

import pandas as pd

noise_words = [
    "Facebook Forum", "live\nDuniani Leo Video Tube", "Duniani Leo", "Forum",
    "Please enable JavaScript to view the", "comments powered by Disqus.", "Embed",
    "share", "The code has been copied to your clipboard.",
    "The URL has been copied to your clipboard", "Shirikiana kwenye Facebook",
    "Shirikiana kwenye Twitter", "No media source currently available",
    "0:00", "0:03:06", "Kiungo cha moja kwa moja", "16 kbps | MP3",
    "32 kbps | MP3", "48 kbps | MP3", "Pleya", "by VOA Swahili - Idhaa ya Kiswahili ya Sauti ya Amerika",
    "VOA Express"
]

df = pd.read_csv("../sentences/01-01-23.csv", header=None)
print(df[0])

# text = text.lower()
# pattern = re.compile('|'.join([re.escape(word) for word in noise_words]), re.IGNORECASE)
# text = pattern.sub('', text)
# # remove (\n)
# text = text.replace('\n', ' ').replace('\r', ' ')
# # double spaces
# text = re.sub(r'\s+', ' ', text)
# text.strip()

# def clean_csv_files(files):
#     for file in files:
#         df = pd.read_csv(file)
#         text = df.columns[0]
#
#         text = text.lower()
#         pattern = re.compile('|'.join([re.escape(word) for word in noise_words]), re.IGNORECASE)
#         text = pattern.sub('', text)
#         # remove (\n)
#         text = text.replace('\n', ' ').replace('\r', ' ')
#         # double spaces
#         text = re.sub(r'\s+', ' ', text)
#         text.strip()
#         print(text)
#
# clean_csv_files(csv_files)

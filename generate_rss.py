import os
import requests
import xml.etree.ElementTree as ET
from pydub import AudioSegment
from datetime import datetime
from email.utils import format_datetime

AUDIO_INPUT = "input"
AUDIO_OUTPUT = "output"
RSS_FILE = "rss.xml"
SITE_URL = "https://zhxianlucky.github.io/notebooklm-podcast"

def fetch_arxiv_metadata(arxiv_id):
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    r = requests.get(url)
    if r.status_code != 200:
        return arxiv_id, "arXiv metadata fetch failed.", ""
    root = ET.fromstring(r.text)
    entry = root.find('{http://www.w3.org/2005/Atom}entry')
    if entry is None:
        return arxiv_id, "arXiv metadata missing.", ""
    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
    summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip().replace('\n', ' ')
    return title, summary, arxiv_id

def convert_and_generate_items():
    items = []
    for fname in sorted(os.listdir(AUDIO_INPUT)):
        if not fname.endswith(".wav"):
            continue
        arxiv_id = os.path.splitext(fname)[0]
        title, summary, guid = fetch_arxiv_metadata(arxiv_id)
        mp3_name = title.replace(" ", "_") + ".mp3"

        wav_path = os.path.join(AUDIO_INPUT, fname)
        mp3_path = os.path.join(AUDIO_OUTPUT, mp3_name)

        sound = AudioSegment.from_wav(wav_path)
        sound.export(mp3_path, format="mp3", bitrate="128k")

        file_size = os.path.getsize(mp3_path)
        duration = f"{int(sound.duration_seconds) // 60}:{int(sound.duration_seconds) % 60:02d}"
        pub_date = format_datetime(datetime.utcnow())

        item = f"""
        <item>
          <title>{title}</title>
          <enclosure url="{SITE_URL}/output/{mp3_name}" length="{file_size}" type="audio/mpeg"/>
          <guid>{guid}</guid>
          <pubDate>{pub_date}</pubDate>
          <description>{summary}</description>
          <itunes:duration>{duration}</itunes:duration>
        </item>
        """
        items.append(item)
    return items

def generate_rss():
    os.makedirs(AUDIO_OUTPUT, exist_ok=True)
    items = convert_and_generate_items()
    rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>NotebookLM语音播客</title>
    <link>{SITE_URL}</link>
    <description>NotebookLM自动生成音频播客</description>
    <language>zh-cn</language>
    <itunes:author>zhxianlucky</itunes:author>
    <itunes:explicit>no</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    {''.join(items)}
  </channel>
</rss>"""
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(rss.strip())

if __name__ == "__main__":
    generate_rss()

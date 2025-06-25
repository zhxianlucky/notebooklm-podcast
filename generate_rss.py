import os
import requests
import subprocess
import xml.etree.ElementTree as ET
# from pydub import AudioSegment
from datetime import datetime
from email.utils import format_datetime
from mutagen.mp3 import MP3
from slugify import slugify  # 可选：确保文件名合法

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

        safe_title = slugify(title)  # 确保生成安全文件名
        mp3_name = f"{safe_title}.mp3"

        wav_path = os.path.join(AUDIO_INPUT, fname)
        mp3_path = os.path.join(AUDIO_OUTPUT, mp3_name)

        print(f"🎧 正在转换: {fname} → {mp3_name}")
        result = subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-codec:a", "libmp3lame", "-b:a", "128k", mp3_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print(f"❌ ffmpeg 转码失败: {result.stderr}")
            continue

        # 获取文件大小和时长
        try:
            file_size = os.path.getsize(mp3_path)
            mp3_info = MP3(mp3_path)
            duration_sec = int(mp3_info.info.length)
            duration = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        except Exception as e:
            print(f"❌ 无法获取 MP3 信息: {e}")
            continue

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
        print(f"✅ 已生成 RSS 条目：{title}")
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

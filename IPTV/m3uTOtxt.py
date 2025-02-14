
import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

# GitHub路徑
base_url = "https://github.com/WaykeYu/verify-iptv/tree/main"
raw_base_url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/"

# 獲取頁面內容
response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# 找到所有的.m3u檔案
m3u_files = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if href.endswith('.m3u'):
        m3u_files.append(href.split('/')[-1])

# 下載並解析每個.m3u檔案
all_channels = []
for m3u_file in m3u_files:
    # 下載.m3u檔案
    m3u_url = urljoin(raw_base_url, m3u_file)
    response = requests.get(m3u_url)
    m3u_content = response.text

    # 解析.m3u檔案
    channels = m3u_content.splitlines()
    for i in range(0, len(channels), 2):
        if i+1 < len(channels):
            channel_name = channels[i].strip('#EXTINF:-1,').strip()
            channel_url = channels[i+1].strip()
            all_channels.append(f"{channel_name}, {channel_url}")

# 將所有頻道合併並轉換為.txt格式
output_content = "\n".join(all_channels)

# 將內容寫入.txt檔案
output_filename = "merged_channels.txt"
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(output_content)

print(f"所有頻道已合併並存儲為 {output_filename}")

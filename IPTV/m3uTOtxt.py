import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

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

# 下載並轉換每個.m3u檔案
for m3u_file in m3u_files:
    # 下載.m3u檔案
    m3u_url = urljoin(raw_base_url, m3u_file)
    m3u_content = requests.get(m3u_url).text

    # 轉換為.txt格式
    txt_content = m3u_content  # 這裡可以根據需要進行格式轉換

    # 保存為.txt檔案
    txt_file = m3u_file.replace('.m3u', '.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(txt_content)

    print(f"已轉換並保存: {txt_file}")

print("所有檔案轉換完成！")

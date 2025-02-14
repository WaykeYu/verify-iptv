import re
import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# GitHub路徑
base_url = "https://github.com/WaykeYu/verify-iptv/tree/main"
raw_base_url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/"

# 清理檔案名稱中的非法字符
def clean_filename(filename):
    # 移除非法字符
    cleaned = re.sub(r'[\\/*?:"<>|]', '', filename)
    # 限制檔案名稱長度
    return cleaned[:50]  # 限制為 50 個字符

# 獲取頁面內容
response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# 找到所有的.m3u檔案
m3u_files = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if href.endswith('.m3u'):
        m3u_files.append(href.split('/')[-1])

# 創建本地目錄來存儲檔案
local_dir = "downloaded_files"
os.makedirs(local_dir, exist_ok=True)

# 下載、解析並轉換每個.m3u檔案
for m3u_file in m3u_files:
    # 下載.m3u檔案
    m3u_url = urljoin(raw_base_url, m3u_file)
    response = requests.get(m3u_url)
    m3u_content = response.text

    # 解析.m3u檔案並轉換為.txt格式
    channels = m3u_content.splitlines()
    txt_content = []
    for i in range(0, len(channels), 2):
        if i + 1 < len(channels):
            channel_name = channels[i].strip('#EXTINF:-1,').strip()
            channel_url = channels[i + 1].strip()
            txt_content.append(f"{channel_name}, {channel_url}")

    # 將內容寫入.txt檔案（改名為.txt）
    txt_filename = os.path.splitext(m3u_file)[0] + ".txt"
    txt_path = os.path.join(local_dir, txt_filename)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(txt_content))

    print(f"已轉換並存儲: {txt_path}")

    # 對當前.txt檔案進行頻道分類
    categories = {}
    for channel in txt_content:
        # 假設頻道名稱的第一部分是分類（例如 "電影:頻道1"）
        category = channel.split(':')[0].strip()
        if category not in categories:
            categories[category] = []
        categories[category].append(channel)

    # 將分類後的頻道存儲到各自的檔案中
    for category, channels in categories.items():
        # 清理分類名稱以確保檔案名稱合法
        cleaned_category = clean_filename(category)
        category_filename = f"{cleaned_category}.txt"
        category_path = os.path.join(local_dir, category_filename)
        with open(category_path, 'a', encoding='utf-8') as f:  # 使用 'a' 模式追加內容
            f.write(f"=== {category} ===\n")
            f.write("\n".join(channels) + "\n\n")

        print(f"已分類並存儲: {category_path}")

import os
import requests
from bs4 import BeautifulSoup
import re

# GitHub 目錄網址
GITHUB_URL = "https://github.com/WaykeYu/verify-iptv/tree/main"
RAW_URL_PREFIX = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/"

# 設定下載根目錄
BASE_SAVE_DIR = "downloaded_m3u"

# 建立儲存資料夾（如果不存在）
os.makedirs(BASE_SAVE_DIR, exist_ok=True)

def get_m3u_links():
    """取得 GitHub 上所有 .m3u 檔案的下載連結"""
    response = requests.get(GITHUB_URL)
    if response.status_code != 200:
        print("無法存取 GitHub 頁面")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", class_="js-navigation-open Link--primary")

    m3u_files = []
    for link in links:
        file_path = link.text  # 取得檔案名稱或路徑
        if file_path.endswith(".m3u"):
            m3u_files.append(file_path)
    
    return m3u_files

def download_file(file_path):
    """下載指定的 .m3u 檔案，並保留 GitHub 上的目錄結構"""
    raw_url = RAW_URL_PREFIX + file_path
    local_path = os.path.join(BASE_SAVE_DIR, file_path)

    # 確保目錄存在
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    response = requests.get(raw_url)
    if response.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"下載成功: {file_path}")
        return local_path
    else:
        print(f"下載失敗: {file_path}")
        return None

def parse_m3u(m3u_path):
    """解析 .m3u 檔案，分類後存回與下載檔案相同的目錄"""
    txt_path = m3u_path.replace(".m3u", ".txt")  # 轉換副檔名為 .txt

    with open(m3u_path, "r", encoding="utf-8") as m3u_file:
        lines = m3u_file.readlines()

    channels_by_category = {}  # 字典儲存不同分類的頻道
    current_category = "未分類"  # 預設分類
    channel_name = None  # 暫存頻道名稱

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 使用正則表達式提取 group-title 和頻道名稱
            match = re.search(r'group-title="([^"]*)".*,(.*)', line)
            if match:
                current_category = match.group(1).strip() or "未分類"
                channel_name = match.group(2).strip()
            else:
                channel_name = line.split(",")[-1].strip()  # 若無 group-title，僅取頻道名稱
        elif line and not line.startswith("#"):
            # 這一行應該是播放連結
            if channel_name:
                # 加入分類字典
                if current_category not in channels_by_category:
                    channels_by_category[current_category] = []
                channels_by_category[current_category].append(f"{channel_name} - {line}")
                channel_name = None  # 重置頻道名稱

    # 將所有分類存回下載的目錄
    with open(txt_path, "w", encoding="utf-8") as txt_file:
        for category, channel_list in sorted(channels_by_category.items()):
            txt_file.write(f"# {category}\n")
            txt_file.write("\n".join(channel_list) + "\n\n")

    print(f"分類儲存: {txt_path}")

def main():
    m3u_files = get_m3u_links()

    if not m3u_files:
        print("沒有找到 .m3u 檔案")
        return

    for file_path in m3u_files:
        m3u_path = download_file(file_path)
        if m3u_path:
            parse_m3u(m3u_path)

if __name__ == "__main__":
    main()

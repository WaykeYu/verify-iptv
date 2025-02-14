import os
import requests
from bs4 import BeautifulSoup

# GitHub 目錄網址
GITHUB_URL = "https://github.com/WaykeYu/verify-iptv/tree/main"
RAW_URL_PREFIX = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/"

# 設定儲存資料夾
SAVE_DIR = "downloaded_m3u"

# 建立儲存資料夾（如果不存在）
os.makedirs(SAVE_DIR, exist_ok=True)

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
        file_name = link.text
        if file_name.endswith(".m3u"):
            m3u_files.append(file_name)
    
    return m3u_files

def download_file(file_name):
    """下載指定的 .m3u 檔案"""
    raw_url = RAW_URL_PREFIX + file_name
    response = requests.get(raw_url)

    if response.status_code == 200:
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"下載成功: {file_name}")
        return file_path
    else:
        print(f"下載失敗: {file_name}")
        return None

def parse_m3u(m3u_path):
    """解析 .m3u 檔案並轉換為 '頻道名稱 - 播放連結' 格式"""
    txt_path = m3u_path.replace(".m3u", ".txt")

    with open(m3u_path, "r", encoding="utf-8") as m3u_file:
        lines = m3u_file.readlines()

    channel_list = []
    channel_name = None  # 用來暫存當前頻道名稱

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 解析頻道名稱
            parts = line.split(",")  # EXTINF 的最後一部分是頻道名稱
            if len(parts) > 1:
                channel_name = parts[-1]  # 取最後的頻道名稱
        elif line and not line.startswith("#"):
            # 這一行應該是播放連結
            if channel_name:
                channel_list.append(f"{channel_name} - {line}")
                channel_name = None  # 重置頻道名稱，等待下一組資料

    # 寫入轉換後的 .txt 檔案
    with open(txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write("\n".join(channel_list))

    print(f"轉換成功: {txt_path}")
    return txt_path

def main():
    m3u_files = get_m3u_links()

    if not m3u_files:
        print("沒有找到 .m3u 檔案")
        return

    for file_name in m3u_files:
        m3u_path = download_file(file_name)
        if m3u_path:
            parse_m3u(m3u_path)

if __name__ == "__main__":
    main()

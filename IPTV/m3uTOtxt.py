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

def convert_m3u_to_txt(m3u_path):
    """轉換 .m3u 檔案為 .txt 格式，並存回同目錄"""
    txt_path = m3u_path.replace(".m3u", ".txt")

    with open(m3u_path, "r", encoding="utf-8") as m3u_file:
        lines = m3u_file.readlines()

    # 過濾出有效的播放連結（排除註解行）
    with open(txt_path, "w", encoding="utf-8") as txt_file:
        for line in lines:
            if not line.startswith("#") and line.strip():
                txt_file.write(line)

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
            convert_m3u_to_txt(m3u_path)

if __name__ == "__main__":
    main()

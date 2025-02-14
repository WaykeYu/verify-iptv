import os
import requests
import re
from bs4 import BeautifulSoup

def get_all_m3u_files(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        m3u_files = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.m3u') and 'blob' in href:
                m3u_files.append("https://raw.githubusercontent.com" + href.replace('/blob', ''))
        return m3u_files
    except requests.exceptions.RequestException as e:
        print(f"獲取 .m3u 文件列表失敗: {e}")
        return []

def download_file(url, local_path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"文件已下載到: {local_path}")
    except requests.exceptions.RequestException as e:
        print(f"下載文件失敗: {e}")

def parse_m3u(file_path):
    channels = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            channel = {}
            for line in file:
                line = line.strip()
                if line.startswith("#EXTINF:"):
                    info = re.search(r'#EXTINF:-?\\d+,\\s*(.*)', line)
                    if info:
                        channel['name'] = info.group(1)
                elif line.startswith("http"):
                    channel['url'] = line
                    if 'name' in channel and 'url' in channel:
                        channels.append(channel)
                        channel = {}
    except Exception as e:
        print(f"解析文件失敗: {e}")
    return channels

def classify_channels(channels):
    categories = {}
    for channel in channels:
        category = channel['name'].split()[0] if channel['name'] else '未分類'
        categories.setdefault(category, []).append(channel)
    return categories

def save_channels_by_category(categories):
    for category, channels in categories.items():
        filename = f"{category}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                for channel in channels:
                    file.write(f"{channel['name']} - {channel['url']}\\n")
            print(f"{filename} 已儲存，共 {len(channels)} 頻道")
        except Exception as e:
            print(f"保存 {filename} 失敗: {e}")

def main():
    base_url = "https://github.com/WaykeYu/verify-iptv"
    m3u_files = get_all_m3u_files(base_url)

    for url in m3u_files:
        local_path = os.path.basename(url)
        download_file(url, local_path)
        channels = parse_m3u(local_path)
        print(f"{local_path}: 共解析到 {len(channels)} 個頻道")
        categories = classify_channels(channels)
        save_channels_by_category(categories)

if __name__ == "__main__":
    main()

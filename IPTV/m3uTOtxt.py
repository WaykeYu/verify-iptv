import os
import requests
import re

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
    base_url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/"
    file_list = ["Adult.m3u", "Sports.m3u", "Movies.m3u", "News.m3u"]  # 可使用網頁解析獲取所有檔案

    for m3u_file in file_list:
        url = base_url + m3u_file
        local_path = m3u_file

        download_file(url, local_path)
        channels = parse_m3u(local_path)
        print(f"{m3u_file}: 共解析到 {len(channels)} 個頻道")

        categories = classify_channels(channels)
        save_channels_by_category(categories)

if __name__ == "__main__":
    main()

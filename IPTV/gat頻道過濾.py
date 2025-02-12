import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from tqdm import tqdm  # 導入 tqdm

# 下載 M3U 檔案
def download_m3u_file(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"檔案已成功下載並保存到 {save_path}")
    else:
        print(f"無法下載檔案，HTTP 狀態碼: {response.status_code}")
        exit()

# 去除重複頻道並排序
def remove_duplicates_and_sort(input_file, output_file):
    channels = {}
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:"):  # 頻道資訊行
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if channel_url not in channels:
                channels[channel_url] = channel_info
            i += 2
        else:
            i += 1

    sorted_channels = sorted(channels.items(), key=lambda x: x[1])  # 根據頻道名稱排序

    with open(output_file, 'w', encoding='utf-8') as file:
        for url, info in sorted_channels:
            file.write(info + "\n")
            file.write(url + "\n")

    print(f"已去除重複頻道並排序，結果保存到 {output_file}")

# 檢查頻道有效性
def check_channel_validity(channel_info, channel_url):
    try:
        response = requests.get(channel_url, timeout=5)
        if response.status_code == 200:
            return channel_info, channel_url, True
        else:
            return channel_info, channel_url, False
    except requests.exceptions.RequestException as e:
        return channel_info, channel_url, False

# 過濾無效頻道
def filter_invalid_channels(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    valid_lines = []
    futures = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # 使用多線程檢查
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                break
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip()
            futures.append(executor.submit(check_channel_validity, channel_info, channel_url))

        for future in tqdm(as_completed(futures), total=len(futures), desc="檢查頻道有效性"):
            channel_info, channel_url, is_valid = future.result()
            if is_valid:
                valid_lines.append(channel_info + "\n")
                valid_lines.append(channel_url + "\n")
                print(f"有效頻道: {channel_info}")
            else:
                print(f"無效頻道: {channel_info}")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(valid_lines)

    print("無效頻道已移除，檔案已更新。")

# 主程式
if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/WaykeYu/IPTV1/refs/heads/main/GAT.m3u"
    save_path = "./GAT.m3u"

    # 下載檔案
    download_m3u_file(url, save_path)

    # 去除重複頻道並排序
    remove_duplicates_and_sort(save_path, save_path)

    # 檢查頻道有效性並過濾無效頻道
    filter_invalid_channels(save_path, save_path)
